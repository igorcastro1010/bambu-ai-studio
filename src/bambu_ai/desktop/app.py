"""Aplicativo Qt nativo; imports CAD permanecem no processo de trabalho."""
import html
import importlib.util
import json
import os
from pathlib import Path
import sys
from datetime import datetime
from PySide6.QtCore import (QLibraryInfo, QLocale, QObject, QRunnable, QSize, Qt,
                            QThreadPool, QTimer, QTranslator, QUrl, Signal, Slot)
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFormLayout,
    QGridLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QProgressBar, QPushButton, QSplitter, QStackedWidget, QTextBrowser,
    QVBoxLayout, QWidget)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineUrlRequestInterceptor
from .jobs import CadJob
from .providers import CredentialStore, Intent, JsonAPIProvider, LocalProvider, validate_endpoint
from .storage import Library, Settings, export_file
from ..integrations import open_studio


THEME = """
QWidget {background:#111a22; color:#e0e8ee; font-family:'Segoe UI'; font-size:14px;}
QMainWindow {background:#111a22;} QLabel#brand {font-size:24px;font-weight:700;color:#63d9b2;}
QLabel#title {font-size:24px;font-weight:600;} QLabel#muted {color:#a3b2bf;}
QListWidget,QTextBrowser,QLineEdit,QComboBox {background:#18232d;border:1px solid #2c3c49;border-radius:8px;padding:10px;}
QListWidget::item {padding:12px;border-radius:6px;} QListWidget::item:selected {background:#245747;color:#d9fff1;}
QPushButton {background:#243442;border:1px solid #354b5c;border-radius:7px;padding:10px 15px;}
QPushButton:hover {background:#314c5b;} QPushButton:disabled {color:#6b7a87;background:#1a242d;}
QPushButton#primary {background:#53c5a0;color:#091d16;font-weight:700;border:0;}
QPushButton#primary:hover {background:#75dbb8;}
QProgressBar {border:1px solid #314250;border-radius:5px;text-align:center;background:#18232d;}
QProgressBar::chunk {background:#3f9a82;} QSplitter::handle {background:#253440;}
"""


