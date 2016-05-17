import graph_tool as gt

def lg2gt(g):
    gr = gt.Graph()
    vlabel = gr.new_vertex_property("string")
    verts = {}
    edges = {}
    for v in g:
        verts[v] = gr.add_vertex()
        vlabel[verts[v]] = str(v)
    gr.vertex_properties["label"] = vlabel
    for v in g:
        for w in g[v]:
            edges[(v,w)] = gr.add_edge(verts[v], verts[w])
    return gr

def plotg(g):
    gg = lg2gt(g)
    pos = gt.all.sfdp_layout(gg)
    gt.all.graph_draw(gg, pos,
               vertex_text=gg.vertex_properties['label'],
               vertex_font_size=32,
               edge_pen_width=5,
               vertex_fill_color=[0.62109375,  0.875     ,  0.23828125, 1])

# from graph_tool.all import sfdp_layout, graph_draw
# gg = gr
# pos = sfdp_layout(gr)
#  graph_draw(gg, pos, vertex_text=gg.vertex_properties['label'], vertex_font_size=18, edge_pen_width=2.5)