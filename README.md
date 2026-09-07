# Playas de Espana para Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Release](https://img.shields.io/github/v/release/ggonmar/hacs-playas-espana)](https://github.com/ggonmar/hacs-playas-espana/releases)
[![License](https://img.shields.io/github/license/ggonmar/hacs-playas-espana)](LICENSE)

Integracion personalizada para Home Assistant que publica las condiciones de las
playas de Espana a partir de las fichas de
[playas-espana.com](https://playas-espana.com/).

Cada ficha configurada genera un sensor de bandera estimada (`verde`, `amarilla`
o `roja`) y expone temperatura del agua y aire, oleaje, viento, UV, humedad,
servicios, Bandera Azul, municipio, provincia y coordenadas.

## Instalacion

### HACS

En HACS, abre el menu de repositorios personalizados y anade:

`https://github.com/ggonmar/hacs-playas-espana`

con la categoria **Integracion**. Instala **Playas de Espana** y reinicia Home
Assistant.

### Manual

Copia `custom_components/playas_espana` a
`config/custom_components/playas_espana` y reinicia Home Assistant.

## Configuracion

En *Ajustes* -> *Dispositivos y servicios* -> *Anadir integracion*, selecciona
**Playas de Espana**. Escribe una URL de ficha de Playas de Espana por linea:

```
https://playas-espana.com/en/beaches/playa-de-la-torre-derribada
```

La informacion se actualiza cada hora. La bandera es una **estimacion meteorologica
orientativa** calculada a partir del oleaje y viento, no un parte oficial. La
bandera oficial la iza el socorrista de cada playa y puede diferir: una bandera
roja real tambien puede deberse a medusas o a la calidad del agua (por ejemplo,
vertidos), situaciones que esta estimacion no detecta.

## Desarrollo

```bash
python scripts/test_playas_espana_parser.py
```

La prueba requiere `beautifulsoup4` y `aiohttp`.

## Aviso

Proyecto no oficial y sin relacion con Playas de Espana. Consulta siempre la
senalizacion y las indicaciones del personal de socorrismo.
