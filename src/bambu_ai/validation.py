"""Triagem geometrica; nao substitui fatiamento ou ensaio mecanico."""
from pathlib import Path
import numpy as np
import trimesh
from .thickness import estimate_walls


def load_mesh(path: Path):
    if path.suffix.lower() != ".stl":
        raise ValueError("Validacao/preview recebem STL; exporte STEP para STL via motor CAD")
    mesh = trimesh.load_mesh(path, process=False)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ValueError("Malha vazia ou formato invalido")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError("Malha contem coordenadas nao finitas")
    # STL repete vertices por triangulo: soldar posicoes para avaliar topologia,
    # sem tapar furos, remover faces ou corrigir normais.
    mesh.merge_vertices()
    return mesh


def validate(path: Path, wall_threshold=0.8):
    mesh = load_mesh(path)
    dimensions = mesh.extents
    components = len(trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), engine="scipy"))
    errors = []
    edge_counts = np.bincount(mesh.edges_unique_inverse)
    boundary_edges = int(np.count_nonzero(edge_counts == 1))
    nonmanifold_edges = int(np.count_nonzero(edge_counts > 2))
    if not mesh.is_watertight:
        errors.append("Malha nao estanque: aberta ou nao manifold")
    if not mesh.is_winding_consistent:
        errors.append("Orientacao inconsistente das faces")
    if mesh.volume <= 0:
        errors.append("Volume nao positivo")
    if np.any(dimensions <= 0):
        errors.append("Malha sem espessura")
    if not mesh.nondegenerate_faces().all():
        errors.append("Faces degeneradas")
    if components != 1:
        errors.append(f"Esperado um componente conectado, encontrados {components}")
    fits = bool(np.all(dimensions <= 180.0001))
    if not fits:
        errors.append("Excede 180 x 180 x 180 mm na orientacao atual")
    normals = mesh.face_normals
    bottom = mesh.triangles_center[:, 2] <= mesh.bounds[0, 2] + 0.15
    overhang = (normals[:, 2] < -np.cos(np.deg2rad(45))) & ~bottom
    area = float(mesh.area_faces[overhang].sum())
    walls = estimate_walls(mesh, wall_threshold)
    warnings = ["Unidades assumidas em mm (STL nao registra unidades).",
                "Nao verifica auto-intersecoes nem resistencia; espessura e apenas estimada por amostragem.",
                "PLA: confirmar perfil e suportes no fatiador antes de imprimir."]
    if walls["potentially_thin_samples"]:
        warnings.append(f"Paredes potencialmente finas: {walls['potentially_thin_samples']} amostras abaixo de {wall_threshold} mm; conferir no fatiador.")
    elif walls["status"] == "estimated":
        warnings.append("Sem alerta nas amostras de parede; isso nao garante ausencia de paredes finas.")
    else:
        warnings.append("Analise de paredes indisponivel: " + walls["reason"])
    if area > 1:
        warnings.append("Faces descendentes >45 graus: revisar suportes/ponte no fatiador.")
    return {
        "valid": not errors, "dimensions_mm": dimensions.round(3).tolist(),
        "fits_a1_mini": fits, "watertight": bool(mesh.is_watertight),
        "boundary_edges": boundary_edges, "nonmanifold_edges": nonmanifold_edges,
        "wall_analysis": walls,
        "winding_consistent": bool(mesh.is_winding_consistent), "components": components,
        "volume_mm3": round(float(mesh.volume), 3), "triangles": len(mesh.faces),
        "overhang_area_mm2_estimate": round(area, 3), "errors": errors, "warnings": warnings,
        "preparation": {"printer": "Bambu Lab A1 mini", "material": "PLA",
                        "bed_mm": [180, 180, 180], "orientation": "Base plana em Z minimo; centralizar no fatiador",
                        "ams_lite": "Ate 4 filamentos; STL e monocor. Atribuir cores manualmente no Bambu Studio.",
                        "margin": "Reservar espaco adicional para brim/purga; limite nominal nao garante fatiamento."},
    }
