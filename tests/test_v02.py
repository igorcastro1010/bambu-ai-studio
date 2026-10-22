import json
import numpy as np
import pytest
import trimesh
from bambu_ai.cli import main
from bambu_ai.presets import from_preset
from bambu_ai.validation import validate
from bambu_ai.viewer import build_figure, preview


def test_presets_use_independent_defaults():
    assert from_preset("suporte-celular").depth == 70
    assert from_preset("placa").width == 120
    assert from_preset("chaveiro", text="ANA", width=60).text == "ANA"
    assert from_preset("chaveiro").width == 70


@pytest.mark.parametrize("preset,parameters", [
    ("suporte-celular", {"text": "ANA"}), ("placa", {"hole_diameter": 4}),
    ("chaveiro", {"height": 40}), ("unknown", {}), ("placa", {"width": -1}),
])
def test_preset_rejects_ignored_or_invalid_options(preset, parameters):
    with pytest.raises(ValueError):
        from_preset(preset, **parameters)


def test_create_cli_routes_readable_parameters(tmp_path, monkeypatch, capsys):
    calls = []
    def generate(spec, output, backend, **options):
        calls.append((spec, output, backend, options))
        return {"valid": True}
    monkeypatch.setattr("bambu_ai.cli.generate", generate)
    assert main(["create", "chaveiro", "--nome", "ANA", "--largura", "60",
                 "--diametro-furo", "4", "--out", str(tmp_path / "ana"),
                 "--backend", "build123d", "--stl-only", "--no-preview"]) == 0
    assert calls[0][0].text == "ANA" and calls[0][0].width == 60
    assert calls[0][0].hole_diameter == 4
    assert calls[0][2:] == ("build123d", {"step": False, "html": False})
    assert json.loads(capsys.readouterr().out)["valid"]


def test_create_rejects_irrelevant_option(tmp_path):
    assert main(["create", "suporte-celular", "--nome", "ANA", "--out", str(tmp_path / "bad")]) == 2
    assert not (tmp_path / "bad").exists()


def test_wall_estimate_warns_without_failing_geometry(tmp_path):
    source = tmp_path / "thin.stl"
    trimesh.creation.box([20, 15, 0.5]).export(source)
    report = validate(source)
    assert report["valid"]
    assert report["wall_analysis"]["minimum_observed_mm"] == pytest.approx(0.5)
    assert report["wall_analysis"]["potentially_thin_samples"] > 0
    assert any("potencialmente finas" in warning for warning in report["warnings"])
    assert validate(source, wall_threshold=0.4)["wall_analysis"]["potentially_thin_samples"] == 0


def test_thick_box_has_no_thin_samples(tmp_path):
    source = tmp_path / "thick.stl"
    trimesh.creation.box([20, 15, 5]).export(source)
    report = validate(source)
    assert report["wall_analysis"]["status"] == "estimated"
    assert report["wall_analysis"]["minimum_observed_mm"] == pytest.approx(5)
    assert report["wall_analysis"]["potentially_thin_samples"] == 0
    assert any("nao garante" in warning for warning in report["warnings"])


def test_thin_wall_after_rotation_and_translation(tmp_path):
    mesh = trimesh.creation.box([20, 15, 0.5])
    mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi/5, [1, 2, 3]))
    mesh.apply_translation([30, -10, 12])
    source = tmp_path / "rotated.stl"
    mesh.export(source)
    report = validate(source)
    assert min(report["dimensions_mm"]) > 0.8
    assert report["wall_analysis"]["potentially_thin_samples"] > 0
    assert report["wall_analysis"]["minimum_observed_mm"] == pytest.approx(0.5, abs=0.001)


def test_wall_threshold_cli(tmp_path, capsys):
    source = tmp_path / "thin.stl"
    trimesh.creation.box([20, 15, 0.5]).export(source)
    assert main(["validate", str(source), "--wall-threshold", "0.4"]) == 0
    assert json.loads(capsys.readouterr().out)["wall_analysis"]["potentially_thin_samples"] == 0


def test_open_mesh_reports_boundary_without_wall_claim(tmp_path):
    source = tmp_path / "open.stl"
    mesh = trimesh.creation.box()
    mesh.update_faces(np.arange(11))
    mesh.export(source)
    report = validate(source)
    assert not report["valid"] and report["boundary_edges"] == 3
    assert report["wall_analysis"]["status"] == "unavailable"
    assert report["wall_analysis"]["minimum_observed_mm"] is None


def test_nonmanifold_edges_reported(tmp_path):
    mesh = trimesh.creation.box()
    mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=np.vstack([mesh.faces, mesh.faces[0]]), process=False)
    source = tmp_path / "nonmanifold.stl"
    mesh.export(source)
    report = validate(source)
    assert not report["valid"] and report["nonmanifold_edges"] == 3
    assert report["wall_analysis"]["status"] == "unavailable"


@pytest.mark.parametrize("threshold", [0, -1, float("nan"), float("inf")])
def test_invalid_wall_threshold(tmp_path, threshold):
    source = tmp_path / "box.stl"
    trimesh.creation.box().export(source)
    with pytest.raises(ValueError, match="Limiar"):
        validate(source, wall_threshold=threshold)


@pytest.mark.parametrize("size,fits", [([180, 180, 180], True), ([20, 181, 20], False), ([20, 20, 181], False)])
def test_a1_dimensions_each_axis(tmp_path, size, fits):
    source = tmp_path / "box.stl"
    trimesh.creation.box(size).export(source)
    assert validate(source)["fits_a1_mini"] is fits


def test_preview_modes_dimensions_and_normals(tmp_path):
    mesh = trimesh.creation.box([20, 30, 4])
    figure = build_figure(mesh)
    assert figure.layout.scene.dragmode == "orbit"
    assert figure.layout.scene.aspectmode == "data"
    assert "20.00 × 30.00 × 4.00" in figure.layout.title.text
    assert len(figure.data[0].i) == len(mesh.faces)
    # Cada aresta e cada normal terminam com NaN para separar os segmentos.
    assert np.isnan(np.asarray(figure.data[1].x).reshape(-1, 3)[:, 2]).all()
    assert len(figure.layout.updatemenus[0].buttons) == 4
    assert figure.layout.updatemenus[0].buttons[1].args[0]["visible"] == [True, True, False]
    assert figure.layout.updatemenus[0].buttons[3].args[0]["visible"] == [True, True, True]
    source = tmp_path / "box.stl"
    mesh.export(source)
    output = preview(source, tmp_path / "box.html")
    content = output.read_text(encoding="utf-8")
    assert '"scrollZoom": true' in content
    assert '<script src=' not in content
