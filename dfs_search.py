import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque

def build_radial_graph(branch_lengths, cross_links=(), tree_only=False,
                        center=(500, 430), r_step=55, start_angle=90):
    nodes = {0: center}
    edges = []
    n_branches = len(branch_lengths)
    node_id = 1
    branch_node_ids = []
    for i, length in enumerate(branch_lengths):
        angle_deg = start_angle + i * (360.0 / n_branches)
        angle = math.radians(angle_deg)
        ids = []
        prev = 0
        for depth in range(1, length + 1):
            r = r_step * depth
            wiggle = 16 * math.sin(depth * 0.9 + i)
            x = center[0] + r * math.cos(angle) + wiggle * math.cos(angle + math.pi / 2)
            y = center[1] + r * math.sin(angle) + wiggle * math.sin(angle + math.pi / 2)
            nodes[node_id] = (x, y)
            edges.append((prev, node_id))
            ids.append(node_id)
            prev = node_id
            node_id += 1
        branch_node_ids.append(ids)
    if not tree_only:
        for (bi, di, bj, dj) in cross_links:
            u = branch_node_ids[bi][di]
            v = branch_node_ids[bj][dj]
            edges.append((u, v))
    return nodes, edges, branch_node_ids, node_id


def make_tree_A():
    nodes, edges, branches, n = build_radial_graph([6, 6, 5, 5, 7], tree_only=True)
    return nodes, edges, n, "Дерево (5 гілок)"


def make_graph_B():
    cross = [(0, 5, 1, 5), (2, 4, 3, 4), (3, 4, 4, 4), (0, 2, 1, 2), (2, 2, 3, 2)]
    nodes, edges, branches, n = build_radial_graph([6, 6, 5, 5, 7], cross_links=cross)
    extra = n
    nodes[extra] = (nodes[branches[0][-1]][0] + 40, nodes[branches[0][-1]][1] + 20)
    nodes[extra + 1] = (nodes[branches[4][-1]][0] - 30, nodes[branches[4][-1]][1] + 30)
    edges.append((branches[0][-1], extra))
    edges.append((branches[4][-1], extra + 1))
    edges.append((extra, extra + 1))
    n_total = extra + 2
    return nodes, edges, n_total, "Граф (5 гілок + цикли)"


def make_graph_C():
    lengths = [7, 7, 6, 6, 7, 7, 6, 6]
    cross = [(0, 6, 1, 6), (2, 5, 3, 5), (4, 6, 5, 6), (6, 5, 7, 5),
              (0, 3, 4, 3), (1, 3, 5, 3), (2, 2, 6, 2), (3, 2, 7, 2),
              (1, 6, 2, 5), (5, 5, 6, 5)]
    nodes, edges, branches, n = build_radial_graph(lengths, cross_links=cross,
                                                     center=(520, 430), r_step=50)
    return nodes, edges, n, "Великий граф (8 гілок)"


PRESETS = {
    "tree": make_tree_A,
    "graph": make_graph_B,
    "large": make_graph_C,
}
PRESET_NAMES = {"tree": "Дерево (30 в., 29 р.)",
                 "graph": "Граф (32 в., 37 р.)",
                 "large": "Великий граф (53 в., 62 р.)"}

ORDER_MODES = {
    "asc": "За зростанням id",
    "desc": "За спаданням id",
    "orig": "У порядку визначення",
    "rev": "У зворотному порядку визначення",
}

BULK_DIRECTION_MODES = {
    "undirected": "Усі ребра неорієнтовані",
    "outward": "Усі дуги: від центру до листя",
    "inward": "Усі дуги: від листя до центру",
}

ALGORITHMS = {
    "bfs": "Пошук у ширину (BFS)",
    "dfs": "Пошук у глибину (DFS)",
}


def make_edge(u, v, directed=False):
    return {"u": u, "v": v, "directed": directed, "base_u": u, "base_v": v}


def find_edge(edges, a, b):
    for e in edges:
        if {e["u"], e["v"]} == {a, b}:
            return e
    return None


def build_adjacency(nodes, edges):
    adj = {nid: [] for nid in nodes}
    for e in edges:
        if e["u"] not in adj or e["v"] not in adj:
            continue
        if e["directed"]:
            adj[e["u"]].append(e["v"])
        else:
            adj[e["u"]].append(e["v"])
            adj[e["v"]].append(e["u"])
    return adj


def order_neighbors(neigh, mode):
    if mode == "asc":
        return sorted(neigh)
    if mode == "desc":
        return sorted(neigh, reverse=True)
    if mode == "rev":
        return list(reversed(neigh))
    return list(neigh)  # 'orig'


