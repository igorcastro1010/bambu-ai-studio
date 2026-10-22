# Uma distribuicao inclui apenas um binding OpenCascade.
from importlib.util import find_spec
from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent
backend = "build123d" if find_spec("build123d") else "cadquery"
if not find_spec(backend):
    raise RuntimeError("Instale exatamente um motor CAD no ambiente de empacotamento")
if find_spec("build123d") and find_spec("cadquery"):
    raise RuntimeError("Nao empacote dois bindings OCP no mesmo ambiente")
datas, binaries, hiddenimports = collect_all(backend)
if backend == "build123d":
    extra_data, extra_binaries, extra_imports = collect_all("lib3mf")
    datas += extra_data
    binaries += extra_binaries
    hiddenimports += extra_imports
hiddenimports += collect_submodules("OCP")
hiddenimports += ["bambu_ai.desktop.worker", "keyring.backends.Windows"]
excluded = "cadquery" if backend == "build123d" else "build123d"
a = Analysis([str(root / "packaging/desktop_entry.py")], pathex=[str(root / "src")],
             binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             excludes=[excluded, "PyQt5", "PyQt6", "PySide2", "pytest"],
             noarchive=False)
# Qt no Windows usa a ICU do sistema. Um PATH com Poppler pode fazer o
# analisador coletar uma ICU com simbolos renomeados e quebrar QtCore.
system_icu = {"icu.dll", "icuuc.dll", "icuin.dll"}
a.binaries = [entry for entry in a.binaries
              if Path(entry[0]).name.lower() not in system_icu
              and not (Path(entry[0]).parent == Path(".") and Path(entry[0]).name.lower().startswith("icudt"))]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="BambuAIStudio",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=bool(os.environ.get("BAMBU_PACKAGE_DEBUG")))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="BambuAIStudio")
