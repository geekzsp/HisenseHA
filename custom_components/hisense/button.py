from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from homeassistant.const import EntityCategory
import logging
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)



async def async_setup_entry(hass, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = [HisenseACUpdateButton(api[device_id], config_entry.entry_id) for device_id in api]
    async_add_entities(entities, True)
    entities = [HisenseACRefreshTokenButton(api[device_id], config_entry.entry_id) for device_id in api]
    async_add_entities(entities, True)


class HisenseACUpdateButton(ButtonEntity):
    def __init__(self, api, config_entry_id):
        self._api = api
        self._config_entry_id = config_entry_id
        self._attr_name = f"Force update button"
        self._attr_unique_id = f"{api.device_id}_force_update_button"
        self._attr_icon = "mdi:refresh"

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._api.wifi_id[-12:])},
            "connections": {("mac", self._api.mac)},
            "name": "Hisense AC",
            "manufacturer": "Hisense",
        }

    @property
    def name(self):
        return "Force Update"

    async def async_press(self):
        """Handle the button press and notify all device entities to update."""
        _LOGGER.debug(f"Button pressed for entity: {self._attr_unique_id}")
        await self._api.check_status()
        
        _LOGGER.debug("Starting device entities update process")
        # Notify all entities of the same device to update
        device_registry = await dr.async_get(self.hass)
        entity_registry = await er.async_get(self.hass)
        _LOGGER.debug("Successfully retrieved device and entity registries")
        
        # Get device ID from current entity's device info
        device_id = next(iter(self.device_info["identifiers"]))
        _LOGGER.debug(f"Identified device ID: {device_id}")
        device_entry = device_registry.async_get_device({device_id}, {})
        
        # Update all entities belonging to this device
        entity_count = 0
        for entity_entry in entity_registry.entities.values():
            if entity_entry.device_id == device_entry.id:
                entity = self.hass.states.get(entity_entry.entity_id)
                if entity:
                    _LOGGER.debug(f"Updating entity: {entity_entry.entity_id}")
                    # Update entity data from device (will automatically trigger state update)
                    entity.async_schedule_update_ha_state(force_refresh=True)
                    entity_count += 1
        _LOGGER.debug(f"Update process completed. Total entities updated: {entity_count}")
        



class HisenseACRefreshTokenButton(ButtonEntity):
    def __init__(self, api, config_entry_id):
        self._api = api
        self._config_entry_id = config_entry_id
        self._attr_name = f"Refresh token"
        self._attr_unique_id = f"{api.device_id}_refresh_token"
        self._attr_icon = "mdi:refresh"

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._api.wifi_id[-12:])},
            "connections": {("mac", self._api.mac)},
            "name": "Hisense AC",
            "manufacturer": "Hisense",
        }

    @property
    def name(self):
        return "Refresh token"

    async def async_press(self):
        """Handle the button press."""
        _LOGGER.debug(f"Button pressed for entity: {self._attr_unique_id}")
        await self._api.refresh()
