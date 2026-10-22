"""Protocolo JSON por stdout; CAD isolado em subprocesso e nunca no Qt da janela."""
import json
from pathlib import Path
import sys
from ..pipeline import generate
from ..spec import ModelSpec
from ..validation import validate
from .storage import Library
from .thumbnail import thumbnail

event_path = None


def emit(**event):
    line = json.dumps(event, ensure_ascii=True) + "\n"
    if event_path:
        with event_path.open("a", encoding="utf-8") as stream:
            stream.write(line)
    else:
        print(line, end="", flush=True)


def main(argv=None):
    global event_path
    argv = argv if argv is not None else sys.argv[1:]
    event_path = Path(argv[0]).with_suffix(".events")
    try:
        request = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
        folder = Path(request["folder"])
        if request["operation"] == "generate":
            spec = ModelSpec(**request["spec"])
            report = generate(spec, folder, backend=request["backend"],
                              progress=lambda percent, message: emit(progress=int(percent*0.9), message=message))
            emit(progress=95, message="Criando miniatura e registrando biblioteca")
            thumbnail(folder / "model.stl", folder / "thumbnail.png")
            Library(request["root"]).add(folder, request["name"], spec.to_dict(), report)
        elif request["operation"] == "validate":
            emit(progress=20, message="Analisando malha e paredes amostradas")
            report = validate(folder / "model.stl")
        else:
            raise ValueError("Operação de trabalho desconhecida")
        emit(result=report, folder=str(folder))
        return 0
    except Exception as exc:
        emit(error=f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
