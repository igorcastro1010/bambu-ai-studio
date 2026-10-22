"""Motores importados sob demanda; nunca carregar dois bindings OCP juntos."""
from pathlib import Path
from .spec import ModelSpec


def create(spec: ModelSpec, backend: str):
    if backend == "cadquery":
        import cadquery as cq

        if spec.kind == "phone_stand":
            return cq.Workplane("YZ").polyline(spec.stand_profile()).close().extrude(spec.width)
        part = cq.Workplane("XY").box(spec.width, spec.depth, spec.thickness,
                                      centered=(True, True, False))
        if spec.kind == "keychain":
            x = -spec.width/2 + spec.hole_diameter/2 + 2
            hole = cq.Workplane("XY").center(x, 0).circle(spec.hole_diameter/2).extrude(spec.thickness)
            part = part.cut(hole)
        available_w, available_d, offset = spec.text_layout()
        # Medir os glifos reais antes de ajustar o tamanho (nomes longos/acentos).
        text = cq.Workplane("XY").text(spec.text, spec.text_size, spec.relief + 0.1, font="Arial", combine=False)
        bounds = text.val().BoundingBox()
        scale = min(1, available_w / bounds.xlen, available_d / bounds.ylen)
        text = cq.Workplane("XY").text(spec.text, spec.text_size*scale, spec.relief+0.1,
                                      font="Arial", combine=False)
        bounds = text.val().BoundingBox()
        text = text.translate((offset-(bounds.xmin+bounds.xmax)/2,
                               -(bounds.ymin+bounds.ymax)/2, spec.thickness-0.1))
        return part.union(text).clean()
    if backend == "build123d":
        import build123d as b

        if spec.kind == "phone_stand":
            profile = b.Plane.YZ * b.Polygon(*spec.stand_profile(), align=None)
            return b.extrude(profile, amount=spec.width)
        part = b.Box(spec.width, spec.depth, spec.thickness,
                     align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        if spec.kind == "keychain":
            x = -spec.width/2 + spec.hole_diameter/2 + 2
            part -= b.Pos(x, 0, 0) * b.Cylinder(spec.hole_diameter/2, spec.thickness,
                           align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))
        available_w, available_d, offset = spec.text_layout()
        letters = b.Text(spec.text, font_size=spec.text_size, font="Arial")
        bounds = letters.bounding_box()
        scale = min(1, available_w / bounds.size.X, available_d / bounds.size.Y)
        letters = b.Text(spec.text, font_size=spec.text_size*scale, font="Arial")
        center = letters.bounding_box().center()
        text = b.extrude(letters, amount=spec.relief+0.1)
        return part + b.Pos(offset-center.X, -center.Y, spec.thickness-0.1)*text
    raise ValueError(f"Motor desconhecido: {backend}")


def export(shape, path: Path, backend: str):
    suffix = path.suffix.lower()
    if suffix not in {".stl", ".step"}:
        raise ValueError("CAD suporta somente STL e STEP neste MVP")
    if backend == "cadquery":
        import cadquery as cq
        if not shape.val().isValid() or len(shape.solids().vals()) != 1:
            raise ValueError("CAD invalido ou nao forma um unico solido")
        cq.exporters.export(shape, str(path), exportType="STL" if suffix == ".stl" else "STEP",
                            tolerance=0.05, angularTolerance=0.1)
    else:
        import build123d as b
        if not shape.is_valid or len(shape.solids()) != 1:
            raise ValueError("CAD invalido ou nao forma um unico solido")
        ok = b.export_stl(shape, str(path), tolerance=0.05, angular_tolerance=0.1) if suffix == ".stl" else b.export_step(shape, str(path))
        if not ok:
            raise ValueError(f"Falha ao exportar {path.name}")
