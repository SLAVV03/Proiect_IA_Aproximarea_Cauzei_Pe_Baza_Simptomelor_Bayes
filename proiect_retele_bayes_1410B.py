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


class DesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diagnostice PC - Asistent Automat")
        self.geometry("850x600")

        self.net, self.causes, self.symptoms = load_network_from_json('model_config.json')

        if not self.net:
            self.destroy()
            return

        main_container = ttk.Frame(self, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)

        header_lbl = ttk.Label(main_container, text="Ce probleme are calculatorul?", font=("Helvetica", 16, "bold"))
        header_lbl.pack(pady=(0, 15))

        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(paned_window, text=" Selecteaza simptomele ", padding="10")
        paned_window.add(left_frame, weight=1)

        self.check_vars = {}

        canvas = tk.Canvas(left_frame)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scroll_content = ttk.Frame(canvas)

        scroll_content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for sym_id in self.symptoms:
            node = self.net.get_node(sym_id)
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(scroll_content, text=node.label, variable=var)
            cb.pack(anchor="w", pady=4, padx=5)
            self.check_vars[sym_id] = var

        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill=tk.X, pady=10)

        calc_btn = ttk.Button(action_frame, text="Gaseste Problema", command=self.calculate)
        calc_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        reset_btn = ttk.Button(action_frame, text="Reset", command=self.reset)
        reset_btn.pack(side=tk.RIGHT, padx=5)

        right_frame = ttk.LabelFrame(paned_window, text=" Cauze Posibile ", padding="10")
        paned_window.add(right_frame, weight=1)

        self.results_widgets = {}

        for cause_id in self.causes:
            node = self.net.get_node(cause_id)
            row = ttk.Frame(right_frame)
            row.pack(fill=tk.X, pady=5)

            lbl_name = ttk.Label(row, text=node.label, font=("Helvetica", 10, "bold"))
            lbl_name.pack(anchor="w")

            progress = ttk.Progressbar(row, length=200, mode='determinate')
            progress.pack(fill=tk.X, pady=2)

            lbl_pct = ttk.Label(row, text="0.0%", font=("Helvetica", 9))
            lbl_pct.pack(anchor="e")

            self.results_widgets[cause_id] = (progress, lbl_pct)

    def calculate(self):
        evidence = {k: v.get() for k, v in self.check_vars.items()}

        if not any(evidence.values()):
            messagebox.showinfo("Info", "Bifeaza macar o problema.")
            return

        results = []
        for cause in self.causes:
            prob_dict = enumeration_ask(cause, evidence, self.net)
            prob = prob_dict[True]
            results.append((cause, prob))

        results.sort(key=lambda x: x[1], reverse=True)

        best_val = 0
        best_name = ""

        for cause, prob in results:
            p_bar, lbl = self.results_widgets[cause]
            val_pct = prob * 100
            p_bar['value'] = val_pct
            lbl.config(text=f"{val_pct:.1f}%")

            if prob > best_val:
                best_val = prob
                best_name = self.net.get_node(cause).label

        if best_val > 0.5:
            messagebox.showinfo("Diagnostic",
                                f"Cauza probabila:\n\n{best_name}\n(Probabilitate: {best_val * 100:.1f}%)")

    def reset(self):
        for v in self.check_vars.values():
            v.set(False)
        for p_bar, lbl in self.results_widgets.values():
            p_bar['value'] = 0
            lbl.config(text="0.0%")


if __name__ == "__main__":
    app = DesktopApp()
    app.mainloop()