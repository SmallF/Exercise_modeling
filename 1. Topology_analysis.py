import json, math
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle

# -------------------------
# 0) color config
# -------------------------
C_PRE_ONLY  = "#7A9994"   # 蓝
C_POST_ONLY = "#DEA97D"   # 红
C_EDGE      = "#9AA0A6"   # 边颜色（中性灰）
C_DISK_EDGE = "#D0D0D0"   # 圆盘边界
C_EMPTY     = "#BBBBBB"   # 0 clone 节点

# -------------------------
# 1) load graph
# -------------------------
def load_graph(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    G = nx.Graph()
    for n in data["nodes"]:
        G.add_node(n["id"], label=n.get("label", str(n["id"])))
    for e in data["links"]:
        G.add_edge(e["source"], e["target"], weight=e.get("weight", 1.0))
    return G

# -------------------------
# 2) clone size from Matrix (index = CDR3(pep))
# -------------------------
def load_clone_sizes(G, matrix_csv):
    M = pd.read_csv(matrix_csv, index_col=0).fillna(0)
    label_of = nx.get_node_attributes(G, "label")
    clone = {}
    for node_id, cdr3 in label_of.items():
        clone[node_id] = float(M.loc[cdr3].sum()) if cdr3 in M.index else 0.0
    return clone

# -------------------------
# 3) unified layout (compute ONCE), then squeeze into disk
# -------------------------
def unified_layout_union(G_union):
    return nx.kamada_kawai_layout(G_union, scale=1.0)

def normalize_to_disk(pos, R=1.0, margin=0.08):
    coords = np.array(list(pos.values()), dtype=float)
    if len(coords) == 0:
        return pos
    center = coords.mean(axis=0)
    coords = coords - center
    r = np.sqrt((coords**2).sum(axis=1))
    rmax = float(r.max()) + 1e-12
    scale = (R * (1 - margin)) / rmax
    coords = coords * scale
    return {n: coords[i] for i, n in enumerate(pos.keys())}

# -------------------------
# 4) size mapping: clone -> node radius
# -------------------------
def radius_map(values, v_max, r_min=0.010, r_max=0.060, mode="sqrt"):
    vals = np.array(values, dtype=float)
    x = vals / (v_max + 1e-12)
    if mode == "sqrt":
        x = np.sqrt(x)
    elif mode == "log":
        x = np.log1p(vals) / np.log1p(v_max + 1e-12)
    return r_min + x * (r_max - r_min)

# -------------------------
# 5) draw pie node
# -------------------------
def draw_pie_node(ax, xy, r, pre_val, post_val,
                  c_pre=C_PRE_ONLY, c_post=C_POST_ONLY,
                  alpha=0.95, gap_deg=0.0,
                  edgecolor=None, linewidth=0.0):
    total = pre_val + post_val
    if total <= 0:
        ax.add_patch(Circle(xy, r*0.7, facecolor=C_EMPTY, edgecolor="none", alpha=0.6))
        return

    frac_pre = pre_val / total
    start = 90.0
    mid = start + 360.0 * frac_pre

    if gap_deg > 0:
        g = gap_deg / 2.0
        ax.add_patch(Wedge(xy, r, start + g, mid - g, facecolor=c_pre,
                           edgecolor=edgecolor, linewidth=linewidth, alpha=alpha))
        ax.add_patch(Wedge(xy, r, mid + g, start + 360.0 - g, facecolor=c_post,
                           edgecolor=edgecolor, linewidth=linewidth, alpha=alpha))
    else:
        ax.add_patch(Wedge(xy, r, start, mid, facecolor=c_pre,
                           edgecolor=edgecolor, linewidth=linewidth, alpha=alpha))
        ax.add_patch(Wedge(xy, r, mid, start + 360.0, facecolor=c_post,
                           edgecolor=edgecolor, linewidth=linewidth, alpha=alpha))

# -------------------------
# 6) main plot (NO title, NO legend)
# -------------------------
def plot_overlay_disk_pie_main(pre_json, post_json, pre_matrix_csv, post_matrix_csv,
                               out_png="overlay_disk_pie.png",
                               disk_R=1.0, disk_margin=0.08,
                               edge_alpha=0.18, edge_width=0.8,
                               node_alpha=0.92,
                               pie_gap_deg=0.0,
                               size_mode="sqrt",
                               r_min=0.010, r_max=0.060):
    G_pre  = load_graph(pre_json)
    G_post = load_graph(post_json)

    # union graph
    G_union = nx.Graph()
    G_union.add_nodes_from(G_pre.nodes(data=True))
    G_union.add_edges_from(G_pre.edges(data=True))
    G_union.add_nodes_from(G_post.nodes(data=True))
    G_union.add_edges_from(G_post.edges(data=True))

    # clone sizes
    clone_pre  = load_clone_sizes(G_pre,  pre_matrix_csv)
    clone_post = load_clone_sizes(G_post, post_matrix_csv)

    # node sets
    pre_nodes  = set(G_pre.nodes())
    post_nodes = set(G_post.nodes())
    both_nodes = pre_nodes & post_nodes
    pre_only   = pre_nodes - post_nodes
    post_only  = post_nodes - pre_nodes

    # ONE pos -> disk
    pos = normalize_to_disk(unified_layout_union(G_union), R=disk_R, margin=disk_margin)

    # node radius scale: pre+post global max
    total_clone = {n: clone_pre.get(n, 0.0) + clone_post.get(n, 0.0) for n in G_union.nodes()}
    vmax = max(total_clone.values(), default=1e-9)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_aspect("equal")
    ax.set_axis_off()

    # disk boundary
    disk = Circle((0, 0), disk_R, facecolor="white", edgecolor=C_DISK_EDGE, linewidth=1.2)
    ax.add_patch(disk)

    # edges (clip to disk)
    edge_artists = nx.draw_networkx_edges(G_union, pos, ax=ax,
                                          alpha=edge_alpha, width=edge_width, edge_color=C_EDGE)
    try:
        edge_artists.set_clip_path(disk)
    except Exception:
        if isinstance(edge_artists, list):
            for a in edge_artists:
                try:
                    a.set_clip_path(disk)
                except Exception:
                    pass

    # pre_only: blue filled
    if pre_only:
        nodes = list(pre_only)
        rads = radius_map([total_clone[n] for n in nodes], vmax, r_min=r_min, r_max=r_max, mode=size_mode)
        for n, rr in zip(nodes, rads):
            ax.add_patch(Circle(pos[n], rr, facecolor=C_PRE_ONLY, edgecolor="none", alpha=node_alpha))

    # post_only: red filled
    if post_only:
        nodes = list(post_only)
        rads = radius_map([total_clone[n] for n in nodes], vmax, r_min=r_min, r_max=r_max, mode=size_mode)
        for n, rr in zip(nodes, rads):
            ax.add_patch(Circle(pos[n], rr, facecolor=C_POST_ONLY, edgecolor="none", alpha=node_alpha))

    # both: pie split
    if both_nodes:
        nodes = list(both_nodes)
        rads = radius_map([total_clone[n] for n in nodes], vmax, r_min=r_min, r_max=r_max, mode=size_mode)
        for n, rr in zip(nodes, rads):
            draw_pie_node(ax, pos[n], rr,
                          clone_pre.get(n, 0.0), clone_post.get(n, 0.0),
                          alpha=0.95, gap_deg=pie_gap_deg)

    # tight view only disk
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)

    plt.savefig(out_png, dpi=300, bbox_inches="tight", transparent=False)
    plt.close()
    print("saved main:", out_png)

