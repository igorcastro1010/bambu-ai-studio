"""HTML autonomo: sem CDN, servidor ou acesso a impressora."""
from pathlib import Path
import plotly.graph_objects as go
from .validation import load_mesh


def preview(source: Path, output: Path):
    mesh = load_mesh(source)
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    figure = go.Figure(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k,
                               color="#52bd98", flatshading=True))
    figure.update_layout(title="Bambu AI Studio | arraste para girar, role para zoom",
                         template="plotly_dark", margin=dict(l=0, r=0, b=0, t=60),
                         scene=dict(aspectmode="data", xaxis_title="X (mm)",
                                    yaxis_title="Y (mm)", zaxis_title="Z (mm)"))
    figure.write_html(str(output), include_plotlyjs=True, full_html=True,
                      config={"displaylogo": False, "responsive": True})
    return output
