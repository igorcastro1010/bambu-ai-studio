"""Contrato pequeno e independente dos motores CAD. Todas as medidas em mm."""
from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class ModelSpec:
    kind: str
    width: float = 70
    depth: float = 24
    thickness: float = 3
    text: str = "BAMBU"
    text_size: float = 10
    relief: float = 1
    hole_diameter: float = 5
    height: float = 55

    def __post_init__(self):
        if not isinstance(self.kind, str) or self.kind not in {"keychain", "sign", "phone_stand"}:
            raise ValueError("kind deve ser keychain, sign ou phone_stand")
        for field in fields(self):
            if field.name in {"kind", "text"}:
                continue
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field.name}: esperado numero em mm")
            if not math.isfinite(value) or not 0 < value <= 500:
                raise ValueError(f"{field.name}: use numero finito entre 0 e 500 mm")
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > 40:
            raise ValueError("text deve ter de 1 a 40 caracteres")
        if any(ord(c) < 32 for c in self.text):
            raise ValueError("text nao pode conter caracteres de controle")
        if self.kind in {"keychain", "sign"}:
            if self.width < 15 or self.depth < 10:
                raise ValueError("Placa deve ter pelo menos 15 x 10 mm")
            if self.kind == "keychain" and self.hole_diameter + 4 >= min(self.depth, self.width / 2):
                raise ValueError("Furo muito grande para a base; preserve ao menos 2 mm de parede")
        else:
            if self.depth < 40 or self.height < 25 or self.width < 30:
                raise ValueError("Suporte requer largura >=30, profundidade >=40 e altura >=25 mm")
            if self.thickness * 4 >= min(self.depth * 0.55, self.height):
                raise ValueError("Espessura muito grande para o suporte")

    @classmethod
    def load(cls, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Parametros devem ser um objeto JSON")
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Parametros desconhecidos: {', '.join(sorted(unknown))}")
        if "kind" not in data:
            raise ValueError("Parametro kind obrigatorio")
        return cls(**data)

    def to_dict(self):
        return asdict(self)

    def stand_profile(self):
        d, h, t = self.depth, self.height, self.thickness
        # Perfil YZ: base plana, labio frontal e encosto macico inclinado.
        return [(0, 0), (d, 0), (d, h), (d-t*2, h),
                (d*0.55, t*2), (t*4, t*2), (t*4, t*4),
                (t*2, t*4), (t*2, t*2), (0, t*2)]

    def text_layout(self):
        margin = self.hole_diameter + 6 if self.kind == "keychain" else 3
        return self.width - margin - 3, self.depth - 6, margin / 2 - 1.5
