from devices import *

board = Breakout_dseries_1_6()

# Instantiate Devices.

motionSensor = PMW3360DM(SPI_type='SPI2', eventName='',
                         reset=board.port_3.DIO_B, MT=board.port_3.DIO_C)

# in each direction, Odour0 is always the clean air, Odour1 is the odourant,...
odourDelivery = ParallelOdourRelease(5, 2,
                                     board.port_1.DIO_C, board.port_1.POW_A,    # Dir1
                                     board.port_1.POW_B, board.port_4.DIO_A,    # Dir2
                                     board.port_4.DIO_B, board.port_4.DIO_C,    # Dir3
                                     board.port_5.DIO_A, board.port_5.DIO_B,    # Dir4
                                     board.port_5.POW_A, board.port_5.POW_B)    # Dir5


lickometer = Lickometer(port=board.port_6, rising_event_A='lick', falling_event_A='lick_off',
                        rising_event_B='_lick_2___', falling_event_B='_lick_2_off___', debounce=5)


rewardSol = lickometer.SOL_1  # has two methods: on() and off()

speaker = Audio_board(board.port_7)
