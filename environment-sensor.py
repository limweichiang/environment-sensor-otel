# Import for general systems use
import argparse
import time
import logging
from pythonjsonlogger.json import JsonFormatter

# Import for creating and writing environmental metrics
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
    Gauge
)

# Import for Sensirion SCD41 Sensor
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection, CrcCalculator
from sensirion_driver_adapters.i2c_adapter.i2c_channel import I2cChannel
from sensirion_i2c_scd4x.device import Scd4xDevice

# Initialize Logger using JSON
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--i2c-port', default='/dev/i2c-1', help="Set Sensirion SCD41 i2c port. Default=/dev/i2c-1")
    parser.add_argument('--otlp-receiver-grpc', default='localhost:4317', help="Set OTLP gRPC receiver hostname and port. Default='localhost:4317'")
    parser.add_argument('--otlp-receiver-http', default='localhost:4318', help="Set OTLP HTTP receiver hostname and port. Default='localhost:4318'")
    parser.add_argument("--verbose", action="store_false", help="Enable debug/verbose logging. Default=false")
    args = parser.parse_args()

    # Log at DEBUG level if configured. 
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    
    '''
        metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
        provider = MeterProvider(metric_readers=[metric_reader])

        # Sets the global default meter provider
        metrics.set_meter_provider(provider)

        # Creates a meter from the global meter provider
        meter = metrics.get_meter("my.meter.name")


        env_temp_gauge = meter.create_gauge('environment.temperature', unit='Cel', description='Environmnent/Ambient Temperature in degrees Celsius')
    '''
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
            (co2_concentration, temperature, relative_humidity
            ) = sensor.read_measurement()

            #     Log results in physical units.
            logger.info({
                "co2_concentration": co2_concentration,
                "temperature": temperature,
                "relative_humidity": relative_humidity
            })


# Kick off main, if this is the entrypoint.
if __name__ == '__main__':
    main()
