import pyb, machine, utime
import pyControl.hardware as _h
from devices.PMW3360DM_srom_0x04 import PROGMEM


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

        delta_x = int.from_bytes(delta_x, 'big', True)
        delta_y = int.from_bytes(delta_y, 'big', True)

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

    def write_register(self, addrs: int, data: int):
        """
        addrs < 128
        """
        # flip the MSB to 1:
        addrs = addrs | 0b1000_0000
        addrs = addrs.to_bytes(1, 'big')
        data = data.to_bytes(1, 'big')
        self.select.on()
        self.SPI.write(addrs)
        self.SPI.write(data)
        utime.sleep_us(35)
        self.select.off()

    def power_up(self):
        """
        Perform the power up sequence
        As per page 26 of datasheet
        """
        # 2
        self.select.off()
        utime.sleep_ms(1)
        self.select.on()
        utime.sleep_ms(1)
        # 3
        self.reset.on()
        utime.sleep_ms(1)
        self.reset.off()
        # 4
        utime.sleep_ms(60)
        # 5
        self.read_pos()

        # SROM Download
        # As per page 23 of datasheet
        # 2
        val = self.read_register(0x10)
        val = int.from_bytes(self.read_register(0x10), 'big', True)
        self.write_register(0x10, val)
        utime.sleep_ms(1)
        # 3
        self.write_register(0x13, 0x1d)
        # 4
        utime.sleep_ms(15)
        # 5
        self.write_register(0x13, 0x18)
        # 6
        self.download_srom(PROGMEM)
        # 7
        ID = self.read_register(0x2a)
        utime.sleep_ms(1)
        # 8
        self.write_register(0x10, 0x00)

        print('{}, SROM ID, DONE!'.format(ID))  # Id must not equal zero

        self.write_register(2, 0)  # not sure about this line: write an arbitrary value to the motion register
        self.select.off()

    def shut_down(self):
        """
        Perform the shut down sequence
        As per page 27 of datasheet
        """
        self.select.off()
        utime.sleep_ms(1)
        self.select.on()
        utime.sleep_ms(1)
        self.reset.on()
        utime.sleep_ms(1)
        self.select.off()
        utime.sleep_ms(1)
        self.read_pos()
        utime.sleep_ms(1)

    def download_srom(self, srom):
        # flip the MSB to 1:
        addrs = 0x62
        addrs = addrs.to_bytes(1, 'big')

        self.SPI.write(addrs)
        for srom_byte in srom:
            self.SPI.write(srom_byte.to_bytes(1, 'big'))
            utime.sleep_us(20)

        utime.sleep_ms(1)
