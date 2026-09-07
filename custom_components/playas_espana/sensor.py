"""Sensores de condiciones de playa."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import ATTRIBUTION, DOMAIN, FLAG_STATES
from .coordinator import PlayasEspanaConfigEntry, PlayasEspanaCoordinator
from .icons_map import flag_entity_picture


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PlayasEspanaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea un sensor por ficha configurada."""
    coordinator = entry.runtime_data
    conocidas: set[str] = set()

    @callback
    def _anadir_nuevas() -> None:
        nuevas = set(coordinator.data or {}) - conocidas
        if nuevas:
            conocidas.update(nuevas)
            async_add_entities(BanderaPlayaSensor(coordinator, slug) for slug in nuevas)

    entry.async_on_unload(coordinator.async_add_listener(_anadir_nuevas))
    _anadir_nuevas()


class BanderaPlayaSensor(CoordinatorEntity[PlayasEspanaCoordinator], SensorEntity):
    """Bandera estimada a partir de las condiciones de una playa."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_attribution = ATTRIBUTION
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = FLAG_STATES
    _attr_translation_key = "bandera"

    def __init__(self, coordinator: PlayasEspanaCoordinator, slug: str) -> None:
        super().__init__(coordinator)
        self._slug = slug
        self._attr_unique_id = f"{DOMAIN}_{slug}"
        playa = coordinator.data[slug]
        self._attr_name = f"Playa {playa.nombre}"
        self.entity_id = f"sensor.playa_{slugify(playa.nombre)}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, slug)},
            name=f"Playa {playa.nombre}",
            manufacturer="Playas de Espana",
            model=playa.provincia,
            suggested_area=playa.municipio,
            configuration_url=f"https://playas-espana.com/en/beaches/{slug}",
        )

    @property
    def available(self) -> bool:
        return super().available and self._slug in (self.coordinator.data or {})

    @property
    def native_value(self) -> str | None:
        playa = (self.coordinator.data or {}).get(self._slug)
        return playa.bandera if playa else None

    @property
    def entity_picture(self) -> str | None:
        """Icono de bandera para mostrarlo en el mapa."""
        playa = (self.coordinator.data or {}).get(self._slug)
        if playa is None:
            return None
        return flag_entity_picture(playa.bandera)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        playa = (self.coordinator.data or {}).get(self._slug)
        if playa is None:
            return {}
        return {
            "nombre": playa.nombre,
            "municipio": playa.municipio,
            "provincia": playa.provincia,
            **playa.atributos,
        }