def bfs_search(adj, start, target, order_mode):
    visited = {start}
    parent = {start: None}
    q = deque([start])
    events = [("enqueue", start, None)]
    expand_order = []
    found = False
    cycles = 0
    t0 = time.perf_counter()
    while q:
        cycles += 1
        u = q.popleft()
        expand_order.append(u)
        events.append(("dequeue", u, None))
        if u == target:
            found = True
            break
        for v in order_neighbors(adj.get(u, []), order_mode):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                events.append(("enqueue", v, u))
                q.append(v)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    path = []
    if found:
        cur = target
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()

    return {"algorithm": "bfs", "found": found, "path": path, "events": events,
            "visited_count": len(visited), "expanded_count": len(expand_order),
            "cycles": cycles, "time_ms": elapsed_ms}


def dfs_search(adj, start, target, order_mode):
    visited = {start}
    parent = {start: None}
    stack = [start]
    events = [("push", start, None)]
    expand_order = []
    found = False
    cycles = 0
    t0 = time.perf_counter()
    while stack:
        cycles += 1
        u = stack.pop()
        expand_order.append(u)
        events.append(("pop", u, None))
        if u == target:
            found = True
            break
        neigh = order_neighbors(adj.get(u, []), order_mode)
        for v in reversed(neigh):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                events.append(("push", v, u))
                stack.append(v)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    path = []
    if found:
        cur = target
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()

    return {"algorithm": "dfs", "found": found, "path": path, "events": events,
            "visited_count": len(visited), "expanded_count": len(expand_order),
            "cycles": cycles, "time_ms": elapsed_ms}


def run_search(algorithm, adj, start, target, order_mode):
    if algorithm == "dfs":
        return dfs_search(adj, start, target, order_mode)
    return bfs_search(adj, start, target, order_mode)



COLOR_IDLE = "#c9d6e3"
COLOR_QUEUE = "#f5d76e"
COLOR_CURRENT = "#e8743b"
COLOR_VISITED = "#8aa6c1"
COLOR_START = "#2e86de"
COLOR_TARGET = "#c0392b"
COLOR_PATH = "#27ae60"
COLOR_EDGE = "#7f8c8d"
COLOR_PATH_EDGE = "#27ae60"
COLOR_SELECTED = "#9b59b6"

NODE_R = 12


