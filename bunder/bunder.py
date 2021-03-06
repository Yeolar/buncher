#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Yeolar
#

import argparse
import imp
import multiprocessing
import os
import shutil
import sys

from collections import defaultdict
from datetime import datetime
from operator import attrgetter

from .connection import Connection
from .util import *


PROG_NAME = 'bunder'

conf = config('~/.bunder.yml', '.bunder.yml')


def basename(name):
    return name.split('-')[0]

def fullname(name, deb=False):
    return '%s-%s%s' % (
        name,
        conf.arch or 'amd64',
        deb and '.deb' or '.tar.xz')

def package_base(name):
    base, _, __ = name.partition('-')
    return base if _ else ''

def package_version(name):
    return name.split('-')[1]


class Handler(object):

    def __init__(self):
        self.c = Connection(conf.source.host)

    def build_path(self, name):
        return os.path.join(conf.build.path, basename(name))

    def deps_path(self, name):
        return os.path.join(conf.build.path + '-deps', basename(name))

    def remote_path(self, name):
        return os.path.join(conf.source.path, fullname(name))

    def package(self, project):
        return [os.path.join(conf.build.path, i)
                for i in os.listdir(conf.build.path)
                if i.startswith(project) and
                   os.path.splitext(i)[1] in ('.deb', '.xz')]


class PkgCleanHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

    def __call__(self, cleaning):
        if not cleaning:
            return False
        run('rm -rf build && mkdir build')
        return True


class PkgGenMakeHandler(Handler):

    CMAKE_GEN_CMD = 'cmake -DCMAKE_TOOLCHAIN_FILE=../%s ..'

    def __init__(self):
        Handler.__init__(self)

    def __call__(self, toolchain):
        if toolchain is None:
            return False
        tc = 'cmake-scripts/%s-toolchain.cmake' % toolchain
        if os.path.exists(tc):
            run('cd build && ' + (self.CMAKE_GEN_CMD % tc))
        else:
            run('cd build && cmake ..')
        return True


class PkgBuildHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

    def __call__(self, job):
        if job is None:
            return False
        run('cd build && make -j %d && make package' % job)
        return True


class PkgPackHandler(Handler):

    PACK_CMD = 'dpkg-scanpackages -m . | gzip - > Packages.gz'

    def __init__(self):
        Handler.__init__(self)

    def __call__(self, path):
        print white('pack: %s' % path, True)
        remote = os.path.join(conf.source.path, os.path.basename(path))
        direct = os.path.dirname(remote)
        self.c.put(path, remote)
        if os.path.splitext(path)[1] == '.deb':
            self.c.run('cd %s && %s' % (direct, self.PACK_CMD))


class PkgListHandler(Handler):

    TYPE_MAP = { '.deb': 'DEB', '.xz': 'TXZ', }

    def __init__(self):
        Handler.__init__(self)

    def __call__(self):
        files = self.c.sftp().listdir_attr(conf.source.path)
        d = defaultdict(list)
        for f in files:
            base = package_base(f.filename)
            if base:
                d[base].append(f)
        for k in sorted(d.keys()):
            print k
            for f in sorted(d[k], key=attrgetter('filename'), reverse=True):
                print ' ',
                print package_version(f.filename),
                print self.TYPE_MAP[os.path.splitext(f.filename)[1]],
                print '%5dK' % (f.st_size / 1024),
                print datetime.fromtimestamp(f.st_mtime)


class DepInstallHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

    def __call__(self, dep):
        print 'install dep: %s' % dep
        direct = os.path.join(self.deps_path(dep), basename(dep))
        target = os.path.join(self.deps_path(dep), fullname(dep))
        if os.path.exists(target):
            print '  already installed.'
            return
        if not os.path.exists(direct):
            os.makedirs(direct, 0755)
        self.c.get(self.remote_path(dep), target)
        self.c.local('tar xJf %s -C %s --strip-components=1' % (target, direct))


class DepDeleteHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

    def __call__(self, dep):
        print 'delete dep: %s' % dep
        shutil.rmtree(self.deps_path(dep))


def pkg_build(toolchain, cleaning, building):
    return PkgCleanHandler()(cleaning) \
        or PkgGenMakeHandler()(toolchain) \
        or PkgBuildHandler()(building)


def pkg_pack(names):
    handler = PkgPackHandler()
    if not map(handler, names or handler.package(conf.project)):
        print yellow('pack none package.')


def dep_install(names):
    handler = DepInstallHandler()
    if not map(handler, names or conf.depend or []):
        print yellow('install none dep.')


def dep_delete(names):
    handler = DepDeleteHandler()
    if not map(handler, names or conf.depend or []):
        print yellow('delete none dep.')


def main():
    ap = argparse.ArgumentParser(
            prog=PROG_NAME,
            description='Bunder tool.',
            epilog='Author: Yeolar <yeolar@gmail.com>',
            add_help=False)

    ag = ap.add_argument_group('building')
    ag.add_argument('-g', '--gen',
                    action='store', nargs='?', metavar='toolchain', const='gcc',
                    help='generate package build environment')
    ag.add_argument('-b', '--build',
                    action='store', nargs='?', metavar='job', const=multiprocessing.cpu_count,
                    help='build package')
    ag.add_argument('-c', '--clean',
                    action='store_true', default=False,
                    help='cleaning before generate')

    ag = ap.add_argument_group('package')
    ag.add_argument('-p', '--pack',
                    action='store', nargs='*', metavar='pkg',
                    help='pack package to deb host.')
    ag.add_argument('-l', '--list',
                    action='store_true', default=False,
                    help='list package on deb host.')

    ag = ap.add_argument_group('dependency')
    ag.add_argument('-i', '--dep-install',
                    action='store', nargs='*', metavar='dep',
                    help='initialize dependencies.')
    ag.add_argument('-d', '--dep-delete',
                    action='store', nargs='*', metavar='dep',
                    help='clean dependencies.')

    ag = ap.add_argument_group('others')
    ag.add_argument('-h', '--help',
                    action='store_true',
                    help='show help')

    args = ap.parse_args()

    if args.list:
        PkgListHandler()()
        return
    if pkg_build(args.gen, args.clean, args.build):
        return
    if args.pack is not None:
        pkg_pack(args.pack)
        return
    if args.dep_install is not None:
        dep_install(args.dep_install)
        return
    if args.dep_delete is not None:
        dep_delete(args.dep_delete)
        return

    ap.print_help()


if __name__ == '__main__':
    main()

