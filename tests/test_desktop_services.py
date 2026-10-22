import json
from pathlib import Path
import pytest
from bambu_ai.desktop.providers import (CredentialStore, Intent, JsonAPIProvider,
    LocalProvider, NoRedirect, validate_endpoint)
from bambu_ai.desktop.storage import Library, Settings, export_file


@pytest.mark.parametrize("text,preset,width", [
    ('chaveiro com nome "ANA", largura 60 mm', "chaveiro", 60),
    ('Crie uma placa com texto OFICINA largura 10 cm', "placa", 100),
    ('suporte de celular largura 65 mm', "suporte-celular", 65),
    ('chaveiro nome JOÃO largura 6,5 cm', "chaveiro", 65),
])
def test_portuguese_parameters(text, preset, width):
    result = LocalProvider().interpret(text)
    assert result.ready and result.preset == preset
    assert result.spec().width == width
    if preset == "chaveiro" and "JOÃO" in text:
        assert result.spec().text == "JOÃO"


def test_missing_name_and_followup():
    provider = LocalProvider()
    pending = provider.interpret("chaveiro largura 60 mm")
    assert not pending.ready and "Qual nome" in pending.message
    answer = provider.interpret('"MARIA"', pending)
    assert answer.ready and answer.spec().text == "MARIA" and answer.spec().width == 60
    adjusted = provider.interpret("altere largura 70 mm", answer)
    assert adjusted.spec().text == "MARIA" and adjusted.spec().width == 70


@pytest.mark.parametrize("text", ['dragão articulado', 'chaveiro redondo com nome "ANA"',
    'placa texto "OI" e logotipo', 'placa e chaveiro', 'chaveiro com nome "ANA" duas unidades'])
def test_unsupported_commands_never_generate(text):
    assert not LocalProvider().interpret(text).ready


def test_invalid_dimensions_do_not_pass_to_cad():
    with pytest.raises(ValueError):
        LocalProvider().interpret('chaveiro nome ANA largura -5 mm')


def test_settings_do_not_store_credentials(tmp_path):
    settings = Settings(endpoint="https://example.test/v1", model="modelo")
    settings.save(tmp_path)
    assert "api_key" not in json.loads((tmp_path / "settings.json").read_text())
    loaded = Settings.load(tmp_path)
    assert loaded.bed_mm == (180, 180, 180) and loaded.material == "PLA"


def test_library_and_exclusive_export(tmp_path):
    library = Library(tmp_path / "library")
    folder = library.new_folder()
    folder.mkdir()
    (folder / "model.stl").write_bytes(b"stl-data")
    library.add(folder, "ANA", {"kind": "keychain"}, {"dimensions_mm": [60, 24, 4]})
    assert library.items("ANA")[0]["name"] == "ANA"
    assert Library(library.root).items()[0]["folder"] == str(folder.resolve())
    library.rename(folder.name, "MARIA")
    assert library.items("MARIA")[0]["name"] == "MARIA"
    library.chat("usuario", "Olá")
    assert library.history()[0]["body"] == "Olá"
    target = tmp_path / "export.stl"
    export_file(folder, target, "stl")
    assert target.read_bytes() == b"stl-data"
    with pytest.raises(FileExistsError):
        export_file(folder, target, "stl")
    with pytest.raises(ValueError, match="não disponível"):
        export_file(folder, tmp_path / "missing.step", "step")


@pytest.mark.parametrize("endpoint", ["http://example.com/v1", "https://user:secret@example.com", "https://example.com/?key=abc", "file:///x"])
def test_unsafe_endpoint_rejected(endpoint):
    with pytest.raises(ValueError):
        validate_endpoint(endpoint)


def test_credential_uses_vault_only(monkeypatch):
    class Vault:
        def __init__(self): self.values = {}
        def get_password(self, service, user): return self.values.get((service, user))
        def set_password(self, service, user, value): self.values[(service, user)] = value
        def delete_password(self, service, user): del self.values[(service, user)]
    vault = Vault()
    store = CredentialStore()
    monkeypatch.setattr(store, "backend", lambda: vault)
    store.save("https://example.test/v1", "secret-placeholder")
    assert store.get("https://example.test/v1") == "secret-placeholder"
    assert store.get("https://other.test/v1") is None
    store.remove("https://example.test/v1")
    assert store.get("https://example.test/v1") is None


def test_api_schema_is_validated_without_network(monkeypatch):
    class Vault:
        def get(self, endpoint): return None
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size):
            return json.dumps({"choices": [{"message": {"content": json.dumps({"preset": "chaveiro", "parameters": {"text": "ANA", "width": 60}})}}]}).encode()
    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://example.test/v1/chat/completions"
            return Response()
    monkeypatch.setattr("bambu_ai.desktop.providers.build_opener", lambda *args: Opener())
    result = JsonAPIProvider("https://example.test/v1", "modelo", Vault()).interpret("chaveiro ANA")
    assert result.ready and result.spec().width == 60


def test_redirects_never_forward_credentials():
    with pytest.raises(ValueError, match="redirecionar"):
        NoRedirect().redirect_request(None, None, None, None, None, None)
