#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Yeolar
#

class DAGNode(object):

    def __init__(self, name):
        self.name = name
        self.nexts = set()
        self.prevs = set()
        self.self_dep = False
        self.done = False

class DAG(object):

    def __init__(self):
        self.nodes = []
        self.index = {}
        self.cycle_dep = False

    def get_key(self, name):
        return self.index.get(name, -1)

    def get_node(self, name):
        return self.nodes[self.get_key(name)]

    def add(self, name):
        i = self.get_key(name)
        if i == -1:
            i = len(self.nodes)
            self.nodes.append(DAGNode(name))
            self.index[name] = i
        return i

    def add_dependency(self, a, b):
        self.nodes[a].nexts.add(b)
        self.nodes[b].prevs.add(a)

    def remove_dependency(self, a, b):
        self.nodes[a].nexts.remove(b)
        self.nodes[b].nexts.remove(a)

    def has_cycle(self):
        nexts = []  # [[]]
        for node in self.nodes:
            nexts.append(list(node.nexts))
        targets = [0] * len(self.nodes)
        for edges in nexts:
            for key in edges:
                targets[key] += 1
        keys = []
        for key in range(len(self.nodes)):
            if not self.nodes[key].prevs:
                keys.append(key)
        while keys:
            key = keys[-1]
            del keys[-1:]
            while nexts[key]:
                nxt = nexts[key][-1]
                del nexts[key][-1:]
                targets[nxt] -= 1
                if targets[nxt] == 0:
                    keys.append(nxt)
        for edges in nexts:
            if edges:
                return True
        return False

