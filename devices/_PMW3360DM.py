import utime, machine
import pyControl.hardware as _h
from devices.PMW3360DM_srom_0x04 import PROGMEM

def twos_comp(val, bits=16):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is
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
        SPIparams = {'baudrate': 1000_000, 'polarity': 1, 'phase': 1,
                     'bits': 8, 'firstbit': machine.SPI.MSB}
        if '1' in SPI_type:
            self.SPI = machine.SPI(1, **SPIparams)
            self.select = _h.Digital_output(pin='W7', inverted=True)

        elif '2' in SPI_type:
            self.SPI = machine.SPI(2, **SPIparams)
            self.select = _h.Digital_output(pin='W45', inverted=True)

        elif 'soft' in SPI_type.lower():
            self.SPI = machine.SoftSPI(baudrate=500000, polarity=1, phase=0, bits=8, firstbit=machine.SPI.MSB,
                                       sck=machine.Pin(id=SCK, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       mosi=machine.Pin(id=MO, mode=machine.Pin.OUT, pull=machine.Pin.PULL_DOWN),
                                       miso=machine.Pin(id=MI, mode=machine.Pin.IN))
            self.select = _h.Digital_output(pin=CS, inverted=True)

        self.motion = _h.Digital_input(pin=MT, falling_event=eventName, pull='up')
        self.reset = _h.Digital_output(pin=reset, inverted=True)

        self.select.off()
        self.reset.off()

    def read_pos(self):
        # write and read Motion register to lock the content of delta registers
        self.write_register(0x02, 0x01)
        self.read_register(0x02)

        delta_x_L = self.read_register(0x03)
        delta_x_H = self.read_register(0x04)
        delta_y_L = self.read_register(0x05)
        delta_y_H = self.read_register(0x06)

        delta_x = delta_x_H + delta_x_L
        delta_y = delta_y_H + delta_y_L

        delta_x = int.from_bytes(delta_x, 'big')
        delta_y = int.from_bytes(delta_y, 'big')

        delta_x = twos_comp(delta_x)
        delta_y = twos_comp(delta_y)

        return delta_x, delta_y

    def read_register(self, addrs: int):
        """
        addrs < 128
        """
        # ensure MSB=0
        addrs = addrs & 0x7f
        addrs = addrs.to_bytes(1, 'big')
        self.select.on()
        self.SPI.write(addrs)
        utime.sleep_us(100)  # tSRAD
        data = self.SPI.read(1)
        utime.sleep_us(1)  # tSCLK-NCS for read operation is 120ns
        self.select.off()
        utime.sleep_us(19)  # tSRW/tSRR (=20us) minus tSCLK-NCS
        return data

    def write_register(self, addrs: int, data: int):
        """
        addrs < 128
        """
        # flip the MSB to 1:
        addrs = addrs | 0x80
        addrs = addrs.to_bytes(1, 'big')
        data = data.to_bytes(1, 'big')
        self.select.on()
        self.SPI.write(addrs)
        self.SPI.write(data)
        utime.sleep_us(20)  # tSCLK-NCS for write operation
        self.select.off()
        utime.sleep_us(100)  # tSWW/tSWR (=120us) minus tSCLK-NCS. Could be shortened, but is looks like a safe lower bound

    def power_up(self):
        """
        Perform the power up sequence
        As per page 26 of datasheet
        """
        # 2
        self.select.off()
        self.select.on()
        self.select.off()
        # 3
        self.write_register(0x3a, 0x5a)
        # 4
        utime.sleep_ms(50)
        # 5
        self.read_pos()

        # SROM Download
        # As per page 23 of datasheet
        # 2
        self.write_register(0x10, 0x20)
        # 3
        self.write_register(0x13, 0x1d)
        # 4
        utime.sleep_ms(10)
        # 5
        self.write_register(0x13, 0x18)
        # 6
        self.download_srom(PROGMEM)
        # 7
        ID = int.from_bytes(self.read_register(0x2a), 'big')
        assert ID == 0x04, "bad SROM v={}".format(ID)
        # 8
        # Write 0x00 to Config2 register for wired mouse or 0x20 for wireless mouse design (Enable/Disable Rest mode)
        self.write_register(0x10, 0x00)

        # set initial CPI resolution
        self.write_register(0x0f, 0x77)  # CPI setting=12000

        self.select.off()

        utime.sleep_ms(10)

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
        utime.sleep_ms(60)
        self.read_pos()
        utime.sleep_ms(1)
        self.select.off()
        utime.sleep_ms(1)

    def download_srom(self, srom):
        self.select.on()
        # flip the MSB to 1:
        self.SPI.write((0x62 | 0x80) .to_bytes(1, 'big'))
        utime.sleep_us(15)
        for srom_byte in srom:
            self.SPI.write(srom_byte.to_bytes(1, 'big'))
            utime.sleep_us(15)

        self.select.off()

    def burst_read(self):
        """
        Based on Burst mode Page 22
        reads 12 bytes:
        BYTE[00] = Motion    = if the 7th bit is 1, a motion is detected.
            ==> 7 bit: MOT (1 when motion is detected)
            ==> 3 bit: 0 when chip is on surface / 1 when off surface
        BYTE[01] = Observation
        BYTE[02] = Delta_X_L = dx (LSB)
        BYTE[03] = Delta_X_H = dx (MSB)
        BYTE[04] = Delta_Y_L = dy (LSB)
        BYTE[05] = Delta_Y_H = dy (MSB)
        BYTE[06] = SQUAL     = Surface Quality register, max 0x80
                            - Number of features on the surface = SQUAL * 8
        BYTE[07] = Raw_Data_Sum   = It reports the upper byte of an 18‐bit counter which sums all 1296 raw data in the current frame;
                                * Avg value = Raw_Data_Sum * 1024 / 1296
        BYTE[08] = Maximum_Raw_Data  = Max raw data value in current frame, max=127
        BYTE[09] = Minimum_Raw_Data  = Min raw data value in current frame, max=127
        BYTE[10] = Shutter_Upper     = Shutter LSB
        BYTE[11] = Shutter_Lower     = Shutter MSB, Shutter = shutter is adjusted to keep the average raw data values within normal operating ranges
        """
        # 1
        self.write_register(0x50, 0x00)
        # 2
        self.select.on()
        # 3
        self.SPI.write(0x50 .to_bytes(1, 'big'))
        # 4
        utime.sleep_us(35)  # wait for tSRAD_MOTBR
        # 5
        data = self.SPI.read(6)
        # 6
        self.select.off()
        utime.sleep_us(2)

        delta_x = data[3] + data[2]
        delta_y = data[5] + data[4]

        delta_x = int.from_bytes(delta_x, 'big', True)
        delta_y = int.from_bytes(delta_y, 'big', True)

        return delta_x, delta_y
