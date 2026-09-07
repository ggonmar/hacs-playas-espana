"""Prueba aislada del parser de Playas de Espana."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

RAIZ = pathlib.Path(__file__).resolve().parents[1]
COMPONENTE = RAIZ / "custom_components" / "playas_espana"
PAQUETE = "_playas_espana_standalone"


def _cargar_api() -> types.ModuleType:
    paquete = types.ModuleType(PAQUETE)
    paquete.__path__ = [str(COMPONENTE)]
    sys.modules[PAQUETE] = paquete
    for nombre in ("const", "api"):
        spec = importlib.util.spec_from_file_location(
            f"{PAQUETE}.{nombre}", COMPONENTE / f"{nombre}.py"
        )
        assert spec and spec.loader
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = modulo
        spec.loader.exec_module(modulo)
    return sys.modules[f"{PAQUETE}.api"]


def _cargar_iconos() -> types.ModuleType:
    api = _cargar_api()
    spec = importlib.util.spec_from_file_location(
        f"{PAQUETE}.icons_map", COMPONENTE / "icons_map.py"
    )
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def main() -> int:
    api = _cargar_api()
    html = '''<script>self.__next_f.push([1,"5b:[\\\"$\\\",\\\"main\\\",null,{\\\"playa\\\":{\\\"nombre\\\":\\\"Playa de prueba\\\",\\\"municipio\\\":\\\"Valencia\\\",\\\"provincia\\\":\\\"Valencia\\\",\\\"comunidad\\\":\\\"Comunidad Valenciana\\\",\\\"lat\\\":39.4,\\\"lng\\\":-0.3,\\\"slug\\\":\\\"playa-de-prueba\\\",\\\"socorrismo\\\":true,\\\"bandera\\\":true},\\\"meteo\\\":{\\\"agua\\\":25.5,\\\"olas\\\":0.4,\\\"viento\\\":9,\\\"uv\\\":3},\\\"estado\\\":{\\\"label\\\":\\\"BUENA\\\"},\\\"banderaPlaya\\\":{\\\"color\\\":\\\"verde\\\",\\\"label\\\":\\\"Mar en calma\\\"}}]\\n"])</script>'''
    playa = api.parse_ficha_playa(html)
    assert playa.slug == "playa-de-prueba"
    assert playa.bandera == "verde"
    assert playa.atributos["temperatura_agua"] == 25.5
    assert playa.atributos["latitude"] == 39.4
    assert playa.atributos["condiciones"] == "BUENA"
    assert api.normalizar_url("https://www.playas-espana.com/en/beaches/playa-de-prueba") == "https://playas-espana.com/en/beaches/playa-de-prueba"
    assert api.normalizar_url("https://playas-espana.com/playas/platja-nord-de-gandia") == "https://playas-espana.com/playas/platja-nord-de-gandia"
    assert api.normalizar_url("https://playas-espana.com/playas/platja-de-lahuir") == "https://playas-espana.com/playas/platja-de-lahuir"
    iconos = _cargar_iconos()
    assert iconos.flag_entity_picture("verde").startswith("data:image/svg+xml;base64,")
    assert iconos.flag_entity_picture("amarilla") != iconos.flag_entity_picture("roja")
    assert iconos.flag_entity_picture("sin_bandera") != iconos.flag_entity_picture("verde")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())