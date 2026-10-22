"""Contrato de interpretacao: apenas parametros, nunca codigo vindo de IA."""
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Protocol
import unicodedata
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError, URLError
from ..presets import from_preset


@dataclass
class Intent:
    preset: str | None = None
    parameters: dict = field(default_factory=dict)
    message: str = ""
    ready: bool = False

    def spec(self):
        if not self.ready:
            raise ValueError("Complete os dados do modelo antes de gerar")
        return from_preset(self.preset, **self.parameters)


class InterpretationProvider(Protocol):
    def interpret(self, message: str, previous: Intent | None = None) -> Intent: ...


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(c))


LABELS = {"largura": "width", "comprimento": "width", "profundidade": "depth",
          "espessura": "thickness", "altura": "height", "relevo": "relief",
          "tamanho do texto": "text_size", "diametro do furo": "hole_diameter"}


def finish(preset, parameters):
    if preset in {"chaveiro", "placa"} and not parameters.get("text"):
        return Intent(preset, parameters, "Qual nome ou texto deseja? Responda com o texto entre aspas.")
    spec = from_preset(preset, **parameters)
    dims = (spec.width, spec.depth, spec.height if preset == "suporte-celular" else spec.thickness+spec.relief)
    return Intent(preset, parameters, f"Pronto: {preset}, {dims[0]:g} × {dims[1]:g} × {dims[2]:g} mm. "
                  "Parâmetros não informados usam os padrões. Confira e clique em Gerar.", True)


class LocalProvider:
    def interpret(self, message, previous=None):
        original = message.strip()
        if not original or len(original) > 2000:
            raise ValueError("Escreva um pedido de até 2.000 caracteres")
        text = normalize(original)
        found = []
        for preset, pattern in (("chaveiro", r"\bchaveiros?\b"), ("placa", r"\bplacas?\b"),
                                 ("suporte-celular", r"\bsuporte(?: de| para)? (?:celular|telefone)\b")):
            if re.search(pattern, text):
                found.append(preset)
                text = re.sub(pattern, " ", text)
        if len(found) > 1:
            return Intent(message="Peça um modelo por vez: chaveiro, placa ou suporte de celular.")
        preset = found[0] if found else (previous.preset if previous else None)
        if not preset:
            return Intent(message="Modo local por regras: suporte somente a chaveiro, placa e suporte de celular. Exemplo: chaveiro com nome \"ANA\", largura 60 mm.")
        parameters = dict(previous.parameters) if previous and previous.preset == preset and not found else {}
        # Capturar texto antes de remover palavras do restante do comando.
        quoted = re.search(r'["“](.+?)["”]', original)
        named = re.search(r"\b(?:nome|texto|escrito)\s*(?:e\s+|:|=)?\s*(.+?)(?=\s+(?:de\s+\d|com\s+\d|e\s+(?:largura|altura|espessura)|largura|profundidade|espessura|relevo|altura|tamanho do texto|diametro do furo)\b|[,;]|$)", normalize(original))
        if quoted:
            parameters["text"] = quoted.group(1)
            text = re.sub(r'["“].+?["”]', " ", text)
        elif named:
            parameters["text"] = original[named.start(1):named.end(1)].strip()
            text = text.replace(named.group(1), " ", 1)
        elif previous and not previous.ready and preset in {"chaveiro", "placa"} and not found and not any(label in text for label in LABELS) and not re.match(r"(?:quero|crie|faca|gere)\b", text):
            parameters["text"] = original
            text = ""
        for label, field_name in LABELS.items():
            pattern = rf"\b{label}\s*(?:de|:|=)?\s*(-?\d+(?:[.,]\d+)?)\s*(mm|cm)?\b"
            matches = list(re.finditer(pattern, text))
            if len(matches) > 1:
                raise ValueError(f"Informe apenas um valor para {label}")
            if matches:
                value = float(matches[0].group(1).replace(",", "."))
                parameters[field_name] = value * (10 if matches[0].group(2) == "cm" else 1)
                text = re.sub(pattern, " ", text)
            elif re.search(rf"\b{label}\b", text):
                return Intent(preset, parameters, f"Qual valor de {label}, em mm? Responda: {label} 60 mm.")
        residual = re.sub(r"\b(?:crie|criar|gere|gerar|faca|quero|um|uma|o|a|de|do|da|com|para|e|por|favor|nome|texto|escrito|personalizado|personalizada|mude|mudar|altere|alterar)\b", " ", text)
        residual = re.sub(r"[\s,;:.!?]+", "", residual)
        if residual:
            return Intent(preset, parameters, "Não reconheci parte do pedido. Use apenas nome/texto e medidas identificadas, como largura 60 mm. Formas, logos e recursos novos não são suportados neste modo.")
        return finish(preset, parameters)


