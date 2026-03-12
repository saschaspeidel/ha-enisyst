"""DataUpdateCoordinator for enisyst Wallbox."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EnisystApiClient, EnisystApiError, EnisystAuthError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class EnisystCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the eniserv.de API and provides data to all sensors."""

    def __init__(self, hass: HomeAssistant, client: EnisystApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest charger list from the API."""
        try:
            chargepoints = await self.client.async_get_chargepoints()
        except EnisystAuthError as exc:
            _LOGGER.warning("Authentication issue, will retry: %s", exc)
            # Force re-login and try once more
            self.client._last_login = 0.0
            try:
                chargepoints = await self.client.async_get_chargepoints()
            except (EnisystAuthError, EnisystApiError) as retry_exc:
                raise UpdateFailed(f"enisyst auth error: {retry_exc}") from retry_exc
        except EnisystApiError as exc:
            raise UpdateFailed(f"enisyst API error: {exc}") from exc

        # Key by serialnumber for easy lookup
        return {cp["serialnumber"]: cp for cp in chargepoints if "serialnumber" in cp}
