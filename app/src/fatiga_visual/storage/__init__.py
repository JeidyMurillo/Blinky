"""Persistencia local para estadísticas, informes y exportaciones.

- database.py: conexión SQLite, esquema y migraciones.
- repository.py: guardar muestras y consultar series.
"""

from fatiga_visual.storage.database import Database
from fatiga_visual.storage.repository import Repository

__all__ = ["Database", "Repository"]
