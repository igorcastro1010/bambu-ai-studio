import importlib.util
import json
from pathlib import Path
import time
import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from bambu_ai.desktop.app import MainWindow


@pytest.fixture(scope="module")
def qt():
    return QApplication.instance() or QApplication([])


def wait_until(qt, predicate, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt.processEvents()
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("Tempo limite aguardando tarefa Qt")


def test_chat_generation_and_library_remain_responsive(qt, tmp_path):
    window = MainWindow(tmp_path)
    backend = "cadquery" if importlib.util.find_spec("cadquery") else "build123d"
    if importlib.util.find_spec(backend) is None:
        pytest.skip("Ambiente sem motor CAD")
    window.settings.backend = backend
    try:
        window.prompt.setText("chaveiro largura 60 mm")
        window.send_button.click()
        wait_until(qt, lambda: not window.interpreting)
        assert not window.draft.ready and not window.generate_button.isEnabled()
        window.prompt.setText('"ANA"')
        window.send_button.click()
        wait_until(qt, lambda: not window.interpreting)
        assert window.draft.ready and window.generate_button.isEnabled()
        ticks = []
        timer = QTimer()
        timer.setInterval(25)
        timer.timeout.connect(lambda: ticks.append(True))
        timer.start()
        window.generate_button.click()
        assert window.job.running
        assert not window.generate_button.isEnabled()
        window.navigation.setCurrentRow(1)
        assert window.pages.currentIndex() == 1
        wait_until(qt, lambda: bool(window.library.items()) and not window.job.running)
        timer.stop()
        assert len(ticks) > 2  # Event loop atende eventos durante o CAD.
        row = window.library.items()[0]
        folder = Path(row["folder"])
        assert json.loads(row["report"])["valid"]
        assert (folder / "model.step").is_file() and (folder / "thumbnail.png").stat().st_size > 100
        window.reload_library()
        assert window.model_list.count() == 1
        window.select_model(window.model_list.item(0))
        wait_until(qt, lambda: window.preview_confirmed)
        view_state = []
        window.page.runJavaScript("""(() => {try {const p=document.querySelector('.js-plotly-plot');
            Plotly.restyle(p, {visible:[true,true,true], opacity:[0.5,1,1]});
            Plotly.relayout(p, {'scene.camera.eye':{x:4,y:-4,z:3}});
            return JSON.stringify({arestas:p.data[1].visible, normais:p.data[2].visible, camera:p.layout.scene.camera.eye.x});
            } catch(e) {return JSON.stringify({erro:String(e)});}})()""", view_state.append)
        wait_until(qt, lambda: bool(view_state))
        assert json.loads(view_state[0]) == {"arestas": True, "normais": True, "camera": 4}
        window.validate_current()
        wait_until(qt, lambda: not window.job.running)
        assert window.progress.value() == 100
        assert not list((tmp_path / "jobs").glob("*"))
    finally:
        if window.job.running:
            window.job.process.kill()
            window.job.process.waitForFinished(5000)
        window.close()
        window.deleteLater()
        qt.processEvents()


def test_corrupt_settings_are_reported_without_overwrite(qt, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[]", encoding="utf-8")
    window = MainWindow(tmp_path)
    try:
        assert window.settings_error and "Configuração inválida" in window.history.toPlainText()
        assert path.read_text(encoding="utf-8") == "[]"
    finally:
        window.close()
        window.deleteLater()
        qt.processEvents()


def test_failed_worker_returns_ui_to_ready(qt, tmp_path):
    window = MainWindow(tmp_path)
    try:
        window.current_folder = tmp_path / "missing"
        window.validate_current()
        wait_until(qt, lambda: not window.job.running)
        assert "Falha" in window.status.text()
        assert window.send_button.isEnabled()
    finally:
        window.close()
        window.deleteLater()
        qt.processEvents()
