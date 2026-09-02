"""Cliente asincrono para las fichas de Playas de Espana."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

from .const import FLAG_UNKNOWN

BASE_URL = "https://playas-espana.com"
USER_AGENT = "Mozilla/5.0 (compatible; HomeAssistant-playas_espana)"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

_FLIGHT_RE = re.compile(r"self\.__next_f\.push\(\[1,(.+)\]\)")
_BEACH_MARKER = '{"playa":'
_VALID_PATH_RE = re.compile(r"^/(?:en/)?beaches/[^/]+/?$")


class PlayasEspanaError(Exception):
    """Error al hablar con la web de Playas de Espana."""


@dataclass(slots=True)
class Playa:
    """Datos actuales de una ficha de playa."""

    slug: str
    nombre: str
    municipio: str | None
    provincia: str | None
    bandera: str = FLAG_UNKNOWN
    atributos: dict[str, Any] = field(default_factory=dict)


def normalizar_url(url: str) -> str:
    """Valida una URL de ficha y devuelve su forma canonica sin barra final."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.netloc not in {
        "playas-espana.com",
        "www.playas-espana.com",
    } or not _VALID_PATH_RE.fullmatch(parsed.path):
        raise ValueError("URL de playa no valida")
    return f"{BASE_URL}{parsed.path.rstrip('/')}"


def _flight_payloads(html: str) -> list[str]:
    """Decodifica los fragmentos JSON de React Flight incluidos en el HTML."""
    soup = BeautifulSoup(html, "html.parser")
    payloads: list[str] = []
    for script in soup.find_all("script"):
        contenido = script.string or ""
        match = _FLIGHT_RE.search(contenido)
        if not match:
            continue
        try:
            payloads.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return payloads


def parse_ficha_playa(html: str) -> Playa:
    """Extrae los datos de la playa de la carga React de una ficha."""
    decoder = json.JSONDecoder()
    data: dict[str, Any] | None = None
    for payload in _flight_payloads(html):
        marker = payload.find(_BEACH_MARKER)
        if marker < 0:
            continue
        try:
            candidate, _ = decoder.raw_decode(payload[marker:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and isinstance(candidate.get("playa"), dict):
            data = candidate
            break

    if data is None:
        raise PlayasEspanaError("No se encontraron datos de playa en la respuesta")

    playa = data["playa"]
    nombre = playa.get("nombre")
    slug = playa.get("slug")
    if not isinstance(nombre, str) or not isinstance(slug, str):
        raise PlayasEspanaError("La ficha no contiene un nombre de playa valido")

    meteo = data.get("meteo") if isinstance(data.get("meteo"), dict) else {}
    bandera_data = data.get("banderaPlaya") if isinstance(data.get("banderaPlaya"), dict) else {}
    bandera = bandera_data.get("color", FLAG_UNKNOWN)
    if bandera not in {"verde", "amarilla", "roja"}:
        bandera = FLAG_UNKNOWN

    atributos = {
        "comunidad": playa.get("comunidad"),
        "latitude": playa.get("lat"),
        "longitude": playa.get("lng"),
        "tipo": playa.get("tipo"),
        "composicion": playa.get("composicion"),
        "socorrismo": playa.get("socorrismo"),
        "duchas": playa.get("duchas"),
        "accesible": playa.get("accesible"),
        "parking": playa.get("parking"),
        "bandera_azul": playa.get("bandera"),
        "perros": playa.get("perros"),
        "nudista": playa.get("nudista"),
        "temperatura_agua": meteo.get("agua"),
        "oleaje": meteo.get("olas"),
        "periodo_oleaje": meteo.get("periodo"),
        "viento": meteo.get("viento"),
        "racha_viento": meteo.get("vientoRacha"),
        "direccion_viento": meteo.get("vientoDireccion"),
        "indice_uv": meteo.get("uv"),
        "temperatura_aire": meteo.get("tempAire"),
        "humedad": meteo.get("humedad"),
        "condiciones": data.get("estado", {}).get("label") if isinstance(data.get("estado"), dict) else None,
        "descripcion_bandera": bandera_data.get("label"),
    }
    return Playa(
        slug=slug,
        nombre=nombre,
        municipio=playa.get("municipio"),
        provincia=playa.get("provincia"),
        bandera=bandera,
        atributos={key: value for key, value in atributos.items() if value is not None},
    )


class PlayasEspanaClient:
    """Cliente HTTP para fichas individuales de Playas de Espana."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_playa(self, url: str) -> Playa:
        """Descarga y parsea una ficha de playa."""
        try:
            async with self._session.get(
                normalizar_url(url),
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            ) as response:
                response.raise_for_status()
                html = await response.text()
        except ValueError:
            raise
        except TimeoutError as err:
            raise PlayasEspanaError("Tiempo de espera agotado") from err
        except aiohttp.ClientError as err:
            raise PlayasEspanaError(f"Error de conexion: {err}") from err
        return parse_ficha_playa(html)
