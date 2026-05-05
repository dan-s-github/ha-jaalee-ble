"""Constants for jaalee."""

from jaalee_ble import SensorModel

DOMAIN = "jaalee"

CONF_SENSOR_MODEL = "sensor_model"

SENSOR_MODEL_SHT20 = SensorModel.SHT20.value
SENSOR_MODEL_SHT31 = SensorModel.SHT31.value
DEFAULT_SENSOR_MODEL = SENSOR_MODEL_SHT20
SENSOR_MODELS: tuple[str, ...] = (SENSOR_MODEL_SHT20, SENSOR_MODEL_SHT31)
