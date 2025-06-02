# Import for general systems use
import argparse
import time
import logging
import sys
from pythonjsonlogger.json import JsonFormatter

# Import for creating and writing environmental metrics
from opentelemetry import metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# Import for Sensirion SCD41 Sensor
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection, CrcCalculator
from sensirion_driver_adapters.i2c_adapter.i2c_channel import I2cChannel
from sensirion_i2c_scd4x.device import Scd4xDevice

# Initialize Logger to use JSON
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = JsonFormatter(
    "{asctime}{message}", 
    style="{",
    rename_fields={"asctime": "timestamp"}
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--i2c-port', default='/dev/i2c-1', help="Set Sensirion SCD41 i2c port. Default=/dev/i2c-1")
    # Note: 
    parser.add_argument('--otlp-receiver-http', default='http://localhost:4318', help="Set OTLP HTTP receiver, must use 'http://<hostname>:<port>' format. Default='http://localhost:4318'")
    # Note: For --verbose, action="store_true" behaves in an unintuitive way. The default is "false", and will store "true" if the --verbose flag is used.
    parser.add_argument("--verbose", action="store_true", help="Enable debug/verbose logging. Default=false")
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Log at DEBUG level if configured. 
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Take either the default or specified OTLP receiver/endpoint
    if args.otlp_receiver_http:
        oltp_receiver_http = args.otlp_receiver_http
        logger.debug("OTLP HTTP endpoint set as " + oltp_receiver_http)
    else:
        logger.error("Critical parameter OTLP Reciver HTTP value was not provided.")
        sys.exit(-1)

    # Take either the default or specified I2C port to access the SCD41
    if args.i2c_port:
        i2c_port = args.i2c_port
        logger.debug("I2C device set as " + i2c_port)
    else:
        logger.error("Critical parameter I2C Port value was not provided.")
        sys.exit(-1)

    # Service name is required for most backends
    resource = Resource.create(attributes={SERVICE_NAME: "environment-sensor"})

    # Initialize Metric reader to send to OTLP receiver/endpoint
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=oltp_receiver_http + "/v1/metrics"))
    metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

    # Sets the global default meter provider
    metrics.set_meter_provider(metric_provider)

    # Creates a meter from the global meter provider
    meter = metrics.get_meter(__name__)

    # Set up the metrics and types for collection.
    env_co2_concentration_gauge = meter.create_gauge(
        name='environment.co2_concentration',
        unit='ppm',
        description='Environment CO2 gas concentration in ppm'
    )
    env_temperature_gauge = meter.create_gauge(
        name='environment.temperature',
        unit='Cel',
        description='Environment/Ambient Temperature in degrees Celsius'
    )
    env_relative_humidity_gauge = meter.create_gauge(
        name='environment.relative_humidity',
        unit='%',
        description='Environment/Ambient Relative Humidity in %'
    )

    # Initialize the CO2 sensor and loop data collection and transmission.
    with LinuxI2cTransceiver(args.i2c_port) as i2c_transceiver:
        channel = I2cChannel(I2cConnection(i2c_transceiver),
                            slave_address=0x62,
                            crc=CrcCalculator(8, 0x31, 0xff, 0x0))
        sensor = Scd4xDevice(channel)
        time.sleep(0.03)

        # Ensure sensor is in clean state
        sensor.wake_up()
        sensor.stop_periodic_measurement()
        sensor.reinit()

        # Read out information about the sensor
        serial_number = sensor.get_serial_number()
        logger.debug({"serial_number": serial_number})

        #     If temperature offset and/or sensor altitude compensation
        #     is required, you should call the respective functions here.
        #     Check out the header file for the function definitions.

        # Start periodic measurements (5sec interval)
        sensor.start_periodic_measurement()

        #     If low-power mode is required, switch to the low power
        #     measurement function instead of the standard measurement
        #     function above. Check out the header file for the definition.
        #     For SCD41, you can also check out the single shot measurement example.
        while (1):

            #     Slow down the sampling to 0.2Hz.
            time.sleep(5.0)
            data_ready = sensor.get_data_ready_status()
            while not data_ready:
                time.sleep(0.1)
                data_ready = sensor.get_data_ready_status()

            #     If ambient pressure compenstation during measurement
            #     is required, you should call the respective functions here.
            #     Check out the header file for the function definition.
            (co2_concentration, temperature, relative_humidity) = sensor.read_measurement()

            # Log results units.
            logger.info({
                "message": "Result collected.",
                "co2_concentration": co2_concentration,
                "temperature": temperature,
                "relative_humidity": relative_humidity
            })

            # Collect results as OTel metrics.
            env_co2_concentration_gauge.set(float(str(co2_concentration)))
            env_temperature_gauge.set(float(str(temperature)))
            env_relative_humidity_gauge.set(float(str(relative_humidity)))


# Kick off main, if this is the entrypoint.
if __name__ == '__main__':
    main()
