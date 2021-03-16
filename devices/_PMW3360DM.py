import pyb, machine, utime
import pyControl.hardware as _h
import PMW3360DM_srom_0x04 as srom


class PMW3360DM():
    # mouse motion sensor.
    def __init__(self,
                 SPI_type: str,
                 eventName: str,
                 reset: str,
                 MT: str,
                 CS: str = None,
                 MI: str = None,
                 MO: str = None,
                 SCK: str = None):

        # SPI_type = 'SPI1' or 'SPI2' or 'softSPI'
        SPIparams = {'baudrate': 1000_000, 'polarity': 1, 'phase': 0,
                     'bits': 8, 'firstbit': machine.SPI.MSB}
        if '1' in SPI_type:
            self.SPI = machine.SPI(id=0, **SPIparams)
            self.select = _h.Digital_output(pin='W7', inverted=True)

        elif '2' in SPI_type:
            self.SPI = machine.SPI(id=1, **SPIparams)
            self.select = _h.Digital_output(pin='W45', inverted=True)

        elif 'soft' in SPI_type.lower():
            self.SPI = machine.SoftSPI(baudrate=500000, polarity=1, phase=0, bits=8, firstbit=machine.SPI.MSB,
                                       sck=machine.Pin(id=SCK, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       mosi=machine.Pin(id=MO, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       miso=machine.Pin(id=MI, mode=machine.Pin.IN))
            self.select = _h.Digital_output(pin=CS, inverted=True)

        self.motion = _h.Digital_input(pin=MT, falling_event=eventName)
        self.reset = _h.Digital_output(pin=reset, inverted=True)

    def read_pos(self):
        # read Motion register to lock the content of delta registers
        self.read_register(2)

        delta_x_L = self.read_register(3)
        delta_x_H = self.read_register(4)
        delta_y_L = self.read_register(5)
        delta_y_H = self.read_register(6)

        delta_x = delta_x_H + delta_x_L
        delta_y = delta_y_H + delta_y_L

        delta_x = int.from_bytes(delta_x, 'big', signed=True)
        delta_y = int.from_bytes(delta_y, 'big', signed=True)

        return delta_x, delta_y

    def read_register(self, addrs: int):
        """
        addrs < 128
        """
        addrs = addrs.to_bytes(1, 'big')
        self.select.on()
        self.SPI.write(addrs)
        data = self.SPI.read(1)
        self.select.off()
        utime.sleep_us(20)
        return data

    def write_register(self, addrs: bytes, data: bytes):
        """
        addrs < 128
        """
        # flip the MSB to 1:
        addrs = addrs | 0b1000_0000
        addrs = addrs.to_bytes(1, 'big')
        self.select.on()
        self.SPI.write(addrs)
        self.SPI.write(data)
        utime.sleep_us(35)
        self.select.off()
