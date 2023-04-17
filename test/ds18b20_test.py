import time

from w1thermsensor import W1ThermSensor

sensor_ids = []

try:
    for sensor in W1ThermSensor.get_available_sensors():
        print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
        sensor_ids.append(sensor.id)
except Exception:
    print("no sensors found")

sensor = W1ThermSensor()

while True:
    for sid in sensor_ids:
        sensor = W1ThermSensor(sensor_id=sid)
        temperature = sensor.get_temperature()
        print(f"The temperature of {sid} is {temperature}°C")
        time.sleep(1)
