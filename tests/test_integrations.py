import pytest
from bambu_ai import integrations


def test_openscad_only_exports_stl(tmp_path, monkeypatch):
    source = tmp_path / "part.scad"
    source.write_text("cube(10);")
    monkeypatch.setattr(integrations, "executable", lambda *a: "openscad.exe")
    calls = []
    monkeypatch.setattr(integrations.subprocess, "run", lambda argv, **kw: calls.append((argv, kw)))
    integrations.render_scad(source, tmp_path / "part.stl")
    assert calls[0][0] == ["openscad.exe", "-o", str((tmp_path / "part.stl").resolve()), str(source.resolve())]
    assert calls[0][1]["check"] is True


def test_studio_only_opens_file(tmp_path, monkeypatch):
    source = tmp_path / "part.stl"
    source.write_bytes(b"example")
    monkeypatch.setattr(integrations, "executable", lambda *a: "bambu-studio.exe")
    calls = []
    monkeypatch.setattr(integrations.subprocess, "Popen", lambda argv: calls.append(argv))
    integrations.open_studio(source)
    assert calls == [["bambu-studio.exe", str(source.resolve())]]


def test_bad_executable_configuration(monkeypatch):
    monkeypatch.setenv("OPENSCAD_PATH", "Z:/missing/openscad.exe")
    with pytest.raises(ValueError, match="OPENSCAD_PATH"):
        integrations.executable("openscad", "OPENSCAD_PATH")
