import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from .spec import ModelSpec
from .pipeline import generate, generate_scad
from .validation import validate
from .viewer import preview
from .integrations import open_studio, executable


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bambu AI Studio: CAD local em mm")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("generate", help="Parametros JSON -> STL/STEP + relatorio + HTML")
    build.add_argument("parameters", type=Path)
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--backend", choices=["cadquery", "build123d"], default="cadquery")
    build.add_argument("--stl-only", action="store_true")
    build.add_argument("--no-preview", action="store_true")
    check = sub.add_parser("validate", help="Validar STL; retorna 1 se rejeitado")
    check.add_argument("source", type=Path)
    view = sub.add_parser("preview", help="Gerar visualizacao HTML offline")
    view.add_argument("source", type=Path)
    view.add_argument("--out", type=Path, required=True)
    scad = sub.add_parser("render-scad", help="OpenSCAD externo -> STL validado (sem STEP)")
    scad.add_argument("source", type=Path)
    scad.add_argument("--out", type=Path, required=True)
    studio = sub.add_parser("open-studio", help="Abrir arquivo no Bambu Studio, sem imprimir")
    studio.add_argument("source", type=Path)
    sub.add_parser("doctor", help="Listar versoes instaladas")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            result = generate(ModelSpec.load(args.parameters), args.out, args.backend,
                              step=not args.stl_only, html=not args.no_preview)
        elif args.command == "validate":
            result = validate(args.source)
        elif args.command == "preview":
            if args.out.suffix.lower() != ".html":
                raise ValueError("Preview deve terminar em .html")
            if args.out.exists():
                raise ValueError("Preview ja existe; escolha outro arquivo")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            result = {"preview": str(preview(args.source, args.out))}
        elif args.command == "render-scad":
            result = generate_scad(args.source, args.out)
        elif args.command == "open-studio":
            open_studio(args.source)
            result = {"opened": str(args.source), "printing": False}
        else:
            result = {"python": sys.version.split()[0]}
            for package in ("cadquery", "build123d", "trimesh", "numpy", "plotly"):
                try:
                    result[package] = importlib.metadata.version(package)
                except importlib.metadata.PackageNotFoundError:
                    result[package] = "nao instalado (opcional para CAD)"
            for app, variable, paths in (
                ("openscad", "OPENSCAD_PATH", [r"C:\Program Files\OpenSCAD\openscad.com", r"C:\Program Files\OpenSCAD\openscad.exe"]),
                ("bambu-studio", "BAMBU_STUDIO_PATH", [r"C:\Program Files\Bambu Studio\bambu-studio.exe"]),
            ):
                try:
                    result[app] = executable(app, variable, paths)
                except ValueError as exc:
                    result[app] = str(exc)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("valid", True) else 1
    except (ValueError, OSError, ImportError, subprocess.SubprocessError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
