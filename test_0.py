import machine

from machine import I2C, Pin
import time
import struct
time.sleep(4)
print("Huhun")


from micropython import const

# Converts an int value into a 2 digits str
# Examples : 9 => "09", 14 => "14"
def make2digitsStr(intValue):
    baseStr = "0"
    if intValue > 9:
        baseStr = str(intValue)
    else:
        baseStr += str(intValue)

    return baseStr


DATETIME_REG = const(0) # 0x00-0x06
CHIP_HALT    = const(128)
CONTROL_REG  = const(7) # 0x07
RAM_REG      = const(8) # 0x08-0x3F

class DS1307(object):
    """Driver for the DS1307 RTC."""
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.weekday_start = 1
        self._halt = False

    def _dec2bcd(self, value):
        """Convert decimal to binary coded decimal (BCD) format"""
        return (value // 10) << 4 | (value % 10)

    def _bcd2dec(self, value):
        """Convert binary coded decimal (BCD) format to decimal"""
        return ((value >> 4) * 10) + (value & 0x0F)

    def datetime(self, datetime=None):
        """Get or set datetime"""
        if datetime is None:
            buf = self.i2c.readfrom_mem(self.addr, DATETIME_REG, 7)
            return (
                self._bcd2dec(buf[6]) + 2000, # year
                self._bcd2dec(buf[5]), # month
                self._bcd2dec(buf[4]), # day
                self._bcd2dec(buf[3] - self.weekday_start), # weekday
                self._bcd2dec(buf[2]), # hour
                self._bcd2dec(buf[1]), # minute
                self._bcd2dec(buf[0] & 0x7F), # second
                0 # subseconds
            )
        buf = bytearray(7)
        buf[0] = self._dec2bcd(datetime[6]) & 0x7F # second, msb = CH, 1=halt, 0=go
        buf[1] = self._dec2bcd(datetime[5]) # minute
        buf[2] = self._dec2bcd(datetime[4]) # hour
        buf[3] = self._dec2bcd(datetime[3] + self.weekday_start) # weekday
        buf[4] = self._dec2bcd(datetime[2]) # day
        buf[5] = self._dec2bcd(datetime[1]) # month
        buf[6] = self._dec2bcd(datetime[0] - 2000) # year
        if (self._halt):
            buf[0] |= (1 << 7)
        self.i2c.writeto_mem(self.addr, DATETIME_REG, buf)

    def halt(self, val=None):
        """Power up, power down or check status"""
        if val is None:
            return self._halt
        reg = self.i2c.readfrom_mem(self.addr, DATETIME_REG, 1)[0]
        if val:
            reg |= CHIP_HALT
        else:
            reg &= ~CHIP_HALT
        self._halt = bool(val)
        self.i2c.writeto_mem(self.addr, DATETIME_REG, bytearray([reg]))

    def square_wave(self, sqw=0, out=0):
        """Output square wave on pin SQ at 1Hz, 4.096kHz, 8.192kHz or 32.768kHz,
        or disable the oscillator and output logic level high/low."""
        rs0 = 1 if sqw == 4 or sqw == 32 else 0
        rs1 = 1 if sqw == 8 or sqw == 32 else 0
        out = 1 if out > 0 else 0
        sqw = 1 if sqw > 0 else 0
        reg = rs0 | rs1 << 1 | sqw << 4 | out << 7
        self.i2c.writeto_mem(self.addr, CONTROL_REG, bytearray([reg]))
    
    # Returns a the date and time in a string formatted like so : DD/MM/YYYY HH:MM
    
    def formattedDateTimeStr(self):
        now = self.datetime()
        formattedDateTime = make2digitsStr(now[2])+"/"+make2digitsStr(now[1])+"/"+str(now[0])+" "+make2digitsStr(now[4])+":"+make2digitsStr(now[5])

        return formattedDateTime
    

i2c = I2C(freq=400000, scl=machine.Pin(22), sda=machine.Pin(21))
                                # depending on the port, extra parameters may be required
                                # to select the peripheral and/or pins to use

res = i2c.scan()                      # scan for slaves, returning a list of 7-bit addresses
print(res)

ds = DS1307(i2c)
# Enable oscillator
#ds.halt(False)

# set the datetime 14th August Weekday 5 (Friday) 2020 at 11:27:00 PM 0 subseconds
#now = (2020, 8, 14, 5, 11, 27, 0, 0)
#ds.datetime(now)

#while True:
print(ds.formattedDateTimeStr())

uart = machine.UART(1, 9600)

uart.init(9600, bits=8, parity=None, stop=1, rx=5, tx=4)
print("Done uart init")
uart.write("F-PHDF")
while True:
    print(uart.read())