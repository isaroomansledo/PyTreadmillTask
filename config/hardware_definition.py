# This is an example hardware definition for use with pyControl D-series breakout v1.6
# Nosepokes are plugged into ports 1-3, and a houselight is in port 4. 

from devices import *
from pyb import LED

board = Breakout_dseries_1_6()

# Instantiate Devices.

# motionSensor = PMW3360DM(SPI_type='SPI2', eventName='motion',
#                          reset=board.port_3.DIO_B, MT=board.port_3.DIO_C)

motionSensor = MotionDetector(name='test', sampling_rate=5000, reset=board.port_3.DIO_B, event='motion')
