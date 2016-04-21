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
Generate workload with stochastic rate and video size with FFmpeg.
"""


import argparse
import database
import os, sys, time, signal, shutil
from multiprocessing import cpu_count
import random, subprocess



# Globals
processes = {}      # { fname : subprocess.Popen }
dstdir = None



def quit_properly(*args, **kwargs):
    for p in processes.values():
        p.terminate()
    shutil.rmtree(dstdir)
    sys.exit()



def remove_finished_files():
    finished = []
    for (key, val) in processes.items():
        if val.poll() is not None:
            print("Delete '{}'.".format(key))
            finished.append(key)
            os.remove(key)
    for key in finished:
        del processes[key]



def workload(wait, size, args):
    if not os.path.isdir(args.dstdir):
        os.mkdir(args.dstdir)
    db = database.database()
    while True:

        remove_finished_files()

        for cpu in args.cpus:
            s = int(size())
            src = db.get_fname(s)
            dst = os.path.join(args.dstdir, str(s)+".flv")
            processes[dst] = subprocess.Popen(
                                "taskset -c {} ffmpeg -loglevel 0 -i {} -vcodec flv -acodec adpcm_swf -ar 44100 -ac 2 -y {} > /dev/null 2>&1".format(cpu, src[0], dst), shell=True)
            print("Size: {:5.1f} MiB\t{:+1.3f} %\t on CPU {:2}".format(s/1024**2, (src[1]-s)/s*100, cpu))
        w = wait()
        print("Wait: {:2.2f} s".format(w))
        time.sleep(w)



def main():

    parser = argparse.ArgumentParser(description="Video transcoding workload generator.",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--dstdir", default="/home/frehiwot/Documents/cpufreq/", help="temporary destination directory of transcoded videos")
    parser.add_argument("--vmax", type=int, default=int(80e6), help="maximum video size")
    parser.add_argument("-c", "--cpus", type=lambda s: [int(i) for i in s.split(",")], default=list(range(cpu_count())), help="list of CPUs a transcoding is started on after every wait")

    parser.add_argument("-w", "--wait", type=int, default=30, help="time between transcodings")

    parser.add_argument("-s", "--size", choices=["const", "exp", "gauss", "uni"], default="exp", help="distribution of video size")
    group = parser.add_argument_group("Size: constant ('const')")
    group.add_argument("--csize", type=int, default=int(40e6), help="video size")
    group = parser.add_argument_group("Size: exponential distributed ('exp')")
    group.add_argument("-m", "--mu", type=float, default=int(15e6), help="expectation value")     # mu_db = 93770466
    group = parser.add_argument_group("Size: normal distributed ('gauss')")
    group.add_argument("--gmu", type=float, default=int(15e6), help="expectation value")
    group.add_argument("--gsigma", type=float, default=int(7.5e6), help="standard deviation")
    group = parser.add_argument_group("Size: uniform distributed ('uni')")
    group.add_argument("--uvmin", type=int, default=1, help="minimal video size")

    args = parser.parse_args()
    wait = lambda: args.wait
    if args.size == "const":
        size = lambda: min(args.csize, args.vmax)
    elif args.size == "exp":
        size = lambda: min(random.expovariate(1.0/args.mu), args.vmax)
    elif args.size == "gauss":
        size = lambda: max(1, min(random.normalvariate(args.gmu, args.gsigma), args.vmax))
    elif args.size == "uni":
        size = lambda: random.uniform(args.uvmin, args.vmax)

    global dstdir
    dstdir = args.dstdir
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, quit_properly)
    workload(wait, size, args)

    return 0


if __name__ == '__main__':
    main()


