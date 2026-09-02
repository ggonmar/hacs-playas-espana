"""Coordinador de actualizacion de las fichas de Playas de Espana."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PlayasEspanaClient, PlayasEspanaError, Playa
from .const import CONF_PLAYAS, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type PlayasEspanaConfigEntry = ConfigEntry[PlayasEspanaCoordinator]


class PlayasEspanaCoordinator(DataUpdateCoordinator[dict[str, Playa]]):
    """Actualiza las fichas configuradas por el usuario."""

    config_entry: PlayasEspanaConfigEntry

    def __init__(self, hass: HomeAssistant, entry: PlayasEspanaConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = PlayasEspanaClient(async_get_clientsession(hass))
        self.urls: list[str] = entry.options.get(CONF_PLAYAS, entry.data[CONF_PLAYAS])

    async def _async_update_data(self) -> dict[str, Playa]:
        results = await asyncio.gather(
            *(self.client.async_get_playa(url) for url in self.urls),
            return_exceptions=True,
        )
        playas: dict[str, Playa] = {}
        failures: list[Exception] = []
        for result in results:
            if isinstance(result, Exception):
                failures.append(result)
            else:
                playas[result.slug] = result

        if failures and not playas:
            raise UpdateFailed(str(failures[0])) from failures[0]
        for error in failures:
            _LOGGER.warning("No se pudo actualizar una playa: %s", error)
        return playas
