# PyTreadmillTask

from pyControl.utility import *
import hardware_definition as hw
from devices import *
import math
import uarray
import init_odour

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial',
          'trial_start']

events = ['motion',
          'session_timer',
          'IT_duration_elapsed'
          ]

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------


# session params
v.session_duration = 30 * second  # 1 * hour
v.min_IT_duration = 1 * second
v.delta_x = uarray.array('i')  # signed int minimm 2 bytes
v.delta_y = uarray.array('i')
# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------


# Run start and stop behaviour.
def run_start():
    # Code here is executed when the framework starts running.
    set_timer('session_timer', v.session_duration, True)

    motionSensor.power_up()


def run_end():
    # Code here is executed when the framework stops running.
    # Turn off all hardware outputs.
    hw.off()


# State behaviour functions.
def intertrial(event):
    if event == 'entry':
        set_timer('IT_duration_elapsed', v.min_IT_duration)
        led.on()
    elif event == 'IT_duration_elapsed':
        v.IT_duration_done___ = True
    elif event == 'motion':
        if v.IT_duration_done___:
            led.off()
            goto_state('trial_start')


def trial_start(event):
    if event == 'entry':
        disarm_timer('IT_duration_elapsed')
        led2.on()
    elif event == 'motion':
        led2.off()
        goto_state('intertrial')


# State independent behaviour.
def all_states(event):
    # Code here will be executed when any event occurs,
    # irrespective of the state the machine is in.
    if event == 'motion':
        # read the motion registers and and append the variables
        delta_x, delta_y = hw.motionSensor.read_pos()
        v.delta_x.append(delta_x)
        v.delta_y.append(delta_y)

        print('{},{}'.format(v.delta_x[-1], v.delta_y[-1]))

    elif event == 'session_timer':
        stop_framework()
