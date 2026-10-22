"""Dados locais fora do projeto, com SQLite e configuracao sem credenciais."""
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
from uuid import uuid4


def data_home():
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "BambuAIStudio"


@dataclass
class Settings:
    backend: str = "cadquery"
    build_python: str = ""
    provider: str = "local"
    endpoint: str = ""
    model: str = ""
    studio_path: str = ""
    printer: str = "Bambu Lab A1 mini"
    bed_mm: tuple = (180, 180, 180)
    material: str = "PLA"

    @classmethod
    def load(cls, root):
        path = Path(root) / "settings.json"
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Configurações devem ser um objeto JSON")
        allowed = {f.name for f in fields(cls)}
        settings = cls(**{k: v for k, v in raw.items() if k in allowed})
        if settings.backend not in {"cadquery", "build123d"} or settings.provider not in {"local", "api"}:
            raise ValueError("Configuração de motor ou provedor inválida")
        # O MVP oferece apenas este perfil; nao aceitar limites falsos no arquivo.
        settings.printer, settings.bed_mm, settings.material = cls.printer, (180, 180, 180), "PLA"
        return settings

    def save(self, root):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        path = root / "settings.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)


class Library:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_home()
        self.root.mkdir(parents=True, exist_ok=True)
        self.models = self.root / "models"
        self.models.mkdir(exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS models (id TEXT PRIMARY KEY, name TEXT, created TEXT, folder TEXT UNIQUE, spec TEXT, report TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, role TEXT, body TEXT, created TEXT)")

    def connect(self):
        db = sqlite3.connect(self.root / "library.sqlite", timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def new_folder(self):
        return self.models / uuid4().hex

    def add(self, folder, name, spec, report):
        folder = Path(folder).resolve()
        if not folder.is_relative_to(self.models.resolve()) or not (folder / "model.stl").is_file():
            raise ValueError("Modelo deve existir na biblioteca local")
        with self.connect() as db:
            db.execute("INSERT INTO models VALUES (?, ?, ?, ?, ?, ?)", (
                folder.name, name[:100], datetime.now(timezone.utc).isoformat(), str(folder),
                json.dumps(spec, ensure_ascii=False), json.dumps(report, ensure_ascii=False)))

    def items(self, search=""):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM models WHERE name LIKE ? ORDER BY created DESC", (f"%{search}%",))]

    def rename(self, identifier, name):
        if not name.strip() or len(name) > 100:
            raise ValueError("O nome deve ter de 1 a 100 caracteres")
        with self.connect() as db:
            db.execute("UPDATE models SET name=? WHERE id=?", (name.strip(), identifier))

    def chat(self, role, body):
        with self.connect() as db:
            db.execute("INSERT INTO history(role, body, created) VALUES (?, ?, ?)",
                       (role, body, datetime.now(timezone.utc).isoformat()))

    def history(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM (SELECT * FROM history ORDER BY id DESC LIMIT 100) ORDER BY id")]


def export_file(folder, target, extension):
    if extension not in {"stl", "step"}:
        raise ValueError("Exportação disponível somente em STL ou STEP")
    source = Path(folder) / f"model.{extension}"
    target = Path(target)
    if not source.is_file():
        raise ValueError(f"Arquivo {extension.upper()} não disponível neste modelo")
    if target.suffix.lower() != f".{extension}":
        raise ValueError(f"O destino deve terminar em .{extension}")
    # Criação exclusiva: preserva exportações anteriores, inclusive a fonte.
    with source.open("rb") as incoming, target.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
