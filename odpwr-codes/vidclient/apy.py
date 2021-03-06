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
API for Python to control distributed things in a coherent way.
"""



import subprocess, os, time



################
### Machines ###
################

class SshDevice:
    """
    Base class for an device controlled over SSH.

    :param host: user@address or SSH agent's host name
    :type host: str
    :param password: sudo authentication
    :type password: str
    :param message: announce
    :type message: str

    Class variable:
        commands = { "name" : "command"}
        --> creates name_start() and name_stop() routines
    """
    commands = {}

    def __init__(self, host, password=None):
        self.host = host
        self.password = password
        self._processes = dict()
        super().__init__()          # additional features

        # integrated commands from class variable
        self._commands = dict()
        def start(c):
            if c in self._commands: self.stop(self._commands[c])
            self._commands[c] = self.start(c)
        def stop(c):
            self.stop(self._commands[c])
        for (key, val) in type(self).commands.items():
            self.__setattr__("{}_start".format(key), lambda: start(val))
            self.__setattr__("{}_stop".format(key), lambda: stop(val))

    def __delete__(self):
        if self._motd:
            self.rmannounce()

    def _SSHcommand(self, command, sudo=False):
        if sudo:
            if self.password is None:
                raise Exception("No password set.")
            command = "echo {} | sudo -S sh -c '{}'".format(self.password, command)
        return command

    def call(self, command, sudo=False, **kwargs):
        """
        Execute command on remote device and wait for its end.

        :param sudo: run command as root
        :type sudo: bool
        :param kwargs: additional keyword arguments for subprocess.call
        :type kwargs: dict        :returns: stdout and stderr
        :rtype: str, str
        """
        return subprocess.check_output(["ssh", self.host, self._SSHcommand(command, sudo=sudo)], **kwargs).decode("ascii")

    def start(self, command, sudo=False, delay=0.1, **kwargs):
        """
        Start command on remote device.

        :param sudo: run command as root
        :type sudo: bool
        :param delay: delay after getting process id to prevent connection closing befor process really started
        :type delay: float
        :param kwargs: additional keyword arguments for subprocess.Popen
        :type kwargs: dict
        :returns: process id of remote process
        :rtype: int
        """
        p =  subprocess.Popen(["ssh", self.host, "{} & echo $! && sleep {}".format(
                    self._SSHcommand(command, sudo=sudo), delay)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    **kwargs)
        pid = int(p.stdout.readline())
        self._processes[pid] = p
        return pid

    def stop(self, pid):
        """Kill process of process id if still running."""
        if self._processes[pid].poll() is None:
            subprocess.call(["ssh", self.host, "kill {}".format(pid)])

    def is_running(self, pid):
        """Check whether remote process is still running."""
        return self._processes[pid].poll() is None

    def get_output(self, pid):
        """Return stdout and stderr of finished processes."""
        if self.is_running(pid):
            raise subprocess.CalledProcessError("Remote process with id '{}' is still running.".format(pid))
        stderr = ""
        for l in self._processes[pid].stderr:
            stderr += l.decode("ascii") 
        stdout = ""
        for l in self._processes[pid].stdout:
            stdout += l.decode("ascii")
        return stdout, stderr

    def announce(self, msg="Frehiwot Konjo"):
        self.call("echo {} > /tmp/measrun".format(msg))

    def rmannounce(self):
        try:    self.call("rm /tmp/measrun")
        except subprocess.CalledProcessError:   pass
        self._motd = False

    def ntpdate(self, server="ntp.ubuntu.com", critical=True):
        """
        Synchronize system time.

        :param critical: raise exception on non-zero exit status
        :type critical: bool
        :returns: output of ntpdate call, 'None' if an error occured
        :rtype: str
        """
        out = None
        try:
            out = self.call("ntpdate {}".format(server), sudo=True)
        except subprocess.CalledProcessError as e:
            if critical:    raise e
        return out

    def set_governor(self, governor, cpus=None):
        """Set governor to each logical CPU."""
        if cpus is None:
            if not hasattr(self, "cpus"):
                self.cpus = int(self.call("grep -c ^processor /proc/cpuinfo"))
            self.call("for i in $(seq 0 1 {}); do echo {} > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor; done".format(self.cpus-1, governor), sudo=True)
            return
        for cpu in cpus:
            self.call("echo {} > /sys/devices/system/cpu/cpu{}/cpufreq/scaling_governor".format(governor, cpu), sudo=True)


class FeatureDstat:
    def __init__(self):
        self._dstat, self._dstat_fname = None, None
        super().__init__()

    def dstat_start(self, user="markus", prefix="pyAPI",
                    datetime=None):
        if self._dstat is not None:
            self.stop(self._dstat)
        self._dstat_fname = os.path.join("/home/odroid/Documents/odroidtranscoding/dstat/",
                "{}_{}.csv".format(prefix,
                time.strftime("%Y-%m-%d_%H-%M-%S") if datetime is None else datetime))
        self._dstat = self.start("dstat -tclmndN eth1,eth2 --output {}".format(self._dstat_fname))

    def dstat_stop(self):
        self.stop(self._dstat)
        self._dstat = None

    def dstat_save(self, dst):
        """Download the remote file to given local destination."""
        if self._dstat_fname is None:
            raise Exception("There is no file to download.")
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.split(self._dstat_fname)[1])
        return subprocess.call(["scp", "{}:{}".format(self.host, self._dstat_fname), dst])


class FeatureWT230:
    """Feature of old power sampling script."""
    def __init__(self):
        self._wt230, self._wt230_fname = None, None
        super().__init__()

    def WT230_start(self, mode="230V", user="frehiwot", prefix="pyAPI", datetime=None):
        """
        :param mode: '230V' or '12V'
        :type mode: str
        """
        if self._wt230 is not None:
            self.stop(self._wt230)
        self._wt230_fname = os.path.join("/home/lab", user, "power",
                "{}_{}.csv".format(prefix,
                time.strftime("%Y-%m-%d_%H-%M-%S") if datetime is None else datetime))
        self._wt230 = self.start("WT230 -u {} -p {} -t {} -m {}".format(user, prefix,
                time.strftime("%Y-%m-%d_%H-%M-%S") if datetime is None else datetime,
                mode))

    def WT230_stop(self):
        self.stop(self._wt230)
        self._wt230 = None

    def WT230_save(self, dst):
        """Download the remote file to given local destination."""
        if self._wt230_fname is None:
            raise Exception("There is no file to download.")
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.split(self._wt230_fname)[1])
        return subprocess.call(["scp", "{}:{}".format(self.host, self._wt230_fname), dst])


class FeatureYokogawa:
    """Feature of old power sampling script."""
    def __init__(self):
        self._yokogawa, self._yokogawa_fname = None, None
        super().__init__()

    def yokogawa_start(self, mode="230V",
                        dir="/home/lab/frehiwot/power", file=None):
        """
        :param mode: '230V, '12V' or '5V'
        :type mode: str
        """
        if self._yokogawa is not None:
            self.stop(self._yokogawa)
        command = "yokogawa -m {}".format(mode)
        if file is None:
            file = "{}.csv".format(time.strftime("%Y-%m-%d_%H-%M-%S"))
        self._yokogawa_fname = os.path.join(dir, file)
        self._yokogawa = self.start("yokogawa -m {} -d {} -f {}".format(mode, dir, file))

    def yokogawa_stop(self):
        self.stop(self._yokogawa)
        self._yokogawa = None

    def yokogawa_save(self, dst):
        """Download the remote file to given local destination."""
        if self._yokogawa_fname is None:
            raise Exception("There is no file to download.")
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.split(self._yokogawa_fname)[1])
        return subprocess.call(["scp", "{}:{}".format(self.host, self._yokogawa_fname), dst])



class VidServer(SshDevice, FeatureDstat):
    """
    SshDevice for the vidserver with integrated Dstat and IntelPCM.
    """
    def __init__(self):
        super().__init__(host="141.76.41.124", password="wireless")



class PwrSmplr(SshDevice, FeatureWT230, FeatureYokogawa):
    """
    SshDevice for the pwrsmplrs with integrated WT230 & Yokogawa.

    :param number: id of PowerSampler
    :type number: int
    """
    def __init__(self, number):
        super().__init__(("141.76.41.125", "141.76.41.126")[number-1], password="wireless")


######################
### Local commands ###
######################

def announce(msg="Frehiwot Konjo"):
    with open("/tmp/measrun", "w") as f:
        f.write(msg)

def rmannounce():
    os.remove("/tmp/measrun")

