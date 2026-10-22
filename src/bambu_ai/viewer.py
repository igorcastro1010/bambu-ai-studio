"""HTML autonomo: sem CDN, servidor ou acesso a impressora."""
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from .validation import load_mesh


def build_figure(mesh):
    """Separado da escrita HTML para testar modos, escala e geometria exibida."""
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    figure = go.Figure(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k,
                               name="Superficie", color="#52bd98", flatshading=True,
                               hovertemplate="X: %{x:.2f} mm<br>Y: %{y:.2f} mm<br>Z: %{z:.2f} mm<extra></extra>"))
    edges = mesh.vertices[mesh.edges_unique]
    wire = np.full((len(edges), 3, 3), np.nan)
    wire[:, :2] = edges
    figure.add_trace(go.Scatter3d(x=wire[:, :, 0].ravel(), y=wire[:, :, 1].ravel(),
                                 z=wire[:, :, 2].ravel(), mode="lines", name="Arestas",
                                 line=dict(color="#d8e5ed", width=2), hoverinfo="skip", visible=False))
    # Normais amostradas para manter o navegador responsivo.
    indices = np.linspace(0, len(mesh.faces)-1, min(200, len(mesh.faces)), dtype=int)
    starts = mesh.triangles_center[indices]
    ends = starts + mesh.face_normals[indices] * max(float(mesh.extents.max())*0.04, 0.5)
    normals = np.full((len(indices), 3, 3), np.nan)
    normals[:, 0], normals[:, 1] = starts, ends
    labels = [f"Face {index} (normal da face)" for index in indices for _ in range(3)]
    figure.add_trace(go.Scatter3d(x=normals[:, :, 0].ravel(), y=normals[:, :, 1].ravel(),
                                 z=normals[:, :, 2].ravel(), mode="lines+markers", name="Normais amostradas",
                                 text=labels, hovertemplate="%{text}<extra></extra>",
                                 line=dict(color="#ffb36b", width=3),
                                 marker=dict(size=[size for _ in indices for size in (0, 3, 0)]), visible=False))
    dimensions = " × ".join(f"{value:.2f}" for value in mesh.extents)
    camera = dict(eye=dict(x=1.5, y=-1.8, z=1.3), up=dict(x=0, y=0, z=1))
    modes = []
    for label, visible, opacity in (("Solido", [True, False, False], 1),
                                    ("Faces / arestas", [True, True, False], 1),
                                    ("Transparente", [True, True, False], 0.3),
                                    ("Normais", [True, True, True], 1)):
        modes.append(dict(label=label, method="restyle", args=[{"visible": visible, "opacity": [opacity, 1, 1]}]))
    views = [dict(label="Isometrica / reset", method="relayout", args=[{"scene.camera": camera}])]
    for label, eye, up in (("Topo", dict(x=0, y=0, z=2.5), dict(x=0, y=1, z=0)),
                            ("Frente", dict(x=0, y=-2.5, z=0), dict(x=0, y=0, z=1)),
                            ("Lado", dict(x=2.5, y=0, z=0), dict(x=0, y=0, z=1))):
        views.append(dict(label=label, method="relayout", args=[{"scene.camera": dict(eye=eye, up=up)}]))
    figure.update_layout(title=dict(text=f"Bambu AI Studio 0.2 | {dimensions} mm (X × Y × Z)", font_size=18),
                         template="plotly_dark", showlegend=False, margin=dict(l=0, r=0, b=65, t=120),
                         updatemenus=[dict(type="dropdown", buttons=modes, x=0.01, y=1.14),
                                      dict(type="dropdown", buttons=views, x=0.42, y=1.14)],
                         annotations=[dict(text=f"{len(mesh.faces):,} faces | Arraste: girar · scroll: zoom · botao direito: mover<br>"
                                                 "Faces: triangulacao STL · Normais: ate 200 amostras · Unidades assumidas em mm",
                                           x=0.5, y=-0.10, xref="paper", yref="paper", showarrow=False)],
                         scene=dict(aspectmode="data", dragmode="orbit", camera=camera,
                                    xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="Z (mm)"))
    return figure


def preview(source: Path, output: Path):
    figure = build_figure(load_mesh(source))
    figure.write_html(str(output), include_plotlyjs=True, full_html=True,
                      default_height="100vh", default_width="100%",
                      config={"displaylogo": False, "responsive": True, "scrollZoom": True})
    return output
