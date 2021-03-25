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
          'trial_start',
          'odour_release',
          'reward',
          'penalty']

events = ['motion',
          'lick',
          'session_timer',
          'IT_duration_elapsed',
          'odour_duration_elapsed',
          'reward_duration_elapsed'
          ]

initial_state = 'intertrial'

# -------------------------------------------------------------------------
# Variables.
# -------------------------------------------------------------------------


# session params
v.session_duration = 1 * hour
v.reward_duration = 100 * ms
v.penalty_duration = 10 * second
v.trial_number = 0
v.delta_x = uarray.array('i')  # signed int minimm 2 bytes
v.delta_y = uarray.array('i')

# intertrial params
v.min_IT_movement = 10  # cm
v.min_IT_duration = 1 * second
v.IT_duration_done___ = False

# trial params
v.max_odour_time = 10 * second
v.max_odour_movement = 50  # cm
v.distance_to_target = 20  # cm
v.target_angle_tolerance = math.pi / 18  # deg_rad
v.odourant_direction = -1
v.air_off_duration = 100 * ms

# -------------------------------------------------------------------------
# Define behaviour.
# -------------------------------------------------------------------------


# Run start and stop behaviour.
def run_start():
    # Code here is executed when the framework starts running.
    set_timer('session_timer', v.session_duration, True)
    hw.motionSensor.power_up()
    hw.speaker.set_volume(90)
    hw.speaker.off()
    hw.odourDelivery.clean_air_on()


def run_end():
    # Code here is executed when the framework stops running.
    # Turn off all hardware outputs.
    hw.motionSensor.shut_down()
    hw.off()


# State behaviour functions.
def intertrial(event):
    if event == 'entry':
        # coded so that at this point, there is clean air coming from every direction
        set_timer('IT_duration_elapsed', v.min_IT_duration)
        v.IT_duration_done___ = False
    elif event == 'exit':
        disarm_timer('IT_duration_elapsed')
    elif event == 'lick':
        # TODO: handle the lick data better
        pass
    elif event == 'IT_duration_elapsed':
        v.IT_duration_done___ = True
        v.delta_x, v.delta_y = uarray.array('i'), uarray.array('i')
    elif event == 'motion':
        if v.IT_duration_done___:
            if math.sqrt((sum(v.delta_x)**2) + (sum(v.delta_x)**2)) >= v.min_IT_movement:
                goto_state('trial_start')


def trial_start(event):
    if event == 'entry':
        v.delta_x, v.delta_y = uarray.array('i'), uarray.array('i')
        v.trial_number += 1
        print('{}, trial_number'.format(v.trial_number))
        hw.odourDelivery.all_off()
        timed_goto_state('odour_release', v.air_off_duration)


def odour_release(event):
    if event == 'entry':
        set_timer('odour_duration_elapsed', v.max_odour_time)
        v.odourant_direction = init_odour.release_single_odourant_random(hw.odourDelivery)
        v.delta_x, v.delta_y = uarray.array('i'), uarray.array('i')
    elif event == 'exit':
        disarm_timer('odour_duration_elapsed')
    elif event == 'motion':
        D_x = sum(v.delta_x)
        D_y = sum(v.delta_y)
        arrived = init_odour.arrived_to_target(D_x, D_y,
                                               v.odourant_direction,
                                               v.distance_to_target,
                                               v.target_angle_tolerance)

        init_odour.audio_feedback(hw.speaker, D_x, D_y, v.odourant_direction)

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
        hw.odourDelivery.clean_air_on()
        set_timer('reward_duration_elapsed', v.reward_duration, False)
        hw.rewardSol.on()
        print('{}, reward_on'.format(get_current_time()))
    elif event == 'exit':
        disarm_timer('reward_duration_elapsed')
    elif event == 'reward_duration_elapsed':
        hw.rewardSol.off()
        goto_state('intertrial')


def penalty(event):
    if event == 'entry':
        hw.odourDelivery.clean_air_on()
        print('{}, penalty_on'.format(get_current_time()))
        timed_goto_state('intertrial', v.penalty_duration)


# State independent behaviour.
def all_states(event):
    # Code here will be executed when any event occurs,
    # irrespective of the state the machine is in.
    if event == 'motion':
        # read the motion registers and and append the variables
        delta_x, delta_y = hw.motionSensor.read_pos()
        print('{},{}, dM'.format(delta_x, delta_y))
        v.delta_x.append(delta_x)
        v.delta_y.append(delta_y)

    elif event == 'session_timer':
        stop_framework()