# -------------------------
# 7) legend A: circle size 1-6 (standalone image)
# -------------------------
def save_legend_circle_sizes(out_png="legend_circle_size_1_6.png",
                             r_min=0.010, r_max=0.060,
                             labels=(1,2,3,4,5,6),
                             figsize=(3.5, 1.2)):

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal")
    ax.set_axis_off()

    xs = np.linspace(0.10, 0.90, len(labels))
    y = 0.50

    # 线性映射 1..6 -> 半径
    labs = np.array(labels, dtype=float)
    xnorm = (labs - labs.min()) / (labs.max() - labs.min() + 1e-12)
    rs = r_min + xnorm * (r_max - r_min)

    for x, r, lab in zip(xs, rs, labels):
        ax.add_patch(Circle((x, y), r, facecolor="#666666", edgecolor="none", alpha=0.95))
        ax.text(x, y - 0.22, str(lab), ha="center", va="top", fontsize=9)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    plt.savefig(out_png, dpi=300, bbox_inches="tight", transparent=True)
    plt.close()
    print("saved legend(size):", out_png)

# -------------------------
# 8) legend B: node type (post-only + pre&post pie) standalone
# -------------------------
def save_legend_node_types(out_png="legend_node_types_postonly_pie.png",
                           r=0.10, figsize=(3.8, 1.3),
                           pie_pre_frac=0.5):

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal")
    ax.set_axis_off()

    # positions in a simple 0..1 canvas
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # post-only
    x1, y1 = 0.18, 0.55
    ax.add_patch(Circle((x1, y1), r, facecolor=C_POST_ONLY, edgecolor="none", alpha=0.95))
    ax.text(0.33, y1, "Post-only", ha="left", va="center", fontsize=10)

    # pre&post pie
    x2, y2 = 0.18, 0.20
    pre_val = pie_pre_frac
    post_val = 1.0 - pie_pre_frac
    draw_pie_node(ax, (x2, y2), r, pre_val=pre_val, post_val=post_val,
                  alpha=0.95, gap_deg=0.0)
    ax.text(0.33, y2, "Pre & Post (pie split)", ha="left", va="center", fontsize=10)

    plt.savefig(out_png, dpi=300, bbox_inches="tight", transparent=True)
    plt.close()
    print("saved legend(type):", out_png)

# -------------------------
# 9) usage
# -------------------------
gene = "TRAV13-1;TRAJ36"
pre_json  = f"./networkText/Pre/{gene}.json"
post_json = f"./networkText/Post/{gene}.json"
pre_matrix_csv  = f"./Matrix/Pre/{gene}.csv"
post_matrix_csv = f"./Matrix/Post/{gene}.csv"

# main figure (no title/legend)
plot_overlay_disk_pie_main(
    pre_json, post_json, pre_matrix_csv, post_matrix_csv,
    out_png=f"./network_plot_{gene}_overlay_disk_pie.pdf"
)

# legends as standalone images
save_legend_circle_sizes(out_png="./legend_circle_size_1_6.pdf",
                         r_min=0.010, r_max=0.060, labels=(1,2,3,4,5,6))

save_legend_node_types(out_png="./legend_node_types_postonly_pie.pdf",
                       r=0.10, pie_pre_frac=0.5)