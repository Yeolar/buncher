# -*- coding: utf-8 -*-
#
# Copyright 2018 Yeolar
#

import os.path

from collections import defaultdict
from datetime import datetime
from operator import attrgetter


def get_package_base(name):
    base, _, __ = name.partition('-')
    return base if _ else ''


def get_package_version(name):
    return name.split('-')[1]


TYPE_MAP = {
    '.deb': 'DEB',
    '.xz': 'TXZ',
}


class Stat(object):

    def __init__(self, connection):
        self.connection = connection

    def listdir(self, path='.'):
        sftp = self.connection.sftp()
        d = defaultdict(list)
        for f in sftp.listdir_attr(path):
            base = get_package_base(f.filename)
            if base:
                d[base].append(f)
        for k in sorted(d.keys()):
            print k
            for f in sorted(d[k], key=attrgetter('filename'), reverse=True):
                print ' ',
                print get_package_version(f.filename),
                print TYPE_MAP[os.path.splitext(f.filename)[1]],
                print '%5dK' % (f.st_size / 1024),
                print datetime.fromtimestamp(f.st_mtime)

