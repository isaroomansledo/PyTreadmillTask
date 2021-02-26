import pyb, machine
import pyControl.hardware as _h


class PMW3360DM():
    # mouse motion sensor.
    def __init__(self,
                 SPI_type: str,
                 eventName: str,
                 reset: str,
                 MT: str,
                 CS: str,
                 MI: str = None,
                 MO: str = None,
                 SCK: str = None):

        # SPI_type = 'SPI1' or 'SPI2' or 'softSPI'
        SPIparams = {'baudrate': 1000_000, 'polarity': 0, 'phase': 0,
                     'bits': 8, 'firstbit': machine.SPI.MSB}
        if '1' in SPI_type:
            self.SPI = machine.SPI(id=0, **SPIparams)
        elif '2' in SPI_type:
            self.SPI = machine.SPI(id=1, **SPIparams)
        elif 'soft' in SPI_type.lower():
            self.SPI = machine.SoftSPI(baudrate=500000,
                                       sck=machine.Pin(id=SCK, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       mosi=machine.Pin(id=MO, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       miso=machine.Pin(id=MI, mode=machine.Pin.IN))

        self.motion = _h.Digital_input(pin=MT, falling_event=eventName)
        self.reset = _h.Digital_output(pin=reset)
        self.select = _h.Digital_output(pin=CS)