class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лаб. №2 — Пошук у ширину (BFS) і в глибину (DFS) на графах")
        self.root.geometry("1420x940")

        self.algorithm = tk.StringVar(value="bfs")
        self.order_mode = tk.StringVar(value="asc")
        self.speed_ms = tk.IntVar(value=180)
        self.instant = tk.BooleanVar(value=False)

        self.nodes = {}
        self.edges = []
        self.node_items = {}
        self.animating = False
        self.anim_job = None
        self._edit_first_node = None
        self._drag_node = None

        self._build_layout()
        self._load_preset()

    # ---------------------------------------------------------------- layout
    def _build_layout(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        outer = ttk.Frame(main)
        outer.pack(side="left", fill="y")
        panel_canvas = tk.Canvas(outer, width=310, highlightthickness=0)
        vscroll = ttk.Scrollbar(outer, orient="vertical", command=panel_canvas.yview)
        panel = ttk.Frame(panel_canvas, padding=10)
        panel.bind("<Configure>", lambda e: panel_canvas.configure(scrollregion=panel_canvas.bbox("all")))
        panel_canvas.create_window((0, 0), window=panel, anchor="nw", width=300)
        panel_canvas.configure(yscrollcommand=vscroll.set)
        panel_canvas.pack(side="left", fill="y")
        vscroll.pack(side="left", fill="y")

        ttk.Label(panel, text="Керування пошуком", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text="Алгоритм пошуку").pack(anchor="w")
        self.algo_combo = ttk.Combobox(panel, state="readonly", width=32,
                                        values=list(ALGORITHMS.values()))
        self.algo_combo.set(ALGORITHMS["bfs"])
        self.algo_combo.pack(anchor="w", pady=(0, 8))
        self._algo_name_to_key = {v: k for k, v in ALGORITHMS.items()}

        ttk.Label(panel, text="Граф (порядок і розмір)").pack(anchor="w")
        self.preset_combo = ttk.Combobox(panel, state="readonly", width=32,
                                          values=list(PRESET_NAMES.values()))
        self.preset_combo.set(PRESET_NAMES["graph"])
        self.preset_combo.pack(anchor="w", pady=(0, 8))
        self._preset_name_to_key = {v: k for k, v in PRESET_NAMES.items()}

        ttk.Label(panel, text="Початкова вершина").pack(anchor="w")
        self.start_combo = ttk.Combobox(panel, state="readonly", width=32)
        self.start_combo.pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text="Цільова вершина").pack(anchor="w")
        self.target_combo = ttk.Combobox(panel, state="readonly", width=32)
        self.target_combo.pack(anchor="w", pady=(0, 8))

        ttk.Button(panel, text="⇄ Поміняти старт/ціль місцями", command=self._swap_start_target).pack(anchor="w", fill="x", pady=(0, 8))

        ttk.Label(panel, text="Оператор переходу (порядок обходу сусідів)").pack(anchor="w")
        self.order_combo = ttk.Combobox(panel, state="readonly", width=32,
                                         values=list(ORDER_MODES.values()))
        self.order_combo.set(ORDER_MODES["asc"])
        self.order_combo.pack(anchor="w", pady=(0, 8))
        self._order_name_to_key = {v: k for k, v in ORDER_MODES.items()}

        ttk.Label(panel, text="Швидкість анімації (мс/крок)").pack(anchor="w")
        ttk.Scale(panel, from_=500, to=10, orient="horizontal", variable=self.speed_ms).pack(anchor="w", fill="x", pady=(0, 2))
        ttk.Checkbutton(panel, text="Миттєво (без анімації)", variable=self.instant).pack(anchor="w", pady=(0, 10))

        ttk.Separator(panel).pack(fill="x", pady=6)
        ttk.Button(panel, text="Побудувати / оновити граф", command=self._load_preset).pack(fill="x", pady=3)
        ttk.Button(panel, text="▶ Запустити пошук", command=self._run_search).pack(fill="x", pady=3)
        ttk.Button(panel, text="⏹ Зупинити анімацію", command=self._stop_animation).pack(fill="x", pady=3)
        ttk.Button(panel, text="Порівняти BFS і DFS", command=self._run_bfs_dfs_comparison).pack(fill="x", pady=3)
        ttk.Button(panel, text="Порівняти варіанти графів", command=self._run_graph_comparison).pack(fill="x", pady=3)
        ttk.Button(panel, text="Довідка: BFS проти DFS", command=self._show_help).pack(fill="x", pady=3)

        ttk.Label(panel, text="Групова зміна виду ребер").pack(anchor="w", pady=(8, 0))
        self.bulk_dir_combo = ttk.Combobox(panel, state="readonly", width=32,
                                            values=list(BULK_DIRECTION_MODES.values()))
        self.bulk_dir_combo.set(BULK_DIRECTION_MODES["undirected"])
        self.bulk_dir_combo.pack(anchor="w", pady=(0, 3))
        ttk.Button(panel, text="Застосувати до всього графа", command=self._apply_bulk_direction).pack(fill="x", pady=(0, 8))

        # --- редагування графа мишею ---
        edit_box = ttk.LabelFrame(panel, text="Ручне редагування графа (клік по полотну)", padding=6)
        edit_box.pack(fill="x", pady=(6, 0))

        self.edit_mode = tk.StringVar(value="none")
        self._edit_mode_names = {
            "none": "Перегляд (без редагування)",
            "add_vertex": "Додати вершину (клік по пустому місцю)",
            "del_vertex": "Видалити вершину (клік по ній)",
            "add_edge": "Додати ребро (клік 2 вершини)",
            "del_edge": "Видалити ребро (клік 2 вершини)",
            "toggle_direction": "Ребро ↔ дуга (клік 2 вершини)",
            "move_vertex": "Перемістити вершину (тягнути мишею)",
        }
        self.edit_mode_combo = ttk.Combobox(edit_box, state="readonly", width=30,
                                             values=list(self._edit_mode_names.values()))
        self.edit_mode_combo.set(self._edit_mode_names["none"])
        self.edit_mode_combo.pack(anchor="w", fill="x", pady=(0, 6))
        self._edit_mode_name_to_key = {v: k for k, v in self._edit_mode_names.items()}
        self.edit_mode_combo.bind("<<ComboboxSelected>>", self._on_edit_mode_change)

        self.edit_status_var = tk.StringVar(value="")
        ttk.Label(edit_box, textvariable=self.edit_status_var, wraplength=270,
                  foreground="#8a4b00").pack(anchor="w", pady=(0, 6))

        ttk.Button(edit_box, text="Новий порожній граф", command=self._new_empty_graph).pack(fill="x", pady=2)
        ttk.Button(edit_box, text="Скасувати поточний вибір", command=self._edit_reset_selection).pack(fill="x", pady=2)

        ttk.Separator(panel).pack(fill="x", pady=6)
        self.status_var = tk.StringVar(value="Готово.")
        ttk.Label(panel, textvariable=self.status_var, wraplength=270, foreground="#333").pack(anchor="w")

        legend = ttk.LabelFrame(panel, text="Умовні позначення", padding=6)
        legend.pack(fill="x", pady=(16, 0))
        self._legend_row(legend, COLOR_START, "початкова вершина")
        self._legend_row(legend, COLOR_TARGET, "цільова вершина")
        self._legend_row(legend, COLOR_QUEUE, "у черзі/стеку (виявлена)")
        self._legend_row(legend, COLOR_CURRENT, "розкривається зараз")
        self._legend_row(legend, COLOR_VISITED, "розкрита (оброблена)")
        self._legend_row(legend, COLOR_PATH, "вершина/ребро шляху")

        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg="white", width=1090, height=940)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    def _legend_row(self, parent, color, text):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=1)
        sw = tk.Canvas(row, width=14, height=14, highlightthickness=0)
        sw.create_oval(2, 2, 12, 12, fill=color, outline="")
        sw.pack(side="left", padx=(0, 6))
        ttk.Label(row, text=text).pack(side="left")

    # ------------------------------------------------------------- graph mgmt
    def _load_preset(self):
        self._stop_animation()
        name = self.preset_combo.get()
        key = self._preset_name_to_key.get(name, "graph")
        nodes, base_edges, n, _label = PRESETS[key]()
        self.nodes = nodes
        self.edges = [make_edge(u, v, False) for (u, v) in base_edges]
        self._refresh_start_target_values(reset=True)
        self.status_var.set(f"Граф завантажено: {len(self.nodes)} вершин, {len(self.edges)} ребер.")
        self._edit_reset_selection()
        self._redraw()

    def _new_empty_graph(self):
        self._stop_animation()
        self.nodes = {0: (540, 470)}
        self.edges = []
        self._refresh_start_target_values(reset=True)
        self.status_var.set("Створено порожній граф (1 вершина). Додавайте вершини й ребра в режимі редагування.")
        self._edit_reset_selection()
        self._redraw()

    def _refresh_start_target_values(self, reset=False):
        ids = sorted(self.nodes.keys())
        values = [str(i) for i in ids]
        cur_start = self.start_combo.get() if hasattr(self, "start_combo") else None
        cur_target = self.target_combo.get() if hasattr(self, "target_combo") else None
        self.start_combo["values"] = values
        self.target_combo["values"] = values
        if not values:
            self.start_combo.set(""); self.target_combo.set("")
            return
        if reset:
            self.start_combo.set(values[0]); self.target_combo.set(values[-1])
        else:
            self.start_combo.set(cur_start if cur_start in values else values[0])
            self.target_combo.set(cur_target if cur_target in values else values[-1])

    def _current_algorithm(self):
        return self._algo_name_to_key.get(self.algo_combo.get(), "bfs")

    def _current_order_key(self):
        return self._order_name_to_key.get(self.order_combo.get(), "asc")

    def _safe_int(self, s):
        try:
            return int(s)
        except (TypeError, ValueError):
            return None

    def _swap_start_target(self):
        s, t = self.start_combo.get(), self.target_combo.get()
        self.start_combo.set(t)
        self.target_combo.set(s)

    def _apply_bulk_direction(self):
        mode_name = self.bulk_dir_combo.get()
        mode = {v: k for k, v in BULK_DIRECTION_MODES.items()}.get(mode_name, "undirected")
        for e in self.edges:
            if mode == "undirected":
                e["u"], e["v"], e["directed"] = e["base_u"], e["base_v"], False
            elif mode == "outward":
                e["u"], e["v"], e["directed"] = e["base_u"], e["base_v"], True
            else:
                e["u"], e["v"], e["directed"] = e["base_v"], e["base_u"], True
        self.status_var.set(f"До всього графа застосовано режим: «{mode_name}».")
        self._redraw()

    # ------------------------------------------------------------- drawing
    def _redraw(self, node_colors=None, path_edges=None):
        self.canvas.delete("all")
        self.node_items = {}
        path_edge_set = set(path_edges) if path_edges else set()

        for e in self.edges:
            if e["u"] not in self.nodes or e["v"] not in self.nodes:
                continue
            x1, y1 = self.nodes[e["u"]]
            x2, y2 = self.nodes[e["v"]]
            is_path = (e["u"], e["v"]) in path_edge_set or (e["v"], e["u"]) in path_edge_set
            color = COLOR_PATH_EDGE if is_path else COLOR_EDGE
            width = 3 if is_path else 1.4
            kwargs = dict(fill=color, width=width)
            if e["directed"]:
                kwargs["arrow"] = tk.LAST
                kwargs["arrowshape"] = (18, 22, 8)
                kwargs["width"] = max(width, 2.2)
            self.canvas.create_line(x1, y1, x2, y2, **kwargs)

        start_id = self._safe_int(self.start_combo.get())
        target_id = self._safe_int(self.target_combo.get())
        for nid, (x, y) in self.nodes.items():
            fill = COLOR_IDLE
            outline, width = "#5a6b7b", 1
            if node_colors and nid in node_colors:
                fill = node_colors[nid]
            if nid == start_id:
                outline, width = COLOR_START, 3
            if nid == target_id:
                outline, width = COLOR_TARGET, 3
            oval = self.canvas.create_oval(x - NODE_R, y - NODE_R, x + NODE_R, y + NODE_R,
                                            fill=fill, outline=outline, width=width)
            text = self.canvas.create_text(x, y, text=str(nid), font=("Segoe UI", 8, "bold"))
            self.node_items[nid] = (oval, text)

    def _set_node_color(self, nid, color):
        if nid not in self.node_items:
            return
        oval, _ = self.node_items[nid]
        self.canvas.itemconfig(oval, fill=color)

    # ------------------------------------------------------------- manual editing (click)
    def _on_edit_mode_change(self, event=None):
        self._edit_reset_selection()
        mode = self._current_edit_mode()
        hints = {
            "none": "",
            "add_vertex": "Клацніть по вільному місцю на полотні, щоб додати нову вершину.",
            "del_vertex": "Клацніть по вершині, щоб видалити її (разом з усіма інцидентними ребрами).",
            "add_edge": "Клацніть по першій, потім по другій вершині, щоб з'єднати їх ребром.",
            "del_edge": "Клацніть по двох вершинах існуючого ребра, щоб видалити це ребро.",
            "toggle_direction": "Клацніть по двох вершинах існуючого ребра: воно перетвориться на дугу "
                                 "в напрямку кліків; повторний клік у тому ж порядку поверне звичайне ребро, "
                                 "клік у зворотному порядку змінить напрям дуги.",
            "move_vertex": "Затисніть ліву кнопку миші на вершині й перетягніть у нове місце.",
        }
        self.edit_status_var.set(hints.get(mode, ""))

    def _current_edit_mode(self):
        return self._edit_mode_name_to_key.get(self.edit_mode_combo.get(), "none")

    def _edit_reset_selection(self):
        self._edit_first_node = None
        self._drag_node = None

    def _node_at(self, x, y, tolerance=6):
        best_id, best_d = None, None
        for nid, (nx, ny) in self.nodes.items():
            d = math.hypot(nx - x, ny - y)
            if d <= NODE_R + tolerance and (best_d is None or d < best_d):
                best_id, best_d = nid, d
        return best_id

    def _next_free_id(self):
        return (max(self.nodes.keys()) + 1) if self.nodes else 0

    def _on_canvas_click(self, event):
        mode = self._current_edit_mode()
        if mode == "none":
            return
        x, y = event.x, event.y
        clicked = self._node_at(x, y)

        if mode == "add_vertex":
            if clicked is not None:
                self.edit_status_var.set("Тут уже є вершина. Клацніть по вільному місцю.")
                return
            new_id = self._next_free_id()
            self.nodes[new_id] = (x, y)
            self._refresh_start_target_values()
            self.status_var.set(f"Вершину {new_id} додано вручну. Усього вершин: {len(self.nodes)}.")
            self._redraw()

        elif mode == "del_vertex":
            if clicked is None:
                self.edit_status_var.set("Клацніть точно по вершині, яку треба видалити.")
                return
            del self.nodes[clicked]
            self.edges = [e for e in self.edges if e["u"] != clicked and e["v"] != clicked]
            self._refresh_start_target_values()
            self.status_var.set(f"Вершину {clicked} видалено разом з інцидентними ребрами. "
                                 f"Залишилось: {len(self.nodes)} вершин, {len(self.edges)} ребер.")
            self._redraw()

        elif mode == "add_edge":
            if clicked is None:
                self.edit_status_var.set("Клацніть по вершині (не по пустому місцю).")
                return
            if self._edit_first_node is None:
                self._edit_first_node = clicked
                self.edit_status_var.set(f"Обрано вершину {clicked}. Клацніть другу вершину для ребра.")
                self._redraw(node_colors={clicked: COLOR_SELECTED})
            else:
                u, v = self._edit_first_node, clicked
                self._edit_first_node = None
                if u == v:
                    self.edit_status_var.set("Не можна з'єднати вершину саму з собою.")
                elif find_edge(self.edges, u, v) is not None:
                    self.edit_status_var.set(f"Ребро {u}-{v} вже існує.")
                else:
                    self.edges.append(make_edge(u, v, False))
                    self.status_var.set(f"Додано ребро {u}-{v} вручну. Усього ребер: {len(self.edges)}.")
                self._redraw()

        elif mode == "del_edge":
            if clicked is None:
                self.edit_status_var.set("Клацніть по вершині (не по пустому місцю).")
                return
            if self._edit_first_node is None:
                self._edit_first_node = clicked
                self.edit_status_var.set(f"Обрано вершину {clicked}. Клацніть другу вершину ребра для видалення.")
                self._redraw(node_colors={clicked: COLOR_SELECTED})
            else:
                u, v = self._edit_first_node, clicked
                self._edit_first_node = None
                e = find_edge(self.edges, u, v)
                if e is None:
                    self.edit_status_var.set(f"Ребра між {u} і {v} не знайдено.")
                else:
                    self.edges.remove(e)
                    self.status_var.set(f"Ребро {u}-{v} видалено вручну. Залишилось ребер: {len(self.edges)}.")
                self._redraw()

        elif mode == "toggle_direction":
            if clicked is None:
                self.edit_status_var.set("Клацніть по вершині (не по пустому місцю).")
                return
            if self._edit_first_node is None:
                self._edit_first_node = clicked
                self.edit_status_var.set(f"Обрано вершину {clicked}. Клацніть другу вершину ребра, "
                                          f"яке треба перетворити.")
                self._redraw(node_colors={clicked: COLOR_SELECTED})
            else:
                u, v = self._edit_first_node, clicked
                self._edit_first_node = None
                e = find_edge(self.edges, u, v)
                if e is None:
                    self.edit_status_var.set(f"Ребра/дуги між {u} і {v} не знайдено.")
                else:
                    if not e["directed"]:
                        e["directed"] = True
                        e["u"], e["v"] = u, v
                        self.status_var.set(f"Ребро {u}-{v} вручну перетворено на дугу {u}→{v}.")
                    elif (e["u"], e["v"]) == (u, v):
                        e["directed"] = False
                        self.status_var.set(f"Дугу {u}→{v} вручну перетворено назад на звичайне ребро.")
                    else:
                        e["u"], e["v"] = u, v
                        self.status_var.set(f"Напрям дуги вручну змінено на {u}→{v}.")
                self._redraw()

        elif mode == "move_vertex":
            self._drag_node = clicked

    def _on_canvas_drag(self, event):
        if self._current_edit_mode() != "move_vertex" or self._drag_node is None:
            return
        self.nodes[self._drag_node] = (event.x, event.y)
        self._redraw()

    def _on_canvas_release(self, event):
        self._drag_node = None

    # ------------------------------------------------------------- search
    def _stop_animation(self):
        self.animating = False
        if self.anim_job is not None:
            try:
                self.root.after_cancel(self.anim_job)
            except Exception:
                pass
            self.anim_job = None

    def _run_search(self):
        self._stop_animation()
        start = self._safe_int(self.start_combo.get())
        target = self._safe_int(self.target_combo.get())
        if start is None or target is None or start not in self.nodes or target not in self.nodes:
            messagebox.showwarning("Увага", "Оберіть коректні початкову й цільову вершини.")
            return

        algorithm = self._current_algorithm()
        order = self._current_order_key()
        adj = build_adjacency(self.nodes, self.edges)
        result = run_search(algorithm, adj, start, target, order)
        self._last_result = result

        self._redraw()

        if self.instant.get():
            self._apply_final_state(result)
            self._show_result_window(result, algorithm, order)
            return

        self.animating = True
        self._animate_events(result["events"], 0, result, algorithm, order)

    def _animate_events(self, events, idx, result, algorithm, order):
        if not self.animating:
            return
        if idx >= len(events):
            self._apply_final_state(result)
            self._show_result_window(result, algorithm, order)
            self.animating = False
            return

        kind, node, _parent = events[idx]
        start_id = self._safe_int(self.start_combo.get())
        if kind in ("enqueue", "push"):
            self._set_node_color(node, COLOR_START if node == start_id else COLOR_QUEUE)
        elif kind in ("dequeue", "pop"):
            self._set_node_color(node, COLOR_CURRENT)

        delay = 0 if self.instant.get() else max(5, int(self.speed_ms.get()))
        self.anim_job = self.root.after(delay, lambda: self._post_step(events, idx, algorithm, order))

    def _post_step(self, events, idx, algorithm, order):
        kind, node, _parent = events[idx]
        if kind in ("dequeue", "pop"):
            start_id = self._safe_int(self.start_combo.get())
            target_id = self._safe_int(self.target_combo.get())
            if node not in (start_id, target_id):
                self._set_node_color(node, COLOR_VISITED)
        self._animate_events(events, idx + 1, self._last_result, algorithm, order)

    def _apply_final_state(self, result):
        start_id = self._safe_int(self.start_combo.get())
        target_id = self._safe_int(self.target_combo.get())
        colors = {}
        for kind, node, _p in result["events"]:
            if node not in (start_id, target_id):
                colors[node] = COLOR_VISITED
        path_edges = []
        if result["found"]:
            path = result["path"]
            for i in range(len(path) - 1):
                path_edges.append((path[i], path[i + 1]))
            for nid in path:
                if nid not in (start_id, target_id):
                    colors[nid] = COLOR_PATH
        self._redraw(node_colors=colors, path_edges=path_edges)

    # ------------------------------------------------------------- results
    def _show_result_window(self, result, algorithm, order):
        win = tk.Toplevel(self.root)
        win.title(f"Результат пошуку: {ALGORITHMS[algorithm]}")
        win.geometry("580x560")

        frame = ttk.Frame(win, padding=14)
        frame.pack(fill="both", expand=True)

        found_text = "ЗНАЙДЕНО" if result["found"] else "НЕ ЗНАЙДЕНО"
        color = "#1e8449" if result["found"] else "#c0392b"
        ttk.Label(frame, text=f"Шлях: {found_text}", font=("Segoe UI", 14, "bold"),
                  foreground=color).pack(anchor="w")
        ttk.Label(frame, text=ALGORITHMS[algorithm], font=("Segoe UI", 10, "italic")).pack(anchor="w")

        ttk.Separator(frame).pack(fill="x", pady=8)

        info = [
            ("Граф", self.preset_combo.get()),
            ("Оператор переходу", ORDER_MODES[order]),
            ("Початкова вершина", self.start_combo.get()),
            ("Цільова вершина", self.target_combo.get()),
            ("Довжина шляху (ребер)", str(len(result["path"]) - 1) if result["found"] else "—"),
            ("Кількість розкритих вершин", str(result["expanded_count"])),
            ("Кількість виявлених вершин", str(result["visited_count"])),
            ("Кількість циклів головного циклу алгоритму", str(result["cycles"])),
            ("Усього вершин у графі", str(len(self.nodes))),
            ("Усього ребер/дуг у графі", str(len(self.edges))),
            ("Час виконання алгоритму", f"{result['time_ms']:.4f} мс"),
        ]
        for label, value in info:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label + ":", width=34).pack(side="left", anchor="w")
            ttk.Label(row, text=value, font=("Segoe UI", 9, "bold")).pack(side="left", anchor="w")

        ttk.Separator(frame).pack(fill="x", pady=8)
        ttk.Label(frame, text="Знайдений шлях (послідовність вершин):").pack(anchor="w")
        path_str = " → ".join(map(str, result["path"])) if result["found"] else "шлях відсутній"
        txt = tk.Text(frame, height=6, wrap="word")
        txt.insert("1.0", path_str)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=False, pady=4)

        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor="e", pady=(10, 0))

    # ------------------------------------------------------------- comparison: BFS vs DFS
    def _run_bfs_dfs_comparison(self):
        start = self._safe_int(self.start_combo.get())
        target = self._safe_int(self.target_combo.get())
        if start is None or target is None or start not in self.nodes or target not in self.nodes:
            messagebox.showwarning("Увага", "Оберіть коректні початкову й цільову вершини.")
            return
        order = self._current_order_key()
        adj = build_adjacency(self.nodes, self.edges)

        rows = []
        for algo_key, algo_label in ALGORITHMS.items():
            r = run_search(algo_key, adj, start, target, order)
            rows.append((algo_label,
                         "так" if r["found"] else "ні",
                         (len(r["path"]) - 1) if r["found"] else "—",
                         " → ".join(map(str, r["path"])) if r["found"] else "—",
                         r["expanded_count"], r["visited_count"], r["cycles"],
                         f"{r['time_ms']:.4f}"))

        win = tk.Toplevel(self.root)
        win.title("Порівняння BFS і DFS на поточному графі")
        win.geometry("1200x260")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        cols = ("Алгоритм", "Знайдено?", "Довж. шляху", "Шлях", "Розкрито", "Виявлено", "Циклів", "Час, мс")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=2)
        widths = (150, 90, 100, 380, 90, 90, 80, 90)
        for c, w in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="center" if c != "Шлях" else "w")
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True)

        note = (f"Порівняння на графі «{self.preset_combo.get()}» ({len(self.nodes)} вершин, "
                f"{len(self.edges)} ребер/дуг), старт={start}, ціль={target}, "
                f"оператор переходу: «{ORDER_MODES[order]}».")
        ttk.Label(frame, text=note, wraplength=1160, foreground="#555").pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------- comparison: graph variants
    def _run_graph_comparison(self):
        order = self._current_order_key()
        algorithm = self._current_algorithm()
        start_sel = self._safe_int(self.start_combo.get())
        target_sel = self._safe_int(self.target_combo.get())

        rows = []
        for key, builder in PRESETS.items():
            nodes, base_edges, n, label = builder()
            ids = sorted(nodes.keys())
            s = start_sel if start_sel in nodes else ids[0]
            t = target_sel if target_sel in nodes else ids[-1]
            for mode_key, mode_label in BULK_DIRECTION_MODES.items():
                edges = []
                for (u, v) in base_edges:
                    if mode_key == "undirected":
                        edges.append(make_edge(u, v, False))
                    elif mode_key == "outward":
                        edges.append(make_edge(u, v, True))
                    else:
                        edges.append(make_edge(v, u, True))
                adj = build_adjacency(nodes, edges)
                r = run_search(algorithm, adj, s, t, order)
                rows.append((label, f"{len(nodes)} / {len(edges)}", mode_label, s, t,
                              "так" if r["found"] else "ні",
                              (len(r["path"]) - 1) if r["found"] else "—",
                              r["expanded_count"], r["cycles"],
                              f"{r['time_ms']:.4f}"))

        win = tk.Toplevel(self.root)
        win.title(f"Порівняння варіантів графів ({ALGORITHMS[algorithm]})")
        win.geometry("1180x420")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        cols = ("Граф", "Верш./Ребер", "Вид ребер", "Старт", "Ціль", "Знайдено?",
                "Довж. шляху", "Розкрито", "Циклів", "Час, мс")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=len(rows))
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=105, anchor="center")
        tree.column("Граф", width=160, anchor="w")
        tree.column("Вид ребер", width=190, anchor="w")
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True)

        note = (f"Алгоритм: «{ALGORITHMS[algorithm]}», оператор переходу: «{ORDER_MODES[order]}». "
                f"Старт/ціль обрані відповідно до поточного вибору, з корекцією індексів під розмір кожного графа.")
        ttk.Label(frame, text=note, wraplength=1140, foreground="#555").pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------- help
    def _show_help(self):
        win = tk.Toplevel(self.root)
        win.title("Довідка: BFS проти DFS")
        win.geometry("700x600")
        frame = ttk.Frame(win, padding=14)
        frame.pack(fill="both", expand=True)

        text = (
            "ПОШУК У ШИРИНУ (BFS) проти ПОШУКУ У ГЛИБИНУ (DFS)\n\n"
            "BFS розкриває вершини «хвилями» по рівнях відстані від старту, "
            "використовуючи чергу FIFO -- завдяки цьому перший знайдений шлях "
            "гарантовано найкоротший за кількістю ребер.\n\n"
            "DFS занурюється якнайглибше вздовж однієї гілки, використовуючи "
            "стек LIFO (або рекурсію) -- і лише коли гілка вичерпана, "
            "повертається й пробує наступну. Знайдений DFS шлях НЕ гарантовано "
            "найкоротший.\n\n"
            "BFS переваги: гарантована оптимальність шляху; передбачувана "
            "поведінка незалежно від структури графа.\n"
            "BFS недоліки: O(V) пам'яті на чергу і множину відвіданих вершин.\n\n"
            "DFS переваги: значно менші вимоги до пам'яті на глибоких графах "
            "(зберігає лише поточний шлях у стеку); просто реалізується рекурсивно.\n"
            "DFS недоліки: не гарантує найкоротшого шляху; може «застрягти» в "
            "довгій неоптимальній гілці, навіть якщо ціль поруч зі стартом.\n\n"
            "На орграфах обидва алгоритми однаково чутливі до напряму дуг: якщо "
            "єдиний шлях до цілі йде проти напряму дуг -- ні BFS, ні DFS шляху "
            "не знайдуть, попри те, що відповідний неорієнтований граф зв'язний."
        )
        txt = tk.Text(frame, wrap="word")
        txt.insert("1.0", text)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True)
        ttk.Button(frame, text="Закрити", command=win.destroy).pack(anchor="e", pady=(8, 0))


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = SearchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
