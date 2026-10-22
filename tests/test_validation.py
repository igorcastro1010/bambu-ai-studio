import json
import numpy as np
import pytest
import trimesh
from bambu_ai.cli import main
from bambu_ai.validation import validate
from bambu_ai.spec import ModelSpec


def write_mesh(tmp_path, mesh):
    path = tmp_path / "test.stl"
    mesh.export(path)
    return path


def test_closed_box(tmp_path):
    report = validate(write_mesh(tmp_path, trimesh.creation.box([20, 30, 4])))
    assert report["valid"]
    assert report["dimensions_mm"] == [20, 30, 4]
    assert report["volume_mm3"] == pytest.approx(2400)


def test_open_mesh_rejected(tmp_path):
    mesh = trimesh.creation.box()
    mesh.update_faces(np.arange(len(mesh.faces)-1))
    assert not validate(write_mesh(tmp_path, mesh))["valid"]


def test_disconnected_mesh_rejected(tmp_path):
    first = trimesh.creation.box()
    second = first.copy()
    second.apply_translation([10, 0, 0])
    assert not validate(write_mesh(tmp_path, first + second))["valid"]


def test_volume_limit_and_cli_exit(tmp_path, capsys):
    path = write_mesh(tmp_path, trimesh.creation.box([181, 20, 3]))
    assert not validate(path)["fits_a1_mini"]
    assert main(["validate", str(path)]) == 1
    assert json.loads(capsys.readouterr().out)["valid"] is False


@pytest.mark.parametrize("changes", [
    {"width": -1}, {"width": float("nan")}, {"depth": True},
    {"text": ""}, {"text": "A\nB"}, {"hole_diameter": 23}, {"kind": "unknown"},
    {"kind": "phone_stand", "thickness": 12, "depth": 70},
    {"kind": []},
])
def test_invalid_parameters(changes):
    with pytest.raises(ValueError):
        ModelSpec(**({"kind": "keychain"} | changes))


def test_unknown_json_field(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"kind": "sign", "widht": 20}')
    with pytest.raises(ValueError, match="desconhecidos"):
        ModelSpec.load(path)


def test_invalid_cli_input(tmp_path):
    assert main(["validate", str(tmp_path / "missing.stl")]) == 2


def test_nonfinite_coordinates_rejected(tmp_path):
    mesh = trimesh.creation.box()
    mesh.vertices[0, 0] = float("nan")
    with pytest.raises(ValueError, match="nao finitas"):
        validate(write_mesh(tmp_path, mesh))
