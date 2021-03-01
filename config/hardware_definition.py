# This is an example hardware definition for use with pyControl D-series breakout v1.6
# Nosepokes are plugged into ports 1-3, and a houselight is in port 4. 

from devices import *
import pyControl.hardware as _h

board = Breakout_dseries_1_6()

# Instantiate Devices.

motionSensor = PMW3360DM(SPI_type='SPI2', eventName='motion', reset='W43', MT='W24')

odour = ParallelSolDriver()
