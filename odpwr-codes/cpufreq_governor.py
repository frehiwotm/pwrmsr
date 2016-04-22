#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2016 Markus Haehnel
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

"""
Measurement of power consumption of vidserver depending on cpufreq-governor.
"""


import apy
import time, os


# Config
dstdir = "/home/frehiwot/Documents/pwr_odroid/cpufreq-governor/"
workloads = [
                dict(time=60, wait=30, uvmin=1, vmax=30000000),
                #dict(time=3600, idle=True), time=3600,
        ]
sockets = { 1 : list(range(1)),
            2 : list(range(4)),         # governor will be set for all vCPU incl. HyperThreads
            3 : list(range(6)),
            4 : list(range(8)),
          }
governors = ("performance", "powersave", "conservative", "ondemand")
#governors = ("powersave", )



class VidServer(apy.VidServer):
    def __init__(self):
        self._workload = None
        super().__init__()

    def workload_start(self, wait=None, vmax=None, cpus=None, uvmin=None, **trash):
        if self._workload is not None:
            self.stop(self._workload)
        command = "/home/frehiwot/Documents/pwr_odroid/odpwr-codes/wlgen_cpufreq-governor.py --size uni"
        if wait is not None:    command += " --wait {}".format(wait)
        if vmax is not None:    command += " --vmax {}".format(vmax)
        if uvmin is not None:   command += " --uvmin {}".format(uvmin)
        if cpus is not None:
            command += " --cpus {}".format(cpus[0])
            for c in cpus[1:]:
                command += "," + str(c)
        print(command)
        self._workload = self.start(command)

    def workload_stop(self):
        self.stop(self._workload)
        self._workload = None



def main():

    apy.announce()
    vidserver = VidServer()
    vidserver.announce()


    for wl in workloads:
        idle = "idle" in wl and wl["idle"]
        for (s, cpus) in sockets.items():
            for governor in governors:

                # configure
                vidserver.set_governor(governor)

                # start
                if not idle:
                    vidserver.workload_start(cpus=cpus, **wl)
                vidserver.dstat_start()

                # measure
                time.sleep(wl["time"])

                vidserver.dstat_stop()
                if not idle:
                    vidserver.workload_stop()
                    vidserver.call("pkill ffmpeg || echo")      # ???

                # get files
                prefix = "sockets={}_time={}_".format(s, wl["time"])
                prefix += "idle_governor={}".format(governor) if idle \
                            else "wait={wait}_uvmin={uvmin}_vmax={vmax}_governor={g}".format(g=governor, **wl)
                vidserver.dstat_save(os.path.join(dstdir, "{}_dstat.csv".format(prefix)))

            # skip different sockets (used only by workload) on idle
            if idle:    break

    vidserver.rmannounce()

    return 0


if __name__ == '__main__':
    main()

