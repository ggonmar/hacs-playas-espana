"""Constantes de la integracion Playas de Espana."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "playas_espana"

CONF_PLAYAS: Final = "playas"

DEFAULT_SCAN_INTERVAL: Final = timedelta(hours=1)

ATTRIBUTION: Final = "Datos facilitados por Playas de Espana"

FLAG_UNKNOWN: Final = "sin_bandera"
FLAG_STATES: Final = ["verde", "amarilla", "roja", FLAG_UNKNOWN]
