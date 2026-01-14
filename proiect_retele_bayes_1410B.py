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
    
def enumerate_all(vars_list, event, bn):
    if not vars_list: return 1.0
    Y = vars_list[0]
    node = bn.get_node(Y)
    rest = vars_list[1:]

    if Y in event:
        return node.p(event[Y], event) * enumerate_all(rest, event, bn)
    else:
        total = 0
        for val in [True, False]:
            extended_event = event.copy()
            extended_event[Y] = val
            total += node.p(val, extended_event) * enumerate_all(rest, extended_event, bn)
        return total

def enumeration_ask(X, evidence, bn):
    distribution = {}
    for val in [True, False]:
        extended_evidence = evidence.copy()
        extended_evidence[X] = val
        prob = enumerate_all(bn.variables, extended_evidence, bn)
        distribution[val] = prob
    total = sum(distribution.values())
    if total == 0: return {True: 0, False: 0}
    return {k: v / total for k, v in distribution.items()}

def load_network_from_json(filename='model_config.json'):
    if not os.path.exists(filename):
        messagebox.showerror("Eroare", f"Fisier lipsa: {filename}")
        return None, [], []

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = []
    causes_list = []
    symptoms_list = []

    for item in data['nodes']:
        processed_cpt = {}
        for k, v in item['cpt'].items():
            if k == "null":
                processed_cpt[()] = float(v)
            else:
                key_parts = k.split(',')
                bool_key = tuple(True if x.strip() == 'T' else False for x in key_parts)
                processed_cpt[bool_key] = float(v)
        
        if item['parents']:
            for combination in itertools.product([True, False], repeat=len(item['parents'])):
                if combination not in processed_cpt:
                    processed_cpt[combination] = 0.05

        nodes.append(BayesNode(item['id'], item['label'], item['parents'], processed_cpt))
        
        if item.get('type') == 'cause':
            causes_list.append(item['id'])
        else:
            symptoms_list.append(item['id'])

    return BayesNet(nodes), causes_list, symptoms_list