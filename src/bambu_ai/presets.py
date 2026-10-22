"""Predefinicoes disponiveis mesmo fora da pasta do repositorio."""
from .spec import ModelSpec

PRESETS = {
    "chaveiro": {"kind": "keychain", "text": "BAMBU", "width": 70, "depth": 24},
    "placa": {"kind": "sign", "text": "BAMBU STUDIO", "width": 120, "depth": 35, "text_size": 12},
    "suporte-celular": {"kind": "phone_stand", "width": 60, "depth": 70, "height": 55},
}


def from_preset(name: str, **parameters):
    if name not in PRESETS:
        raise ValueError(f"Modelo desconhecido: {name}")
    allowed = {"width", "depth", "thickness"}
    allowed |= {"height"} if name == "suporte-celular" else {"text", "text_size", "relief"}
    if name == "chaveiro":
        allowed.add("hole_diameter")
    supplied = {key: value for key, value in parameters.items() if value is not None}
    unsupported = supplied.keys() - allowed
    if unsupported:
        raise ValueError(f"Parametros incompativeis com {name}: {', '.join(sorted(unsupported))}")
    return ModelSpec(**(PRESETS[name] | supplied))
