"""Entrada PyInstaller: processo CAD sem inicializar a janela principal."""
import sys
import json
import os
from pathlib import Path
import traceback

def run():
    if len(sys.argv) > 1 and sys.argv[1] == "--cad-worker":
        from bambu_ai.desktop.worker import main
        return main(sys.argv[2:])
    from bambu_ai.desktop.app import main
    return main()

try:
    code = run()
except Exception:
    error = traceback.format_exc()
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "BambuAIStudio"
    root.mkdir(parents=True, exist_ok=True)
    (root / "startup-error.log").write_text(error, encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        diagnostic = Path(sys.argv[2])
        diagnostic.mkdir(parents=True, exist_ok=True)
        (diagnostic / "smoke-result.json").write_text(json.dumps({"success": False, "error": error}), encoding="utf-8")
    if sys.stderr:
        print(error, file=sys.stderr)
    code = 1
raise SystemExit(code)
