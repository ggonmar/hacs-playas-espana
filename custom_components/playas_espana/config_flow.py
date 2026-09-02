"""Flujo de configuracion de Playas de Espana."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import PlayasEspanaClient, PlayasEspanaError, normalizar_url
from .const import CONF_PLAYAS, DOMAIN
from .coordinator import PlayasEspanaConfigEntry

PLAYAS_SELECTOR = TextSelector(
    TextSelectorConfig(type=TextSelectorType.TEXT, multiline=True)
)


def _parse_urls(raw: str) -> list[str]:
    """Lee una URL de playa por linea y elimina duplicados."""
    urls: list[str] = []
    for linea in raw.splitlines():
        if not linea.strip():
            continue
        url = normalizar_url(linea)
        if url not in urls:
            urls.append(url)
    if not urls:
        raise ValueError("No hay URLs")
    return urls


async def _validar_urls(hass: Any, urls: list[str]) -> bool:
    """Comprueba que todas las URLs corresponden a fichas publicadas."""
    client = PlayasEspanaClient(async_get_clientsession(hass))
    try:
        await __import__("asyncio").gather(*(client.async_get_playa(url) for url in urls))
    except PlayasEspanaError:
        return False
    return True


class PlayasEspanaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta de una o varias playas por sus URLs publicas."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                urls = _parse_urls(user_input[CONF_PLAYAS])
            except ValueError:
                errors[CONF_PLAYAS] = "invalid_url"
            else:
                if not await _validar_urls(self.hass, urls):
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id("|".join(sorted(urls)))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Playas de Espana ({len(urls)} playas)",
                        data={CONF_PLAYAS: urls},
                    )

        schema = vol.Schema(
            {vol.Required(CONF_PLAYAS, default=(user_input or {}).get(CONF_PLAYAS, "")): PLAYAS_SELECTOR}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(entry: PlayasEspanaConfigEntry) -> OptionsFlow:
        return PlayasEspanaOptionsFlow()


class PlayasEspanaOptionsFlow(OptionsFlow):
    """Permite cambiar las fichas seleccionadas."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                urls = _parse_urls(user_input[CONF_PLAYAS])
            except ValueError:
                errors[CONF_PLAYAS] = "invalid_url"
            else:
                if not await _validar_urls(self.hass, urls):
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(data={CONF_PLAYAS: urls})

        actuales = "\n".join(
            (user_input or {}).get(CONF_PLAYAS, self.config_entry.options.get(CONF_PLAYAS, self.config_entry.data[CONF_PLAYAS]))
        )
        schema = vol.Schema({vol.Required(CONF_PLAYAS, default=actuales): PLAYAS_SELECTOR})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
