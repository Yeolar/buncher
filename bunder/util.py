#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Yeolar
#

import json
import os
import subprocess
import sys
import time
import yaml


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = '1;%s' % c
        return '\033[%sm%s\033[0m' % (c, text)
    return inner

red = _wrap_with('31')
green = _wrap_with('32')
yellow = _wrap_with('33')
blue = _wrap_with('34')
magenta = _wrap_with('35')
cyan = _wrap_with('36')
white = _wrap_with('37')


class ObjectDict(dict):
    """Makes a dictionary behave like an object, with attribute-style access.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


def to_object_dict(d):
    if isinstance(d, dict):
        for k in d:
            d[k] = to_object_dict(d[k])
        return ObjectDict(d)
    return d


def json_loads_object_dict(s):
    return json.loads(s, object_hook=ObjectDict)


def rrfind_file(name, level=2):
    path = os.getcwd()
    while path != '/' and level > 0:
        file = os.path.join(path, name)
        if os.path.exists(file):
            return file
        path = os.path.dirname(path)
        level -= 1
    return ''


def run(cmd, timer=False):
    print cyan(cmd, True)
    t = time.time()
    subprocess.call(cmd, shell=True)
    if timer:
        print red('Cost: %.2fs' % (time.time() - t), True)


def config(*names):
    conf = {}
    for name in names:
        try:
            with open(os.path.expanduser(name)) as fp:
                conf.update(yaml.load(fp.read()))
        except IOError:
            print red('Missing conf: %s' % name, True)
            sys.exit(1)
    return to_object_dict(conf)


def pretty_size(n):
    pretty_suffix = (
        ( "TB", 1 << 40 ),
        ( "GB", 1 << 30 ),
        ( "MB", 1 << 20 ),
        ( "kB", 1 << 10 ),
        ( "B ", 0 ),
    )
    for unit, slot in pretty_suffix:
        if n >= slot:
            return '%.4g %s' % (slot and float(n)/slot or n, unit)
    return str(n)


def log_in_process(transfered, total):
    percent = transfered * 100 / total
    msg = '[%s%s%s] %3d%% %s' % (
        percent < 4 and '' or '=' * (percent / 2 - 1),
        percent < 2 and '' or '>',
        ' ' * (50 - percent / 2),
        percent,
        pretty_size(total))
    end = '\n' if transfered == total else '\r'
    sys.stdout.write(msg + end)
    sys.stdout.flush()

