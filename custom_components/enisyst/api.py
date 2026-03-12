"""enisyst API client with automatic WordPress cookie refresh."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from .const import (
    API_BASE,
    BASE_URL,
    COOKIE_REFRESH_INTERVAL_SECONDS,
    LOGIN_URL,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


class EnisystAuthError(Exception):
    """Raised when authentication fails."""


class EnisystApiError(Exception):
    """Raised when an API call fails."""


class EnisystApiClient:
    """Async HTTP client for eniserv.de with automatic cookie refresh."""

    def __init__(
        self,
        username: str,
        password: str,
        station_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._username = username
        self._password = password
        self._station_id = station_id
        self._session = session
        self._cookie_jar: aiohttp.CookieJar = aiohttp.CookieJar()
        self._last_login: float = 0.0
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def async_login(self) -> None:
        """Perform WordPress form login and store session cookies."""
        _LOGGER.debug("Logging in to eniserv.de as %s", self._username)

        # Step 1: GET login page to receive the test cookie
        headers = {"User-Agent": USER_AGENT}
        async with self._session.get(
            LOGIN_URL, headers=headers, allow_redirects=False
        ) as resp:
            pass  # cookie jar is updated automatically by aiohttp

        # Step 2: POST credentials
        payload = {
            "Accept": "text/html",
            "log": self._username,
            "pwd": self._password,
            "redirect_to": f"{BASE_URL}/wp-admin/",
            "rememberme": "forever",
            "submit": "Log In",
            "testcookie": "1",
        }
        async with self._session.post(
            LOGIN_URL,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
            allow_redirects=False,
        ) as resp:
            if resp.status not in (302, 200):
                raise EnisystAuthError(
                    f"Login failed with HTTP {resp.status}"
                )
            # Verify we actually got a wordpress_logged_in cookie
            cookies = {c.key: c.value for c in self._session.cookie_jar}
            logged_in = any(
                k.startswith("wordpress_logged_in") for k in cookies
            )
            if not logged_in:
                raise EnisystAuthError(
                    "Login did not return a valid WordPress session cookie."
                )

        self._last_login = time.monotonic()
        _LOGGER.debug("Login successful")

    async def async_ensure_authenticated(self) -> None:
        """Re-login if the cookie is expired or not yet obtained."""
        async with self._lock:
            age = time.monotonic() - self._last_login
            if age >= COOKIE_REFRESH_INTERVAL_SECONDS:
                await self.async_login()

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    async def async_get_chargepoints(self) -> list[dict[str, Any]]:
        """GET /enilyser/{station}/apiv4/objects/ls – list all chargers."""
        await self.async_ensure_authenticated()
        url = f"{API_BASE}/{self._station_id}/apiv4/objects/ls"
        return await self._get_json(url)

    async def async_get_assigned_chargepoints(self) -> list[dict[str, Any]]:
        """GET /enilyser/{station}/getassignedchargepoints."""
        await self.async_ensure_authenticated()
        url = (
            f"{API_BASE}/{self._station_id}/getassignedchargepoints"
            f"?reference={self._username}"
        )
        return await self._get_json(url)

    async def async_get_allowed_charging_modes(self) -> list[Any]:
        """GET /enilyser/{station}/getallowedchargingmodes."""
        await self.async_ensure_authenticated()
        url = (
            f"{API_BASE}/{self._station_id}/getallowedchargingmodes"
            f"?reference={self._username}"
        )
        return await self._get_json(url)

    async def async_check_park_manager(self) -> bool:
        """GET /enilyser/{station}/whitelist/checkIfChargingParkManager."""
        await self.async_ensure_authenticated()
        url = (
            f"{API_BASE}/{self._station_id}/whitelist/checkIfChargingParkManager"
            f"?reference={self._username}"
        )
        async with self._session.get(
            url, headers={"User-Agent": USER_AGENT}
        ) as resp:
            resp.raise_for_status()
            text = await resp.text()
            return text.strip().lower() == "true"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_json(self, url: str) -> Any:
        """Perform a GET request and return parsed JSON."""
        try:
            async with self._session.get(
                url, headers={"User-Agent": USER_AGENT}
            ) as resp:
                if resp.status == 401 or resp.status == 403:
                    # Force re-login on next call
                    self._last_login = 0.0
                    raise EnisystAuthError(
                        f"Received HTTP {resp.status} – will re-login on next poll"
                    )
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except aiohttp.ClientError as exc:
            raise EnisystApiError(f"API request to {url} failed: {exc}") from exc
