"""Controle de um processo CAD por vez; a janela pode navegar durante a geracao."""
import importlib.util
import json
from pathlib import Path
import sys
from uuid import uuid4
from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal


class CadJob(QObject):
    progress = Signal(int, str)
    completed = Signal(dict, str)
    failed = Signal(str)

    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.root = Path(root)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.process_error)
        self.buffer = b""
        self.stderr = ""
        self.result = None
        self.error = None
        self.request_path = None
        self.timer = QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.read_output)
        self.offset = 0

    @property
    def running(self):
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, request, settings):
        if self.running:
            raise ValueError("Aguarde o trabalho em andamento")
        backend = settings.backend
        generating = request["operation"] == "generate"
        external = settings.build_python.strip() if backend == "build123d" and generating else ""
        if external:
            if not Path(external).is_file() or Path(external).suffix.lower() != ".exe":
                raise ValueError("Selecione o python.exe do ambiente build123d")
            command = [external, "-m", "bambu_ai.desktop.worker"]
        elif getattr(sys, "frozen", False):
            if generating and importlib.util.find_spec(backend) is None:
                raise ValueError("Este executável não inclui o motor escolhido; use o motor empacotado ou um Python build123d externo")
            command = [sys.executable, "--cad-worker"]
        else:
            if generating and importlib.util.find_spec(backend) is None:
                raise ValueError(f"Motor {backend} ausente neste ambiente. Instale-o separadamente e configure o Python alternativo.")
            command = [sys.executable, "-m", "bambu_ai.desktop.worker"]
        jobs = self.root / "jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        self.request_path = jobs / f"{uuid4().hex}.json"
        self.request_path.write_text(json.dumps(request, ensure_ascii=True), encoding="utf-8")
        self.buffer, self.stderr, self.result, self.error = b"", "", None, None
        self.offset = 0
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONUTF8", "1")
        environment.insert("PYTHONIOENCODING", "utf-8")
        if not getattr(sys, "frozen", False):
            environment.insert("PYTHONPATH", str(Path(__file__).resolve().parents[2]))
        self.process.setProcessEnvironment(environment)
        self.process.setProgram(command[0])
        self.process.setArguments(command[1:] + [str(self.request_path)])
        self.process.start()
        self.timer.start()

    def read_output(self):
        # Eventos em arquivo tambem funcionam no executavel sem console (stdout=None).
        self.process.readAllStandardOutput()
        if not self.request_path:
            return
        events = self.request_path.with_suffix(".events")
        if events.exists():
            with events.open("rb") as stream:
                stream.seek(self.offset)
                data = stream.read()
                self.offset = stream.tell()
            self.buffer += data
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                event = json.loads(line)
                if "progress" in event:
                    self.progress.emit(min(99, event["progress"]), event["message"])
                if "result" in event:
                    self.result = (event["result"], event["folder"])
                if "error" in event:
                    self.error = event["error"]
            except (ValueError, KeyError, TypeError):
                continue  # Bibliotecas podem escrever mensagens fora do protocolo.

    def read_error(self):
        self.stderr = (self.stderr + bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))[-3000:]

    def cleanup(self):
        self.timer.stop()
        if self.request_path:
            self.request_path.with_suffix(".events").unlink(missing_ok=True)
            self.request_path.unlink(missing_ok=True)
            self.request_path = None

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.cleanup()
            self.failed.emit("Não foi possível iniciar o processo CAD. Confira o ambiente Python configurado.")

    def finished(self, code, status):
        self.read_output()
        self.read_error()
        self.cleanup()
        if code == 0 and self.result:
            self.completed.emit(*self.result)
        else:
            self.failed.emit(self.error or self.stderr or "O processo CAD terminou sem resultado")
