"""Constants for the Cooking BLE integration."""

from datetime import timedelta

DOMAIN = "cooking_ble"

CONF_MODEL = "model"
MODEL_H5055A = "h5055a"
MODEL_ANOVA = "anova"

# Govee H5055A: passive advertisements.
H5055A_MANUFACTURER_ID = 0x0930
H5055A_SERVICE_UUID = "00005550-0000-1000-8000-00805f9b34fb"
SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"

# Anova Precision Cooker (classic Bluetooth model): polled over GATT.
ANOVA_LOCAL_NAME = "Anova"
ANOVA_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
UPDATE_INTERVAL = timedelta(seconds=30)