def validate_endpoint(endpoint):
    parsed = urlparse(endpoint)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("URL da API não pode conter credenciais, parâmetros ou fragmentos")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
        raise ValueError("Use HTTPS ou HTTP somente em localhost")
    if not parsed.hostname:
        raise ValueError("Informe uma URL válida para a API")
    return endpoint.rstrip("/")


class CredentialStore:
    """Selecionar explicitamente o cofre Windows; nunca usar backend plaintext."""
    @staticmethod
    def backend():
        import sys
        if sys.platform != "win32":
            raise ValueError("O cofre de API desta versão requer Windows")
        from keyring.backends.Windows import WinVaultKeyring
        return WinVaultKeyring()

    def identifier(self, endpoint):
        return hashlib.sha256(validate_endpoint(endpoint).encode()).hexdigest()

    def get(self, endpoint):
        return self.backend().get_password("BambuAIStudio", self.identifier(endpoint))

    def save(self, endpoint, secret):
        if not secret.strip():
            raise ValueError("A chave API está vazia")
        self.backend().set_password("BambuAIStudio", self.identifier(endpoint), secret.strip())

    def remove(self, endpoint):
        backend = self.backend()
        identifier = self.identifier(endpoint)
        if backend.get_password("BambuAIStudio", identifier) is not None:
            backend.delete_password("BambuAIStudio", identifier)


class JsonAPIProvider:
    """API opcional compativel com chat/completions. Requer servico real configurado."""
    def __init__(self, endpoint, model, credentials=None):
        self.endpoint = validate_endpoint(endpoint)
        if not model.strip():
            raise ValueError("Informe o identificador do modelo da API")
        self.model = model
        self.credentials = credentials or CredentialStore()

    def interpret(self, message, previous=None):
        if not message.strip() or len(message) > 2000:
            raise ValueError("Escreva um pedido de até 2.000 caracteres")
        system = ('Extraia somente parametros para chaveiro, placa ou suporte-celular. Nunca gere codigo. '
                  'Responda JSON: {"preset": "chaveiro", "parameters": {"text":"ANA", "width":60}}. '
                  'Campos numericos em mm: width, depth, thickness, height, relief, text_size, hole_diameter. '
                  'Nome/texto ausente: omita text. Pedido fora desses modelos ou recursos novos: '
                  '{"preset":null,"parameters":{}}. Nao invente texto do usuario. '
                  f'Contexto anterior: {json.dumps({"preset": previous.preset, "parameters": previous.parameters}, ensure_ascii=False) if previous else "nenhum"}')
        payload = {"model": self.model, "messages": [{"role": "system", "content": system},
                    {"role": "user", "content": message}], "response_format": {"type": "json_object"}}
        headers = {"Content-Type": "application/json"}
        secret = self.credentials.get(self.endpoint)
        if secret:
            headers["Authorization"] = "Bearer " + secret
        request = Request(self.endpoint + "/chat/completions", data=json.dumps(payload).encode(), headers=headers)
        try:
            with build_opener(NoRedirect()).open(request, timeout=30) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError("Resposta da API excedeu o limite de tamanho")
            data = json.loads(json.loads(raw)["choices"][0]["message"]["content"])
            if set(data) - {"preset", "parameters"}:
                raise ValueError("Resposta da API contém campos não suportados")
            if data.get("preset") is None:
                return Intent(message="O provedor não identificou um pedido suportado. Use chaveiro, placa ou suporte de celular.")
            if not isinstance(data.get("parameters"), dict):
                raise ValueError("Parâmetros da API devem ser um objeto JSON")
            return finish(data["preset"], data["parameters"])
        except HTTPError as exc:
            raise ValueError(f"API recusou a solicitação (HTTP {exc.code}). Confira URL, modelo e credencial.") from None
        except (URLError, TimeoutError):
            raise ValueError("Não foi possível conectar à API configurada") from None
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise ValueError("A API não retornou parâmetros JSON compatíveis") from None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, *args):
        raise ValueError("A API tentou redirecionar a conexão; configure a URL final para preservar a credencial")
