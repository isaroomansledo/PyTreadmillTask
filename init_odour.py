from pyControl.utility import *
import math


def release_single_odourant_random(odourDevice: ParallelOdourRelease):
    """
    Releases 1 odourant at a random direction
    """
    stimDir = randint(0, odourDevice.Ndirections - 1)
    odourDevice.all_off()
    odourDevice.odour_release(stimDir)

    print('{}, odourant_direction'.format(stimDir))

    return stimDir


_pi = math.pi
_target_angle = {0: 5 * _pi / 6,
                 1: 2 * _pi / 3,
                 2: _pi / 2,
                 3: _pi / 3,
                 4: _pi / 6}
_audio_freq_range = (10000, 20000)  # between 10kHz and 20kHz, loosely based on Heffner & Heffner 2007


def arrived_to_target(dX: float, dY: float,
                      odourant_direction: int,
                      distance_to_target: float,
                      target_angle_tolerance: float):
    """
    checks the motion critereon
    MUST have 5 odour directions
    """
    assert odourant_direction < 5, 'wrong direction value'

    movement = math.sqrt(dX**2 + dY**2)
    if movement < distance_to_target:
        return None

    else:
        move_angle = math.atan2(dY, dX)
        if abs(move_angle - _target_angle[odourant_direction]) < target_angle_tolerance:
            return True
        else:
            return False


def audio_mapping(d_a: float) -> float:
    """
    freq = (-10kHz/300)d_a + 15kHz
    """
    return mean(_audio_freq_range) - (_audio_freq_range[0] * d_a / _target_angle[0] * 2)


def audio_feedback(speaker,
                   dX: float, dY: float,
                   odourant_direction: int):
    angle = math.atan2(dY, dX)
    audio_freq = audio_mapping(angle - _target_angle[odourant_direction])
    speaker.sine(audio_freq)
