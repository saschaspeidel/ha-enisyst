# enisyst Wallbox Integration for Home Assistant (unoffical)
![logo](https://github.com/saschaspeidel/ha-enisyst/raw/main/logo.png)

> [!IMPORTANT]
> __Please note__, _that this integration is __not official__, nor is it supported by enisyst. I (saschaspeidel) am not affiliated with enisyst in any way. This integration is based on the eni.charge app and some reverse engineering_.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

This custom integration connects Home Assistant to **enisyst** wallbox charging stations managed via [eniserv.de](https://eniserv.de).

## Features

- Automatic discovery of all assigned charging points for a given station ID
- Live sensor data for each charger (status, power, current, energy, mode, etc.)
- Background cookie refresh for the WordPress-based login
- Config Flow UI setup

## Installation via HACS

1. Open HACS → Integrations → ⋮ → Custom Repositories
2. Add your GitHub repository URL and select category **Integration**
3. Install **enisyst Wallbox**
4. Restart Home Assistant

## Manual Installation

Copy the `custom_components/enisyst` folder into your HA `config/custom_components/` directory and restart.

## Configuration

Go to **Settings → Devices & Services → Add Integration** and search for **enisyst**.

You will need:
- **Username** (your eniserv.de login e-mail)
- **Password**
- **Station ID** (e.g. `B827EB5AF619`)

## Sensors per Charger

| Sensor | Unit | Description |
|---|---|---|
| Status | – | OCPP status (A=free, B=occupied, C=charging, …) |
| Status Text | – | Human-readable status |
| Power | W | Current charging power |
| Current | A | Assigned charging current |
| Max Current | A | Maximum allowed current |
| Charged Energy | Wh | Energy charged in current session |
| Charging Time | s | Duration of current session |
| Mode | – | Charging mode (normal, …) |
| Enabled | – | Whether the charger is enabled |
| OCPP Connected | – | OCPP connection state |
| Modbus Connected | – | Modbus connection state |
| Firmware | – | Charger firmware version |

## Cookie Refresh

The WordPress session cookie is automatically renewed every **20 hours** in the background. No manual re-authentication needed.
