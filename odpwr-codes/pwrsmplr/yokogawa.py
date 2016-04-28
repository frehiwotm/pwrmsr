#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2016 Markus Haehnel (based on Christoph M.'s script)
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


import serial
import datetime
import os
import argparse as ags


class reg_status_mask: # status register mask
    EAV = 0x04  # error available
    ESS = 0x08  # extended event summary bit
    MAV = 0x10  # message available
    ESB = 0x20  # event summary bit
    RQS = 0x40  # request status bit

class reg_eesr_mask: # extended event register mask
    UPD = 0X0001    # updating
    ITG = 0x0002    # integrate busy
    ITM = 0x0004    # integrate time busy
    OVRS = 0x0008   # sigma overflow
    FOV = 0x0010    # frequency over
       


class Yokogawa(object):
    def __init__(self, comport=0, baudrate=9600):
        self._serial = serial.Serial(comport,baudrate)

    def write(self, string):
        return self._serial.write(string.encode())

    def readline(self):
        return self._serial.readline().decode()

    def configure_value(self, mode=None, synchronize=None,
                            voltage=None, current=None, samplerate=None):
        if mode is not None:
            self.write("CONFIGURE:MODE {}\n".format(mode))
        if synchronize is not None:
            self.write("CONFIGURE:SYNCHRONIZE {}\n".format("VOLTAGE" if synchronize else "OFF"))
        if voltage is not None:
            self.write("CONFIGURE:VOLTAGE:RANGE {}\n".format(voltage))
        if current is not None:
            self.write("CONFIGURE:CURRENT:RANGE {}\n".format(current))
        if samplerate is not None:
            self.write("SAMPLE:RATE {}\n".format(samplerate))

    def configure(self, measuretype):
        """
        :param measuretype: Type of measurement:
                            - '230V' (RMS), max. 300V & 2A
                            - '12V' (DC), max. 15V & 5A
                            - '5V' (DC), max. 6V & 4A
        : type measuretype: str
        """
        # initialize the device
        self.write("*RST\n")
        if measuretype == "230V":
            self.configure_value(mode="RMS", synchronize=True,
                                voltage=300, current=2)
        elif measuretype == "12V":
            self.configure_value(mode="DC", synchronize=False,
                                voltage=15, current=5)
        elif measuretype == "5V":
            self.configure_value(mode="DC", synchronize=False,
                                voltage=6, current=4)
        else:
            raise Exception("Unknown measuretype '{}'".format(measuretype))
        # when query measured data only V/A/W output
        self.write("MEASURE:NORMAL:ITEM:PRESET NORMAL\n")
        # update rate 0.1s
        self.configure_value(samplerate=0.1)
        # upd transit filter of updating set to fall
        self.write("STATUS:FILTER1 FALL\n")
        
    def clear_error_queue(self):
        """clear the standard event register, extended event register
        and error queue of wt230        
        """
        self.write("*CLS\n")
    
    def get_measured_data(self, status=False):
        if status:
            # clear the extended event register
            self.write("STATUS:EESR?\n")
            status = self.readline()
            print(datetime.datetime.now(), status)

        # wait for the completion of data updating
        self.write("COMMUNICATE:WAIT 1\n") 
        self.write("MEASURE:VALUE?\n")
        return "{},{}".format(datetime.datetime.now(),
                                self.readline())


def main():
    parser = ags.ArgumentParser("Measurement of voltage, current and power consumption via Yokogawa.")
    parser.add_argument("-d", "--dir", default=os.path.join("/home", "lab", "frehiwot", "power"), help="directory")
    parser.add_argument("-f", "--file", help="file name")
    parser.add_argument("-m", "--mode", default="230V", choices=["230V", "12V", "5V"],
                        help="measurement mode")
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        os.mkdir(args.dir)
    logfile = os.path.join(args.dir, "{}.csv".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) if args.file is None else args.file)
    print(logfile)

    print("start")
    yoko = Yokogawa()
    print("before configure")
    yoko.configure(args.mode)
    print("measuring")
    with open(logfile, "a") as f:
        f.write("timestamp,voltage,current,power\n")
        yoko.clear_error_queue()
        while True:
            print("reading")
            f.write(yoko.get_measured_data())
            f.flush()


if __name__ == "__main__":
    main()
