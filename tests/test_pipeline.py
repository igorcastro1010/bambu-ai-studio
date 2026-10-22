import importlib.util
from pathlib import Path
import pytest
from bambu_ai.pipeline import generate
from bambu_ai.spec import ModelSpec
from bambu_ai.validation import validate
from bambu_ai.viewer import preview

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["cadquery", "build123d"])
def backend(request):
    if importlib.util.find_spec(request.param) is None:
        pytest.skip(f"Motor opcional {request.param} ausente neste ambiente")
    return request.param


@pytest.mark.parametrize("example", ["chaveiro", "placa", "suporte-celular"])
def test_examples(tmp_path, backend, example):
    spec = ModelSpec.load(ROOT / "models" / f"{example}.json")
    out = tmp_path / example
    report = generate(spec, out, backend, html=False)
    assert report["valid"] and report["components"] == 1
    assert report["dimensions_mm"][:2] == pytest.approx([spec.width, spec.depth], abs=0.01)
    assert report["dimensions_mm"][2] == pytest.approx(
        spec.height if spec.kind == "phone_stand" else spec.thickness+spec.relief, abs=0.01)
    assert validate(out / "model.stl")["watertight"]
    assert "ISO-10303-21" in (out / "model.step").read_text()
    if backend == "cadquery":
        import cadquery as cq
        assert cq.importers.importStep(str(out / "model.step")).val().isValid()
    else:
        import build123d as b
        assert b.import_step(str(out / "model.step")).is_valid
    with pytest.raises(ValueError, match="ja existe"):
        generate(spec, out, backend)


def test_rejected_model_does_not_publish(tmp_path, backend):
    out = tmp_path / "oversized"
    with pytest.raises(ValueError, match="180"):
        generate(ModelSpec(kind="sign", width=200), out, backend, html=False)
    assert not out.exists()


def test_html_is_offline(tmp_path):
    import trimesh
    stl = tmp_path / "box.stl"
    trimesh.creation.box().export(stl)
    out = preview(stl, tmp_path / "preview.html")
    content = out.read_text(encoding="utf-8")
    assert "mesh3d" in content and "Plotly.newPlot" in content
    assert '<script src="https://' not in content


def test_long_accented_name(tmp_path, backend):
    report = generate(ModelSpec(kind="keychain", text="JOAO E MARIA ÁÉÇ"),
                      tmp_path / "name", backend, html=False)
    assert report["valid"] and report["dimensions_mm"] == pytest.approx([70, 24, 4], abs=0.01)
