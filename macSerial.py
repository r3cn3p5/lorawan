import sys
import time
import traceback

import serial
from serial.threaded import ReaderThread, LineReader


def write_read_command(ser, cmd, argument=None):
    line = 'AT+'
    line += cmd
    if argument is not None:
        line += '='
        line += argument

    print("write data: " + line)
    ser.write_line(line)
    #ser.write_line(line.encode("UTF-8"))
    #ser.write('\n'.encode("UTF-8"))

class PrintLines(LineReader):
    def connection_made(self, transport):
        super(PrintLines, self).connection_made(transport)
        sys.stdout.write('port opened\n')

    def handle_line(self, data):
        sys.stdout.write('line received: {}\n'.format(repr(data)))

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        sys.stdout.write('port closed\n')

ser = serial.Serial('/dev/cu.usbserial-A50285BI', 115200, timeout=1)

with ReaderThread(ser, PrintLines) as protocol:

    write_read_command(protocol, 'IREBOOT', '0')
    time.sleep(2)
    write_read_command(protocol, 'CGMI?')
    time.sleep(2)
    write_read_command(protocol, 'ILOGLVL', '5')
    time.sleep(2)
    write_read_command(protocol, 'CGMM?')
    time.sleep(2)
    write_read_command(protocol, 'CGMR?')

    time.sleep(10)

ser.close()