class LocalOnly(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if info.requestUrl().scheme() not in {"file", "data", "blob", "qrc", "about"}:
            info.block(True)


class PreviewPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        return url.scheme() in {"file", "about", "data"}


class Signals(QObject):
    done = Signal(object)
    error = Signal(str)


class InterpretTask(QRunnable):
    def __init__(self, provider, text, previous):
        super().__init__()
        self.provider, self.text, self.previous = provider, text, previous
        self.signals = Signals()

    def run(self):
        try:
            self.signals.done.emit(self.provider.interpret(self.text, self.previous))
        except Exception as exc:
            self.signals.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, root=None):
        super().__init__()
        self.library = Library(root)
        self.settings_error = None
        try:
            self.settings = Settings.load(self.library.root)
        except (ValueError, TypeError, OSError) as exc:
            self.settings = Settings()
            self.settings_error = f"Configuração inválida; usando padrões nesta sessão: {exc}"
        if not self.settings.build_python and importlib.util.find_spec(self.settings.backend) is None:
            other = "build123d" if self.settings.backend == "cadquery" else "cadquery"
            if importlib.util.find_spec(other):
                self.settings.backend = other
        self.draft = None
        self.current_folder = None
        self.interpreting = False
        self.preview_confirmed = False
        self.setWindowTitle("Bambu AI Studio 0.3")
        self.resize(1380, 880)
        self.setMinimumSize(1080, 720)
        self.setStyleSheet(THEME)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.job = CadJob(self.library.root, self)
        self.job.progress.connect(self.on_progress)
        self.job.completed.connect(self.on_complete)
        self.job.failed.connect(self.on_error)
        outer = QWidget()
        self.setCentralWidget(outer)
        row = QHBoxLayout(outer)
        row.setContentsMargins(18, 18, 18, 18)
        sidebar = QWidget()
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        brand = QLabel("BAMBU\nAI STUDIO")
        brand.setObjectName("brand")
        side.addWidget(brand)
        side.addWidget(QLabel("DESKTOP  /  0.3"))
        self.navigation = QListWidget()
        self.navigation.addItems(["Criar com IA", "Meus Modelos", "Impressão", "Configurações"])
        side.addWidget(self.navigation)
        profile = QLabel("A1 mini + AMS Lite\n180 × 180 × 180 mm\nPLA • operação manual")
        profile.setObjectName("muted")
        side.addWidget(profile)
        row.addWidget(sidebar)
        self.pages = QStackedWidget()
        row.addWidget(self.pages, 1)
        self.create_page()
        self.library_page()
        self.print_page()
        self.settings_page()
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.restore_history()
        self.reload_library()
        self.update_actions()
        if self.settings_error:
            self.append_chat("assistente", self.settings_error)

    def heading(self, layout, title, subtitle):
        label = QLabel(title)
        label.setObjectName("title")
        layout.addWidget(label)
        description = QLabel(subtitle)
        description.setWordWrap(True)
        description.setObjectName("muted")
        layout.addWidget(description)

    def button(self, text, callback, primary=False):
        button = QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        return button

    def create_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.heading(layout, "Da ideia à peça", "Chaveiros, placas e suportes de celular. Modo local por regras; API de IA opcional nas configurações.")
        splitter = QSplitter(Qt.Orientation.Horizontal)
        chat = QWidget()
        left = QVBoxLayout(chat)
        left.setContentsMargins(0, 12, 12, 0)
        self.history = QTextBrowser()
        self.history.setAccessibleName("Histórico da conversa")
        left.addWidget(self.history, 1)
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText('Ex.: chaveiro com nome "ANA", largura 60 mm')
        self.prompt.setAccessibleName("Pedido de modelagem")
        self.prompt.setMaxLength(2000)
        self.prompt.returnPressed.connect(self.send)
        left.addWidget(self.prompt)
        controls = QHBoxLayout()
        self.send_button = self.button("Enviar", self.send)
        self.generate_button = self.button("Gerar", self.generate, True)
        controls.addWidget(self.send_button)
        controls.addWidget(self.generate_button)
        controls.addWidget(self.button("Novo pedido", self.new_request))
        left.addLayout(controls)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        left.addWidget(self.progress)
        self.status = QLabel("Pronto para criar • sem impressão automática")
        self.status.setWordWrap(True)
        left.addWidget(self.status)
        splitter.addWidget(chat)
        preview = QWidget()
        right = QVBoxLayout(preview)
        self.viewer = QWebEngineView()
        self.viewer.setAccessibleName("Visualizador 3D do modelo")
        self.viewer.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.page = PreviewPage(self.viewer)
        self.viewer.setPage(self.page)
        self.interceptor = LocalOnly(self.page)
        self.page.profile().setUrlRequestInterceptor(self.interceptor)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        self.viewer.loadFinished.connect(self.preview_loaded)
        self.viewer.setHtml('<html><body style="background:#111a22;color:#91a9b7;font:18px Segoe UI;display:grid;place-items:center;height:90vh"><div>Seu modelo aparecerá aqui<br><small>Gere uma peça ou selecione Meus Modelos</small></div></body></html>')
        right.addWidget(self.viewer, 1)
        self.result_label = QLabel("Nenhum modelo selecionado")
        self.result_label.setWordWrap(True)
        right.addWidget(self.result_label)
        actions = QGridLayout()
        self.action_buttons = []
        for label, callback in (("Validar", self.validate_current), ("Abrir no Bambu Studio", self.open_studio),
                                 ("Abrir Pasta", self.open_folder), ("Exportar STL", lambda: self.export("stl")),
                                 ("Exportar STEP", lambda: self.export("step"))):
            button = self.button(label, callback)
            self.action_buttons.append(button)
            index = len(self.action_buttons)-1
            actions.addWidget(button, index // 3, index % 3)
        right.addLayout(actions)
        splitter.addWidget(preview)
        splitter.setSizes([390, 780])
        layout.addWidget(splitter, 1)
        self.pages.addWidget(page)

    def library_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.heading(layout, "Meus Modelos", "Biblioteca local com miniaturas, datas, dimensões e arquivos STL/STEP. Selecione para inspecionar.")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar pelo nome do modelo")
        self.search.textChanged.connect(self.reload_library)
        layout.addWidget(self.search)
        self.model_list = QListWidget()
        self.model_list.setIconSize(QSize(96, 96))
        self.model_list.itemClicked.connect(self.select_model)
        layout.addWidget(self.model_list, 1)
        layout.addWidget(self.button("Atualizar biblioteca", self.reload_library))
        layout.addWidget(self.button("Renomear modelo selecionado", self.rename_model))
        self.pages.addWidget(page)

    def print_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.heading(layout, "Impressão", "Preparação manual para a Bambu Lab A1 mini")
        info = QLabel("Perfil: A1 mini • PLA • 180 × 180 × 180 mm\n\n"
                      "1. Gere ou selecione um modelo em Meus Modelos.\n"
                      "2. Valide a malha e revise os alertas de paredes.\n"
                      "3. Abra no Bambu Studio, selecione o perfil e confira as camadas.\n"
                      "4. Reserve espaço para brim e purga e atribua as cores do AMS Lite.\n\n"
                      "Validação geométrica não garante impressão ou resistência.\n"
                      "O aplicativo não fatia, não envia arquivos à impressora e não inicia impressões.\n"
                      "3MF de projeto: salvar manualmente no Bambu Studio.")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addWidget(self.button("Abrir modelo selecionado no Bambu Studio", self.open_studio))
        layout.addStretch()
        self.pages.addWidget(page)

    def settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.heading(layout, "Configurações", "Arquivos e histórico ficam no perfil do Windows. Credenciais são guardadas apenas no cofre do sistema.")
        form = QFormLayout()
        self.backend = QComboBox()
        self.backend.addItem("CadQuery", "cadquery")
        self.backend.addItem("build123d (ambiente separado)", "build123d")
        self.backend.setCurrentIndex(self.backend.findData(self.settings.backend))
        form.addRow("Motor CAD", self.backend)
        self.build_python = QLineEdit(self.settings.build_python)
        self.build_python.setPlaceholderText("Caminho para .venv-build123d/Scripts/python.exe, se externo")
        form.addRow("Python build123d", self.build_python)
        self.studio_path = QLineEdit(self.settings.studio_path)
        self.studio_path.setPlaceholderText("Opcional: caminho do bambu-studio.exe")
        form.addRow("Bambu Studio", self.studio_path)
        self.provider = QComboBox()
        self.provider.addItem("Local por regras (gratuito, sem IA generativa)", "local")
        self.provider.addItem("API de IA compatível com JSON (opcional)", "api")
        self.provider.setCurrentIndex(self.provider.findData(self.settings.provider))
        form.addRow("Interpretação", self.provider)
        self.endpoint = QLineEdit(self.settings.endpoint)
        self.endpoint.setPlaceholderText("https://seu-provedor/v1 ou http://localhost:11434/v1")
        form.addRow("URL base da API", self.endpoint)
        self.model = QLineEdit(self.settings.model)
        form.addRow("Modelo da API", self.model)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Deixe vazio para manter a credencial existente")
        form.addRow("Chave API", self.api_key)
        form.addRow("Impressora / material", QLabel("A1 mini • 180 × 180 × 180 mm • PLA (perfil fixo nesta versão)"))
        path = QLabel(str(self.library.root))
        path.setWordWrap(True)
        path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Biblioteca e configurações", path)
        layout.addLayout(form)
        layout.addWidget(QLabel("A API recebe apenas seu pedido e os parâmetros anteriores. Nenhum STL é enviado.\n"
                               "O custo e a disponibilidade dependem do serviço escolhido; o modo local não precisa de API."))
        controls = QHBoxLayout()
        controls.addWidget(self.button("Salvar configurações", self.save_settings, True))
        controls.addWidget(self.button("Remover credencial desta URL", self.remove_credential))
        layout.addLayout(controls)
        self.settings_status = QLabel("")
        self.settings_status.setWordWrap(True)
        layout.addWidget(self.settings_status)
        layout.addStretch()
        self.pages.addWidget(page)

    def restore_history(self):
        for item in self.library.history():
            self.append_chat(item["role"], item["body"], save=False)
        if not self.library.history():
            self.append_chat("assistente", 'Olá! No modo local interpreto regras para três modelos. Experimente: chaveiro com nome "ANA", largura 60 mm. Não gero formas livres nem código por IA.')

    def append_chat(self, role, body, save=True):
        label = "Você" if role == "usuario" else "Bambu AI"
        color = "#86debe" if role == "usuario" else "#a8bed0"
        self.history.append(f'<p style="color:{color}"><b>{label}</b><br>{html.escape(body).replace(chr(10), "<br>")}</p>')
        self.history.verticalScrollBar().setValue(self.history.verticalScrollBar().maximum())
        if save:
            self.library.chat(role, body)

    def busy(self):
        return self.interpreting or self.job.running

    def update_actions(self):
        busy = self.busy()
        self.send_button.setEnabled(not busy)
        self.generate_button.setEnabled(not busy and self.draft is not None and self.draft.ready)
        for button in self.action_buttons:
            button.setEnabled(not busy and self.current_folder is not None)

    def new_request(self):
        if self.busy():
            return
        self.draft = None
        self.prompt.clear()
        self.append_chat("assistente", "Novo pedido. Qual peça deseja criar?")
        self.update_actions()

    def send(self):
        if self.busy():
            return
        text = self.prompt.text().strip()
        if not text:
            return
        self.prompt.clear()
        self.append_chat("usuario", text)
        try:
            provider = LocalProvider() if self.settings.provider == "local" else JsonAPIProvider(self.settings.endpoint, self.settings.model)
            self.interpreting = True
            self.status.setText("Interpretando pedido…")
            self.task = InterpretTask(provider, text, self.draft)
            self.task.signals.done.connect(self.on_intent)
            self.task.signals.error.connect(self.on_error)
            self.pool.start(self.task)
        except Exception as exc:
            self.on_error(str(exc))
        self.update_actions()

    @Slot(object)
    def on_intent(self, intent):
        self.interpreting = False
        self.draft = intent
        self.append_chat("assistente", intent.message)
        self.status.setText("Parâmetros prontos" if intent.ready else "Aguardando esclarecimento")
        self.update_actions()

    def generate(self):
        if self.busy() or not self.draft or not self.draft.ready:
            return
        try:
            spec = self.draft.spec()
            folder = self.library.new_folder()
            name = self.draft.parameters.get("text", "Suporte de celular")
            request = {"operation": "generate", "spec": spec.to_dict(), "folder": str(folder),
                       "root": str(self.library.root), "name": name, "backend": self.settings.backend}
            self.job.start(request, self.settings)
            self.progress.setValue(0)
            self.status.setText("Iniciando motor CAD…")
        except Exception as exc:
            self.on_error(str(exc))
        self.update_actions()

    def validate_current(self):
        if not self.current_folder or self.busy():
            return
        try:
            self.job.start({"operation": "validate", "folder": str(self.current_folder)}, self.settings)
        except Exception as exc:
            self.on_error(str(exc))
        self.update_actions()

    @Slot(int, str)
    def on_progress(self, percent, message):
        self.progress.setValue(percent)
        self.status.setText(message)
        self.statusBar().showMessage(message)

    @Slot(dict, str)
    def on_complete(self, report, folder):
        self.progress.setValue(100)
        self.status.setText("Concluído" if report["valid"] else "Malha reprovada")
        self.show_model(Path(folder), report)
        self.append_chat("assistente", ("Verificações geométricas aprovadas. " if report["valid"] else "Modelo reprovado. ")
                         + "\n".join(report["errors"] + report["warnings"]))
        self.reload_library()
        self.update_actions()

    @Slot(str)
    def on_error(self, message):
        self.interpreting = False
        self.status.setText("Falha: " + message[:500])
        self.statusBar().showMessage("Falha: " + message[:500])
        self.append_chat("assistente", "Erro: " + message[:1500])
        self.update_actions()

    def show_model(self, folder, report):
        changed = self.current_folder != folder
        self.current_folder = folder
        if changed:
            self.preview_confirmed = False
            self.viewer.load(QUrl.fromLocalFile(str((folder / "preview.html").resolve())))
        dims = " × ".join(f"{v:g}" for v in report["dimensions_mm"])
        self.result_label.setText(f"{dims} mm • {report['triangles']} faces • "
                                  f"{'malha fechada' if report['watertight'] else 'malha aberta'} • STL / STEP")
        self.update_actions()

    def preview_loaded(self, ok):
        if not self.current_folder:
            return
        if not ok:
            self.status.setText("Não foi possível carregar o preview; os arquivos CAD foram preservados.")
            return
        # setHtml tem limite de tamanho; carregamos o arquivo offline completo.
        script = """(() => {document.querySelectorAll('.modebar').forEach(e => e.style.display='none');
        const p=document.querySelector('.js-plotly-plot');
        return Boolean(p && p._fullLayout && p._fullLayout.scene && p._fullLayout.scene._scene);})()"""
        self.page.runJavaScript(script, self.on_preview_check)

    def on_preview_check(self, ready):
        self.preview_confirmed = bool(ready)
        if ready:
            self.status.setText("Modelo carregado no visualizador 3D • arraste para girar e role para zoom")
            self.statusBar().showMessage("Modelo pronto • verifique os alertas antes de preparar a impressão")
        else:
            self.status.setText("HTML carregado; cena 3D ainda não confirmada. Confira o suporte WebGL da máquina.")

    def reload_library(self, *_):
        self.model_list.clear()
        for row in self.library.items(self.search.text()):
            report = json.loads(row["report"])
            dims = " × ".join(f"{v:g}" for v in report["dimensions_mm"])
            created = datetime.fromisoformat(row["created"]).astimezone().strftime("%d/%m/%Y %H:%M")
            folder = Path(row["folder"])
            files = " / ".join(ext.upper() for ext in ("stl", "step") if (folder / f"model.{ext}").is_file())
            item = QListWidgetItem(QIcon(str(folder / "thumbnail.png")), f"{row['name']}\n{created}  •  {dims} mm  •  {files}")
            item.setData(Qt.ItemDataRole.UserRole, row)
            self.model_list.addItem(item)

    def select_model(self, item):
        row = item.data(Qt.ItemDataRole.UserRole)
        self.show_model(Path(row["folder"]), json.loads(row["report"]))
        self.navigation.setCurrentRow(0)

    def rename_model(self):
        item = self.model_list.currentItem()
        if not item:
            return
        row = item.data(Qt.ItemDataRole.UserRole)
        name, accepted = QInputDialog.getText(self, "Renomear modelo", "Nome do modelo:", text=row["name"])
        if accepted and name.strip():
            try:
                self.library.rename(row["id"], name.strip())
                self.reload_library()
            except (ValueError, OSError) as exc:
                self.on_error(str(exc))

    def open_folder(self):
        if self.current_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.current_folder)))

    def open_studio(self):
        if not self.current_folder:
            self.status.setText("Selecione um modelo na biblioteca primeiro")
            return
        try:
            if self.settings.studio_path:
                os.environ["BAMBU_STUDIO_PATH"] = self.settings.studio_path
            open_studio(self.current_folder / "model.stl")
        except Exception as exc:
            self.on_error(str(exc))

    def export(self, extension):
        if not self.current_folder:
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar " + extension.upper(),
                         f"modelo.{extension}", f"Arquivo {extension.upper()} (*.{extension})")
        if destination:
            try:
                export_file(self.current_folder, Path(destination), extension)
                self.status.setText("Arquivo exportado para " + destination)
            except Exception as exc:
                self.on_error(str(exc))

    def save_settings(self):
        try:
            endpoint = self.endpoint.text().strip()
            if endpoint:
                endpoint = validate_endpoint(endpoint)
            if self.provider.currentData() == "api":
                JsonAPIProvider(endpoint, self.model.text().strip())
            if self.api_key.text():
                CredentialStore().save(endpoint, self.api_key.text())
            settings = Settings(backend=self.backend.currentData(), build_python=self.build_python.text().strip(),
                provider=self.provider.currentData(), endpoint=endpoint, model=self.model.text().strip(),
                studio_path=self.studio_path.text().strip())
            settings.save(self.library.root)
            self.settings = settings
            self.api_key.clear()
            self.settings_status.setText("Configurações salvas. Chave API, quando informada, permanece somente no cofre do Windows.")
        except Exception as exc:
            self.settings_status.setText("Não foi possível salvar: " + str(exc))

    def remove_credential(self):
        try:
            CredentialStore().remove(self.endpoint.text().strip())
            self.api_key.clear()
            self.settings_status.setText("Credencial removida do cofre para esta URL")
        except Exception as exc:
            self.settings_status.setText("Não foi possível remover: " + str(exc))

    def closeEvent(self, event):
        if self.busy():
            self.status.setText("Aguarde a conclusão do trabalho antes de fechar o aplicativo")
            event.ignore()
        else:
            event.accept()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cad-worker":
        from .worker import main as worker_main
        return worker_main(sys.argv[2:])
    QLocale.setDefault(QLocale("pt_BR"))
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("BambuAIStudio.Desktop")
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setApplicationName("Bambu AI Studio")
    app.setOrganizationName("BambuAIStudio")
    translator = QTranslator(app)
    translator.load("qtbase_pt_BR", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    app.installTranslator(translator)
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from .diagnostics import smoke
        return smoke(app, MainWindow, Path(sys.argv[2]))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
