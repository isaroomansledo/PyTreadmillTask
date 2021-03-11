# PyTreadmillTask

from pyControl.utility import *
import hardware_definition as hw
from devices import *
import math
import init_odour

# -------------------------------------------------------------------------
# States and events.
# -------------------------------------------------------------------------

states = ['intertrial',
          'trial_start',
          'odour_release',
          'reward',
          'penalty']

events = ['motion',
          'lick',
          'session_timer',
          'IT_duration_elapsed',
          'odour_duration_elapsed'
          ]

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------


# session params
v.session_duration = 5 * second  # 1 * hour
v.reward_duration = 100 * ms  
v.trial_number = 0
v.delta_x = []
v.delta_y = []

# intertrial params
v.min_IT_movement = 10  # cm
v.min_IT_duration = 1 * second
v.IT_duration_done___ = False

# trial params
v.odour_release_delay = 1  # second
v.max_odour_time = 10 * second
v.max_odour_movement = 50  # cm
v.distance_to_target = 20  # cm
v.target_angle_tolerance = math.pi / 18  # deg_rad
v.odourant_direction = -1

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
        v.delta_x, v.delta_y = [], []
        v.trial_number += 1
        print('{}, trial_number'.format(v.trial_number))
        odourDelivery.clean_air_on()
    elif event == 'motion':
        # TODO: implement the criteria
        odourDelivery.clean_air_on()


def odour_release(event):
    if event == 'entry':
        del v.delta_x[:-1]
        del v.delta_y[:-1]
        v.odourant_direction = init_odour.single_odourant_random(odourDelivery, v.odour_release_delay)
        set_timer('odour_duration_elapsed', v.max_odour_time)
    elif event == 'motion':
        arrived = init_odour.arrived_to_target(sum(v.delta_x), sum(v.delta_y),
                                               v.odourant_direction,
                                               v.distance_to_target,
                                               v.target_angle_tolerance)
        if arrived is None:
            pass
        elif arrived is True:
            goto_state('reward')
        elif arrived is False:
            goto_state('penalty')
    elif event == 'odour_duration_elapsed':
        goto_state('penalty')


def reward(event):
    if event == 'entry':
        disarm_timer('odour_duration_elapsed')
        set_timer('reward_duration', v.reward_duration, False)
        rewardSol.on()
    elif event == 'reward_duration':
        rewardSol.off()
        disarm_timer('reward_duration')
        goto_state('intertrial')


def penalty(event):
    if event == 'entry':
        disarm_timer('odour_duration_elapsed')
        set_timer('penalty_duration', v.reward_duration, False)
        # implement the penalty
    elif event == 'penalty_duration':
        disarm_timer('penalty_duration')
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
