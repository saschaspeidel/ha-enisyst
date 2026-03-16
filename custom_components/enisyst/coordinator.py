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

# Number of consecutive failures before entities go unavailable.
# At 30s poll interval this means ~2.5 minutes of tolerance.
FAILURE_TOLERANCE = 5


class EnisystCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the eniserv.de API and provides data to all sensors.

    Consecutive failures are counted. Only after FAILURE_TOLERANCE
    consecutive failed polls is UpdateFailed raised, which causes HA
    to mark entities as unavailable. During the tolerance window the
    last known good data is silently kept.
    """

    def __init__(self, hass: HomeAssistant, client: EnisystApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        # Counts consecutive failed API calls
        self._failure_count: int = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest charger data, tolerating short API outages."""
        try:
            chargepoints = await self._fetch_with_auth_retry()
        except (EnisystAuthError, EnisystApiError) as exc:
            self._failure_count += 1
            _LOGGER.warning(
                "enisyst API call failed (attempt %d/%d): %s",
                self._failure_count,
                FAILURE_TOLERANCE,
                exc,
            )
            if self._failure_count >= FAILURE_TOLERANCE:
                # Exceeded tolerance – let HA mark entities unavailable
                raise UpdateFailed(
                    f"enisyst API unreachable after {self._failure_count} attempts: {exc}"
                ) from exc

            # Return last known good data so entities stay available
            if self.data:
                _LOGGER.debug("Returning cached data during outage window")
                return self.data

            # No cached data yet (e.g. first poll) – must raise
            raise UpdateFailed(f"enisyst API error on first poll: {exc}") from exc

        # Successful call – reset failure counter
        self._failure_count = 0
        return {cp["serialnumber"]: cp for cp in chargepoints if "serialnumber" in cp}

    async def _fetch_with_auth_retry(self) -> list[dict[str, Any]]:
        """Attempt API fetch; on auth error re-login once and retry."""
        try:
            return await self.client.async_get_chargepoints()
        except EnisystAuthError:
            _LOGGER.warning("Session expired – re-logging in")
            self.client._last_login = 0.0
            await self.client.async_login()
            return await self.client.async_get_chargepoints()