# PyTreadmillTask

from pyControl.utility import *
from devices import *
import math
import uarray

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial',
          'trial_start']
events = ['session_timer']

initial_state = 'intertrial'


# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------

# general parameters
v.rand_angle = uarray.array('d')

# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------

# Run start and stop behaviour.


def trial_start(event):
    if event == 'entry':
        if len(v.rand_angle) > 1:
            math.atan2(v.rand_angle[-1], 1)
            del v.rand_angle[-1]

            goto_state('trial_start2')
        else:
            print('endAtan')
            stop_framework()


def trial_start2(event):
    if event == 'entry':
        if len(v.rand_angle) > 1:
            math.atan2(v.rand_angle[-1], 1)
            del v.rand_angle[-1]

            goto_state('trial_start')
        else:
            print('endAtan')
            stop_framework()


def intertrial(event):
    if event == 'entry':
        set_timer('session_timer', 10, True)
        print('timeBeforeRand')
        for i in range(1000):
            v.rand_angle.append(random() * 6.28)

        print('timeAfterRandGeneration')
        goto_state('trial_start')


def all_states(event):
    if event == 'session_timer':
        stop_framework()
