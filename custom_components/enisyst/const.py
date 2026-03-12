"""Constants for the enisyst Wallbox integration."""

DOMAIN = "enisyst"

BASE_URL = "https://eniserv.de"
LOGIN_URL = f"{BASE_URL}/login/"
API_BASE = f"{BASE_URL}/enilyser"

CONF_STATION_ID = "station_id"

# How often to poll charger data (seconds)
SCAN_INTERVAL_SECONDS = 30

# Cookie re-login interval (seconds) – 20 hours
COOKIE_REFRESH_INTERVAL_SECONDS = 20 * 3600

USER_AGENT = "HomeAssistant/enisyst-integration/1.0"
