"""Validar antes de publicar arquivos finais; falhas preservam saidas anteriores."""
import json
from pathlib import Path
import tempfile
from . import cad
from .spec import ModelSpec
from .validation import validate
from .viewer import preview
from .integrations import render_scad


def generate(spec: ModelSpec, output: Path, backend="cadquery", step=True, html=True):
    output = output.resolve()
    if output.exists():
        raise ValueError("Pasta de saida ja existe; escolha outra para preservar os modelos")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp)
        shape = cad.create(spec, backend)
        cad.export(shape, stage / "model.stl", backend)
        report = validate(stage / "model.stl")
        if not report["valid"]:
            raise ValueError("Modelo rejeitado: " + "; ".join(report["errors"]))
        if step:
            cad.export(shape, stage / "model.step", backend)
        if html:
            preview(stage / "model.stl", stage / "preview.html")
        report["backend"] = backend
        (stage / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        (stage / "parameters.json").write_text(json.dumps(spec.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        # Uma pasta por geracao evita sobrescrever STL/STEP/relatorios antigos.
        if output.exists():
            raise ValueError("Pasta de saida ja existe; escolha outra para preservar os modelos")
        stage.rename(output)
    return report


def generate_scad(source: Path, output: Path):
    output = output.resolve()
    if output.exists():
        raise ValueError("Pasta de saida ja existe; escolha outra")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp)
        render_scad(source, stage / "model.stl")
        report = validate(stage / "model.stl")
        if not report["valid"]:
            raise ValueError("OpenSCAD gerou malha rejeitada: " + "; ".join(report["errors"]))
        preview(stage / "model.stl", stage / "preview.html")
        (stage / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        if output.exists():
            raise ValueError("Pasta de saida ja existe; escolha outra")
        stage.rename(output)
    return report
