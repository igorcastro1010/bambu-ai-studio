"""Teste real do desktop/empacotamento, em biblioteca isolada informada pelo usuario."""
import json
from pathlib import Path
import time
from PySide6.QtCore import QTimer
from .storage import export_file


def smoke(app, window_class, root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    window = window_class(root)
    window.show()
    started = time.monotonic()
    state = {"stage": "start", "exit": 1}

    def finish(success, error=""):
        timer.stop()
        result = {"success": success, "error": error, "backend": window.settings.backend,
                  "preview_confirmed": window.preview_confirmed,
                  "folder": str(window.current_folder) if window.current_folder else None}
        if success:
            for extension in ("stl", "step"):
                export_file(window.current_folder, root / f"diagnostico-{time.time_ns()}.{extension}", extension)
            result["screenshot_saved"] = window.grab().save(str(root / "desktop.png"))
        (root / "smoke-result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        state["exit"] = 0 if success else 1
        if window.job.running:
            window.job.process.kill()
            window.job.process.waitForFinished(5000)
        window.interpreting = False
        window.close()
        app.exit(state["exit"])

    def tick():
        try:
            if time.monotonic()-started > 120:
                finish(False, "Tempo limite: " + window.status.text())
            elif state["stage"] == "start":
                window.prompt.setText('chaveiro com nome "TESTE", largura 70 mm')
                window.send_button.click()
                state["stage"] = "interpret"
            elif state["stage"] == "interpret" and not window.interpreting:
                if not window.draft or not window.draft.ready:
                    finish(False, window.status.text())
                else:
                    window.generate_button.click()
                    state["stage"] = "generate"
            elif state["stage"] == "generate" and not window.job.running:
                if window.status.text().startswith("Falha"):
                    finish(False, window.status.text())
                elif window.preview_confirmed:
                    finish(True)
        except Exception as exc:
            finish(False, str(exc))

    timer = QTimer(window)
    timer.setInterval(100)
    timer.timeout.connect(tick)
    timer.start()
    app.exec()
    window.deleteLater()
    app.processEvents()
    return state["exit"]
