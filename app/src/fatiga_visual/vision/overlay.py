"""Geometría del overlay facial sobre el video de la UI.

El feed se dibuja con escala `cover` y recorte central. Estas funciones pasan
los landmarks normalizados del fotograma completo a coordenadas del widget,
teniendo en cuenta ese recorte. No importan Tk ni MediaPipe: solo números.
"""


def cover_crop(source_w, source_h, feed_w, feed_h):
    """Devuelve (new_w, new_h, left, top) del escalado cover + recorte."""
    scale = max(feed_w / float(source_w), feed_h / float(source_h))
    new_w = max(feed_w, round(source_w * scale))
    new_h = max(feed_h, round(source_h * scale))
    return new_w, new_h, (new_w - feed_w) // 2, (new_h - feed_h) // 2


def project_points(points, new_w, new_h, left, top):
    """Pasa puntos normalizados del fotograma escalado a píxeles del feed."""
    return tuple(
        (round(x * new_w - left), round(y * new_h - top)) for x, y in points
    )


def project_overlay(overlay, source_w, source_h, feed_w, feed_h):
    """Proyecta todos los puntos de un `FaceOverlay` al tamaño del widget."""
    new_w, new_h, left, top = cover_crop(source_w, source_h, feed_w, feed_h)
    return {
        "oval": project_points(overlay.oval, new_w, new_h, left, top),
        "left_eye": project_points(overlay.left_eye, new_w, new_h, left, top),
        "right_eye": project_points(overlay.right_eye, new_w, new_h, left, top),
        "irises": project_points(overlay.irises, new_w, new_h, left, top),
    }
