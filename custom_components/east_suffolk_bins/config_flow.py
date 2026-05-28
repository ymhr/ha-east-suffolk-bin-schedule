"""Config flow for East Suffolk Bins."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import CONF_UPRN, DOMAIN
from .coordinator import _fetch_raw

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_UPRN): str,
})


async def _validate_uprn(hass: HomeAssistant, uprn: str) -> str | None:
    """Return an error key, or None if valid."""
    try:
        await hass.async_add_executor_job(_fetch_raw, uprn, 28)
    except Exception:
        return "cannot_connect"
    return None


class EastSuffolkBinsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            uprn = user_input[CONF_UPRN].strip()
            await self.async_set_unique_id(uprn)
            self._abort_if_unique_id_configured()

            error = await _validate_uprn(self.hass, uprn)
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=f"UPRN {uprn}",
                    data={CONF_UPRN: uprn},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
