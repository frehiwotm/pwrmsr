"""
Copy videos of different sizes with different intervals.
"""

import odatabase
import os


def main():
    fsize_intervals = [[0, 2000000], [2000000, 5000000], [5000000, 10000000], [10000000, 20000000],[20000000, 30000000], [30000000, 50000000]]
    steps = [100, 1000, 10000, 140000, 250000, 700000]
    vid_fname = []
    fname = []

    dbobj = odatabase.videos()

    for size in range(0,74111,23000):
        vid_fname.append(dbobj.get_fname(size))

    for f in vid_fname:
        fname.append((f[0]))

    dbobj.copy_file(fname)

def test():

    fsize_intervals = [[0,3], [3, 7], [7, 11], [11, 16],
                       [16, 22], [22, 27]]
    steps = [1, 2, 3, 4, 5, 6]

    for size, step in zip(fsize_intervals, steps):
        for fsize in range(size[0], size[1], step):
            print("the values are {} , {}, {}:".format(size[0], size[1], step))
            print("fsize:", fsize)

if __name__ == '__main__':

    test()



