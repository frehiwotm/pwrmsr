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
Select and copy videos from video pool with constant relative distance.
"""

import math, shutil
import database


def main(minsize=11.5e3, maxsize=50e6, factor=1.0025,
            dstdir="/home/videos/subset/"):

    number = int( math.log(maxsize/minsize)/math.log(factor) + 0.5 )
    print("{} videos between {:n} and {:n} Bytes will be copied. Each is {:.2f}% bigger than the previous one.".format(number, minsize, maxsize, (factor-1)*100))
    print("The size of all files will be approx. {:.3f} GiB, located in {}.".format(
            sum(minsize * factor**i for i in range(number))/1024**3, dstdir))
    if input("Type 'yes' for continueing: ") not in ("yes", "y"):
        return 1

    if not shutil.os.path.isdir(dstdir):
        shutil.os.mkdir(dstdir)

    previous = None
    db = database.videos()
    for i in range(number):
        vidsize = minsize * factor**i
        video = db.get_fname(vidsize)[0]
        if video == previous:
            print("Skip video '{}' for video size '{:n}'.".format(video, vidsize))
        else:
            shutil.copy(video, dstdir)
        previous = video


if __name__ == "__main__":
    main()
