import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import itertools

class BayesNode:
    def __init__(self, name, label, parents, cpt):
        self.name = name
        self.label = label
        self.parents = parents
        self.cpt = cpt

    def p(self, value, event):
        if not self.parents:
            ptrue = self.cpt.get((), 0.01)
        else:
            parent_vals = tuple(event[parent] for parent in self.parents)
            ptrue = self.cpt.get(parent_vals, 0.01)
        return ptrue if value else 1 - ptrue

class BayesNet:
    def __init__(self, nodes):
        self.nodes = nodes
        self.variables = [node.name for node in nodes]
        self.node_map = {n.name: n for n in nodes}
    def get_node(self, name):
        return self.node_map.get(name)