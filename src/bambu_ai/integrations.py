"""Integracoes locais explicitas, sem comandos de fatiamento ou impressao."""
import os
from pathlib import Path
import shutil
import subprocess


def executable(name: str, variable: str, candidates=()):
    configured = os.environ.get(variable)
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)
        raise ValueError(f"{variable} nao aponta para um arquivo executavel")
    found = shutil.which(name)
    if found:
        return found
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise ValueError(f"{name} indisponivel. Instale e configure {variable} com o caminho do executavel")


def render_scad(source: Path, target: Path):
    if source.suffix.lower() != ".scad" or not source.is_file():
        raise ValueError("Informe um arquivo .scad local existente e confiavel")
    app = executable("openscad", "OPENSCAD_PATH", [r"C:\Program Files\OpenSCAD\openscad.com",
                                                   r"C:\Program Files\OpenSCAD\openscad.exe"])
    subprocess.run([app, "-o", str(target.resolve()), str(source.resolve())],
                   check=True, timeout=180, capture_output=True, text=True)


def open_studio(source: Path):
    if not source.is_file() or source.suffix.lower() not in {".stl", ".step", ".3mf"}:
        raise ValueError("Informe STL, STEP ou 3MF existente")
    app = executable("bambu-studio", "BAMBU_STUDIO_PATH",
                     [r"C:\Program Files\Bambu Studio\bambu-studio.exe"])
    subprocess.Popen([app, str(source.resolve())])
