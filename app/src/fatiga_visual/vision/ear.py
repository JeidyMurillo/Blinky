"""Cálculo del Eye Aspect Ratio (EAR).

Qué va aquí:
- La fórmula geométrica pura, sin cámara ni MediaPipe.
- Los índices de landmarks de MediaPipe para cada ojo.

EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
"""

import math

LEFT_EYE_INDICES = (362, 385, 387, 263, 373, 380)
RIGHT_EYE_INDICES = (33, 160, 158, 133, 153, 144)


def distance(point_a, point_b):
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def eye_aspect_ratio(points):
    """Calcula EAR con 6 puntos ordenados alrededor del ojo."""
    if len(points) != 6:
        raise ValueError("eye_aspect_ratio espera exactamente 6 puntos")
    vertical = distance(points[1], points[5]) + distance(points[2], points[4])
    horizontal = distance(points[0], points[3])
    if horizontal == 0:
        return 0.0
    return vertical / (2.0 * horizontal)


def _scaled_points(points, indices, width, height):
    scaled = []
    for index in indices:
        landmark = points[index]
        if hasattr(landmark, "x"):
            x, y = landmark.x, landmark.y
        else:
            x, y = landmark[0], landmark[1]
        scaled.append((x * width, y * height))
    return scaled


def eye_aspect_ratios(points, width, height):
    """Devuelve (EAR izquierdo, EAR derecho) desde landmarks normalizados."""
    left = _scaled_points(points, LEFT_EYE_INDICES, width, height)
    right = _scaled_points(points, RIGHT_EYE_INDICES, width, height)
    return eye_aspect_ratio(left), eye_aspect_ratio(right)


def average_eye_aspect_ratio(points, width, height):
    """Calcula el EAR medio de ambos ojos desde landmarks normalizados."""
    left, right = eye_aspect_ratios(points, width, height)
    return (left + right) / 2.0
