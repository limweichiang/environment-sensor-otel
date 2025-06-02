# environment-sensor-otel
Personal Raspberry Pi Environmental Sensor, using OTel Collector.

# Environment - Development & Operational

This project is developed and will operate using with the following:
- Raspberry Pi 4B 8GB
- Ubuntu 24.04.2 LTS (aarch64)

# Setting Up

Configure the Raspberry Pi to enable I2c at the GPIO
```
~ $ sudo apt install raspi-config
~ $ sudo raspi-config
```
Select to **3 Interface Options**, then select **I2C**. When the GUI asks **Would you like the ARM I2C interface to be enabled?**, select **<Yes>**. If all goes well, you should see a **The ARM I2C interface is enabled**.

Download the latest code from this repository and cd into the directory.
```
~ $ git clone https://github.com/limweichiang/environment-sensor-otel.git
~ $ cd environment-sensor-otel
~/environment-sensor-otel $ 
```

Using a virtual environment is highly recommended. Create one and activate it.
```
~/environment-sensor-otel $ python3 -m venv .venv
~/environment-sensor-otel $ source .venv/bin/Activate
(.venv) ~/environment-sensor-otel $
```

Install the required dependencies.
```
(.venv) ~/environment-sensor-otel $ pip install -r requirements.txt
```

Install the OpenTelemetry Collector
```
Work in Progress
```

# Run Sensor Data Collection

See the following for runtime options and starting data collection.
```
(.venv) ~/environment-sensor-otel $ python3 environment-sensor.py --help
usage: environment-sensor.py [-h] [--i2c-port I2C_PORT] [--otlp-receiver-http OTLP_RECEIVER_HTTP] [--verbose]

options:
  -h, --help            show this help message and exit
  --i2c-port I2C_PORT   Set Sensirion SCD41 i2c port. Default=/dev/i2c-1
  --otlp-receiver-http OTLP_RECEIVER_HTTP
                        Set OTLP HTTP receiver, must use 'http://<hostname>:<port>' format. Default='http://localhost:4318'
  --verbose             Enable debug/verbose logging. Default=false
(.venv) ~/environment-sensor-otel $ python3 environment-sensor.py
```