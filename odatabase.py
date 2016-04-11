#!/usr/bin/env python3


"""
Categorize and find videos into database.
"""

import sqlite3, os, glob
import random
import shutil 

class BaseDatabase(object):
    """
    Base class for file databases.

    :param dbfile: path to database file.
    :type dbfile: str
    :param quiet: If True, overwrite an existing database file.
    :type quiet: bool
    """

    def __init__(self, dbfile=":memory:", quiet=False):
        """Returns True if new database was created and new tables are needed."""

        # check existing file
        i = None
        if os.path.exists(dbfile):
            i = input("Database file still exists. Append [a], reset [r] or quit [q]? ")
            if i == "r" or quiet:    os.remove(dbfile)
            elif i != "a":  return None

        # connect to file
        self.conn = sqlite3.connect(dbfile)
        return i != "a"


    def print(self, query, *args):
        """
        :param query: statement which result should be printed
        :type query: str
        """

        for l in self.conn.execute(query, *args):
            print(l)


class videos(BaseDatabase):
    """
    :param path: directory and pattern to search for videos
    :type path: str
    """
    def __init__(self, path="/home/videos/*.mp4", **kwargs):

        if super().__init__(**kwargs):    # Create Table
            self.conn.execute("CREATE TABLE videos (vid INT PRIMARY KEY, fname TEXT, size INT)")

        # insert values
        for f in glob.glob(path):
            fname = os.path.split(f)[1]
            vid, size = os.path.splitext(fname)[0].split("_")
            vid, size = int(vid), int(size)
            #print(vid, fname, size)
            self.conn.execute("INSERT INTO videos(fname, size) VALUES (?, ?)", (f, size))

        self.conn.commit()


    def get_fname(self, size):
        """
        Find a file with size nearest to X.

        :param size: size to look for
        :type size: int
        :returns: tuple of filename and real size
        :rtype: tuple(str, int)
        """

        c = self.conn.cursor()
        c.execute("SELECT fname, size FROM videos ORDER BY ABS(size - ?) LIMIT 1", (size,))
        #c.execute("SELECT fname FROM videos ORDER BY ABS(size - ?) LIMIT 1", (size,))
        return c.fetchone()
        

    def copy_file(self, src, dest='/home/lab/frehiwot/task2016/videos'):
        """
        Copy a file to dest directory.
        """
        try:
            shutil.copy(src, dest)
        except shutil.Error as e:
            print("Error: %s " % e)
        except IOError as e:
            print("Error: %s " % e.strerror)



class database(videos):
    """Backwards compatibility for videos."""
    pass

