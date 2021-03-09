# This is an example hardware definition for use with pyControl D-series breakout v1.6
# Nosepokes are plugged into ports 1-3, and a houselight is in port 4. 

from devices import *

board = Breakout_dseries_1_6()

# Instantiate Devices.

motionSensor = PMW3360DM(SPI_type='SPI2', eventName='motion',
                         reset=board.port_3.DIO_B, MT=board.port_3.DIO_C)

# in each direction, Odour0 is always the clean air, Odour1 is the odourant,...
odourDelivery = ParallelOdourRelease(5, 2,
                                     board.port_4.DIO_A, board.port_4.DIO_B,    # Dir1
                                     board.port_4.DIO_C, board.port_4.POW_A,    # Dir2
                                     board.port_4.POW_B, board.port_5.DIO_A,    # Dir3
                                     board.port_5.DIO_B, board.port_5.POW_A,    # Dir4
                                     board.port_3.POW_A, board.port_3.POW_B)    # Dir5


rewardSol = Digital_output(pin=board.port_5.POW_B, inverted=False, pulse_enabled=False)

lickometer = Lickometer(port=board.port_6, rising_event_A='lick', falling_event_A='_lick_off___',
                        rising_event_B='_lick_2___', falling_event_B='_lick_2_off___', debounce=5)
