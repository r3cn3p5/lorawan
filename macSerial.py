import serial


def write_read_command(ser, cmd, argument=None):
    line = 'AT+'
    line += cmd
    if argument is not None:
        line += '='
        line += argument

    print("write data: " + line)
    ser.write(line.encode("UTF-8"))
    ser.write('\n'.encode("UTF-8"))

    response = ser.readline()
    print("read data: " + response.decode("utf-8"))


ser = serial.Serial('/dev/cu.usbserial-A50285BI', 115200, timeout=1)

write_read_command(ser, "")
write_read_command(ser, 'IREBOOT', '0')
write_read_command(ser, 'CGMI?')
write_read_command(ser, 'ILOGLVL', '0')
write_read_command(ser, 'CGMM?')
write_read_command(ser, 'CGMR?')

ser.close()
