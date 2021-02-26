from re import MULTILINE
from typing import Match
import pyb, machine
import pyControl.hardware as _h


class PMW3360DM():
    # mouse motion sensor.
    def __init__(self,
                 SPI_type: str,
                 eventName: str,
                 reset: _h.DigitalOutput,
                 MT: _h.DigitalInput,
                 MI=None: _h.DigitalInput,
                 MO=None: _h.DigitalOutput,
                 CS=None: _h.DigitalOutput,
                 SCK=None: _h.DigitalOutput):

        # SPI_type = 'SPI0' or 'SPI1' or 'softSPI'
        if '0' in SPI_type:
            self.SPI = machine.SPI(id=0)
        elif '1' in SPI_type:
            self.SPI = machine.SPI(id=1)
        elif 'soft' in SPI_type.lower():
            self.SPI = machine.SoftSPI(baudrate= 500000, sck= SCK, mosi= MO, miso= MI)
        
        self.motion = MT
        self.reset = reset
        self.select = CS
