# PyTreadmillTask

from pyControl.utility import *
import hardware_definition as hw
from devices import *
import math
import uarray

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial']

events = ['motion',
          'session_timer']

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------

# session params
v.session_duration = 10 * second
v.motion_timer___ = 1 * ms  # polls motion every 1ms
v.motionBuffer = bytearray(4)
v.motionBuffer_mv = memoryview(v.motionBuffer)
v.delta_x_L_mv = v.motionBuffer_mv[1:2]
v.delta_x_H_mv = v.motionBuffer_mv[0:1]
v.delta_y_L_mv = v.motionBuffer_mv[3:]
v.delta_y_H_mv = v.motionBuffer_mv[2:3]
v.delta_x_mv = v.motionBuffer_mv[0:2]
v.delta_y_mv = v.motionBuffer_mv[2:]



def read_sensor(sensor):
    sensor.write_register_buff(b'\x02', b'\x81')
    sensor.read_register_buff(b'\x02', v.delta_x_L_mv)

    sensor.read_register_buff(b'\x03', v.delta_x_L_mv)
    sensor.read_register_buff(b'\x04', v.delta_x_H_mv)
    sensor.read_register_buff(b'\x05', v.delta_y_L_mv)
    sensor.read_register_buff(b'\x06', v.delta_y_H_mv)



# Run start and stop behaviour.
def run_start():
    # Code here is executed when the framework starts running.
    set_timer('session_timer', v.session_duration, True)
    hw.motionSensor.power_up()
    # set_timer('motion', v.motion_timer___)


def run_end():
    # Code here is executed when the framework stops running.
    # Turn off all hardware outputs.
    # hw.motionSensor.stop()
    hw.off()


# State behaviour functions.
def intertrial(event):
    if event == 'motion':
        print('mo')


# State independent behaviour.
def all_states(event):
    # Code here will be executed when any event occurs,
    # irrespective of the state the machine is in.
    if event == 'motion':
        # read the motion registers and and append the variables
        # read_sensor(hw.motionSensor)
        print('{}, dM'.format(hw.motionSensor.delta))
        # set_timer('motion', v.motion_timer___)

    elif event == 'session_timer':
        stop_framework()
