import asyncio
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Hisense buttons from a config entry."""
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = [HisenseACUpdateButton(api[device_id], config_entry.entry_id) for device_id in api]
    async_add_entities(entities, True)
    entities = [HisenseACRefreshTokenButton(api[device_id], config_entry.entry_id) for device_id in api]
    async_add_entities(entities, True)


class HisenseACUpdateButton(ButtonEntity):
    """Button to force update all entities of the Hisense AC device."""

    def __init__(self, api, config_entry_id):
        """Initialize the button."""
        self._api = api
        self._config_entry_id = config_entry_id
        self._attr_name = f"Force update button"
        self._attr_unique_id = f"{api.device_id}_force_update_button"
        self._attr_icon = "mdi:refresh"

    @property
    def entity_category(self):
        """Return the entity category."""
        return EntityCategory.CONFIG

    @property
    def device_info(self):
        """Return device information about this Hisense AC."""
        return {
            "identifiers": {(DOMAIN, self._api.wifi_id[-12:])},
            "connections": {("mac", self._api.mac)},
            "name": "Hisense AC",
            "manufacturer": "Hisense",
        }

    @property
    def name(self):
        """Return the name of the button."""
        return "Force Update"

    async def async_press(self):
        """Handle the button press and notify all device entities to update."""
        _LOGGER.debug(f"Button pressed for entity: {self._attr_unique_id}")
        await self._api.check_status()
        
        try:
            # 获取设备和实体注册表
            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)
            
            # 获取设备ID
            device_identifiers = self.device_info.get("identifiers", set())
            if not device_identifiers:
                _LOGGER.error("No device identifiers found for entity")
                return
                
            domain, device_id = next(iter(device_identifiers))
            device_entry = device_registry.async_get_device({(domain, device_id)}, set())
            if not device_entry:
                _LOGGER.error(f"Device not found with identifier: {(domain, device_id)}")
                return
                
            # 获取设备下的所有实体
            entities_to_update = []
            for entity_entry in entity_registry.entities.values():
                if entity_entry.device_id == device_entry.id:
                    entities_to_update.append(entity_entry.entity_id)
                    
            _LOGGER.debug(f"Found {len(entities_to_update)} entities to update for device: {device_entry.id}")
            
            # 使用 Home Assistant 服务更新实体
            await asyncio.gather(*[
                self.hass.services.async_call(
                    "homeassistant", 
                    "update_entity", 
                    {"entity_id": entity_id},
                    blocking=True
                )
                for entity_id in entities_to_update
            ])
            
            _LOGGER.info(f"Successfully updated {len(entities_to_update)} entities")
            
        except Exception as e:
            _LOGGER.error(f"Error updating entities: {e}")


class HisenseACRefreshTokenButton(ButtonEntity):
    """Button to refresh the API token for the Hisense AC device."""

    def __init__(self, api, config_entry_id):
        """Initialize the button."""
        self._api = api
        self._config_entry_id = config_entry_id
        self._attr_name = f"Refresh token"
        self._attr_unique_id = f"{api.device_id}_refresh_token"
        self._attr_icon = "mdi:refresh"

    @property
    def entity_category(self):
        """Return the entity category."""
        return EntityCategory.CONFIG

    @property
    def device_info(self):
        """Return device information about this Hisense AC."""
        return {
            "identifiers": {(DOMAIN, self._api.wifi_id[-12:])},
            "connections": {("mac", self._api.mac)},
            "name": "Hisense AC",
            "manufacturer": "Hisense",
        }

    @property
    def name(self):
        """Return the name of the button."""
        return "Refresh token"

    async def async_press(self):
        """Handle the button press to refresh the API token."""
        _LOGGER.debug(f"Button pressed for entity: {self._attr_unique_id}")
        await self._api.refresh()