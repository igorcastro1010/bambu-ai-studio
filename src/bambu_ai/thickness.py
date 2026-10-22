"""Distancia ate a primeira face oposta por raios internos amostrados, sem rtree."""
import numpy as np


def estimate_walls(mesh, threshold=0.8):
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("Limiar de parede deve ser finito e positivo em mm")
    result = {
        "status": "unavailable", "method": "sampled_inward_normal_rays",
        "threshold_mm": threshold, "sampled_faces": 0, "hit_count": 0,
        "potentially_thin_samples": 0, "minimum_observed_mm": None,
        "thin_face_indices": [],
        "limitation": "Amostragem de cordas internas; pode perder paredes pequenas/obliquas. Nao certifica espessura minima ou imprimibilidade.",
    }
    if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume <= 0:
        result["reason"] = "Requer malha fechada, orientada e com volume positivo"
        return result
    # Limitar custo a ~2 milhoes de pares raio/triangulo, ate 128 amostras.
    count = min(128, len(mesh.faces), max(1, 2_000_000 // len(mesh.faces)))
    cumulative = np.cumsum(mesh.area_faces)
    indices = np.unique(np.searchsorted(cumulative, (np.arange(count)+0.5)*cumulative[-1]/count))
    triangles = mesh.triangles
    edge1 = triangles[:, 1] - triangles[:, 0]
    edge2 = triangles[:, 2] - triangles[:, 0]
    epsilon = max(float(mesh.extents.max()) * 1e-9, 1e-8)
    distances, thin = [], []
    for index in indices:
        direction = -mesh.face_normals[index]
        origin = mesh.triangles_center[index] + direction*epsilon
        cross = np.cross(direction, edge2)
        determinant = np.einsum("ij,ij->i", edge1, cross)
        inverse = np.divide(1.0, determinant, out=np.zeros_like(determinant),
                            where=np.abs(determinant) > 1e-12)
        delta = origin - triangles[:, 0]
        u = np.einsum("ij,ij->i", delta, cross)*inverse
        q = np.cross(delta, edge1)
        v = (q @ direction)*inverse
        distance = np.einsum("ij,ij->i", edge2, q)*inverse
        hits = ((np.abs(determinant) > 1e-12) & (u >= -1e-9) & (v >= -1e-9)
                & (u+v <= 1+1e-9) & (distance > epsilon)
                & ((mesh.face_normals @ direction) > 1e-8))
        hits[index] = False
        if hits.any():
            observed = float(distance[hits].min()+epsilon)
            distances.append(observed)
            if observed < threshold:
                thin.append(int(index))
    result.update(status="estimated" if distances else "unavailable", sampled_faces=len(indices),
                  hit_count=len(distances), potentially_thin_samples=len(thin),
                  minimum_observed_mm=round(min(distances), 5) if distances else None,
                  thin_face_indices=thin)
    if not distances:
        result["reason"] = "Nenhum raio encontrou uma face oposta"
    return result
