import time

import numpy as np
import scipy.io as sio
import serial

SIG_FS = 1000  # Hz

t = 0

subject = sio.loadmat("U02.mat", simplify_cells=True)
subject = subject[list(subject.keys())[-1]]
ppg = -subject["sx"].astype("float32")
print(len(ppg))

ser = serial.Serial("/dev/ttyUSB1", 230400)  # change tty to COM on Windows

sig = ser.read(1).decode("ascii")
print(sig)
time.sleep(0.1)

if sig == "=":
    while True:
        if ser.in_waiting > 0:
            sig = ser.read(1).decode("ascii")
            print(sig)
            if sig == ":":
                break
        data = np.zeros(shape=(5, 1), dtype="float32")
        for i in range(5):
            data[i, 0] = ppg[t]
            t += 1

        ser.write(data.astype("float32").tobytes())
        time.sleep(5.0 / SIG_FS)

print(t)

time.sleep(0.2)
ser.reset_input_buffer()
ser.reset_output_buffer()
time.sleep(0.2)
ser.close()
