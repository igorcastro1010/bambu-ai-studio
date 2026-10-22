"""Miniatura geometrica rasterizada na CPU, sem navegador adicional."""
import numpy as np
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPolygonF
from ..validation import load_mesh


def thumbnail(source, target):
    mesh = load_mesh(source)
    vertices = mesh.vertices - mesh.bounds.mean(axis=0)
    matrix = np.array([[0.707, -0.707, 0], [0.408, 0.408, -0.816]])
    points = vertices @ matrix.T
    points -= (points.max(axis=0)+points.min(axis=0))/2
    points = points * (210 / max(float(np.ptp(points, axis=0).max()), 1e-9)) + 128
    depth = vertices @ np.array([1, 1, 1])
    order = np.argsort(depth[mesh.faces].mean(axis=1))
    image = QImage(256, 256, QImage.Format.Format_RGB32)
    image.fill(QColor("#18232c"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    for index in order:
        brightness = 0.6 + 0.4*abs(float(mesh.face_normals[index] @ np.array([0.2, 0.4, 0.8])))
        painter.setBrush(QColor(int(80*brightness), int(210*brightness), int(170*brightness)))
        painter.drawPolygon(QPolygonF([QPointF(*point) for point in points[mesh.faces[index]]]))
    painter.end()
    if not image.save(str(target), "PNG"):
        raise ValueError("Não foi possível salvar a miniatura")
