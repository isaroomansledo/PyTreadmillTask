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
          ]

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------


# session params
v.session_duration = 5 * second  # 1 * hour

# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------


# Run start and stop behaviour.
def run_start():
    # Code here is executed when the framework starts running.
    set_timer('session_timer', v.session_duration, True)


def run_end():
    # Code here is executed when the framework stops running.
    # Turn off all hardware outputs.
    hw.off()


# State behaviour functions.
def intertrial(event):
    if event == 'entry':
        set_timer('IT_duration_elapsed', v.min_IT_duration)
    elif event == 'lick':
        # TODO: handle the lick data better
        pass
    elif event == 'IT_duration_elapsed':
        v.IT_duration_done___ = True
    elif event == 'motion':
        if v.IT_duration_done___:
            if math.sqrt((sum(v.delta_x)**2) + (sum(v.delta_x)**2)) >= v.min_IT_movement:
                v.IT_duration_done___ = False
                goto_state('trial_start')


def trial_start(event):
    if event == 'entry':
        disarm_timer('IT_duration_elapsed')
        v.delta_x, v.delta_y = uarray.array('i'), uarray.array('i')
        v.trial_number += 1
        print('{}, trial_number'.format(v.trial_number))
        odourDelivery.clean_air_on()
    elif event == 'motion':
        # TODO: implement the criteria
        odourDelivery.clean_air_on()



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
