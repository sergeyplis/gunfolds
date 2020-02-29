import sys, os
import sys, os

sys.path.append('./tools/')
import traversal as trv
import bfutils as bfu
import graphkit as gk
import numpy as np
from random import shuffle
import ecj
from copy import deepcopy
from pathtree import PathTree, osumset
import ipdb


def g2lg(g):
    """
    Convert a data structure encoding the MSL-type graph into a structure encoding latents graph
    :return: a graph with integer indices and sets as weights

    Args:
        g (MSL-graph): 
    """
    edge_type = {(0, 1): 1, (2, 0): 2}
    edge_weight = {(0, 1): 1, (2, 0): 0}
    lg = {int(e): {int(c): {edge_type[w]: {edge_weight[w]}
                            for w in g[e][c]}
                   for c in g[e]}
          for e in g}
    return fix_selfloops(lg)


def fix_selfloops(g):
    for v in g:
        if v in g[v]:
            g[v][v] = {1: {PathTree({1})}}
    return g


def gtranspose(G):  # Transpose (rev. edges of) G
    GT = {u: {} for u in G}
    for u in G:
        for v in G[u]:
            if 1 in G[u][v]:
                GT[v][u] = {1: {1}}  # Add all reverse edges
    return GT


def parents(g, N):  # an inefficient way to do it
    t = gtranspose(g)  # Transpose the graph
    return {n: g[n][N][1]
            for n in t[N] if n != N}  # Return all children


def children(g, N):
    return {n: g[N][n][1]
            for n in g[N] if n != N}


def remove_node(g, N):
    del g[N]
    for V in g:
        if N in g[V]:
            del g[V][N]


def iterate_ws(ws):
    starts = []
    for e in ws:
        if type(e) is int:
            starts.append(e)
            continue
        if type(e) is set:
            starts.extend(list(e))
            continue
        starts.append(e.preset)
        starts.append([e.preset, iterate_ws(e.loopset)])
    return starts


def iterate_pt(pt):  # iterate over a path tree
    starts = [pt.preset]
    for e in pt.loopset:
        if type(e) is int:
            starts.append(e)
            continue
        if type(e) is set:
            starts.extend(list(e))
            continue
        starts.append(e.preset)
        starts.append([e.preset, iterate_ws(e.loopset)])
    return starts


def merge_weightsets(ab, ah, hb, hh):
    ws = osumset(ah, hb)
    if hh:
        ws = osumset(ws, hh)
    if not type(ws) is set:
        ws = {ws}
    return ws.union(ab)


def hide_node(g, H):
    """
    Removes a node from a graph taking care of the edges and weights as if the node was not observed
    :param g: input graph
    :param H: node to hide
    :return: the graph
    """

    gg = deepcopy(g)

    if not H in g:
        raise KeyError
    ch = children(g, H)
    pa = parents(g, H)
    if H in g[H]:
        sl = g[H][H][1]
    else:
        sl = set()
    remove_node(gg, H)

    for p in pa:
        for c in ch:
            if c in gg[p]:
                ab = gg[p][c][1]  # self loop
            else:
                ab = set()
            w = merge_weightsets(ab, pa[p], ch[c], sl)  # new weight set
            if c == p:  # a new loop is forming
                w = {PathTree(w)}
            gg[p][c] = {1: w}

    return gg


def degrees(nodes, g):
    return [len(parents(g, v)) + len(children(g, v)) for v in nodes]


def sortbydegree(nodes, g):
    idx = np.argsort(degrees(nodes, g))
    return list(np.asarray(nodes)[idx])


def hide_nodes(g, nodelist, dosort=True):
    nodeset = set()  # make sure not to delete a node twice
    if dosort: nodelist = sortbydegree(nodelist, g)
    gg = deepcopy(g)
    for n in nodelist:
        if n in nodeset: continue
        gg = hide_node(gg, n)
        nodeset.add(n)
    return gg


def hide_random(g, ratio):
    """
    Hire random modes in the `ratio` proportion from graph g
    :param g: input graph
    :param ratio: what percentage of nodes to hide
    :return: the graph with hidden variables
    """
    nodes = g.keys()
    shuffle(nodes)
    return hide_nodes(g, nodes[:int(len(g) * ratio)])


def print_ws(ws):
    print '{',
    for e in ws:
        print e, ', ',
    print '}'


def test_osumnum():
    assert osumnum(set(range(5)), 1) == set(range(1, 5 + 1))


def testcase(n):
    g1 = {1: {2: {1: {1}}, 4: {1: {1}}},
          2: {3: {1: {1}}, 7: {1: {1}}},
          3: {},
          4: {5: {1: {1}}},
          5: {3: {1: {1}}, 6: {1: {1}}},
          6: {5: {1: {1}}},
          7: {8: {1: {1}}},
          8: {2: {1: {1}}}}

    g2 = {1: {2: {1: {1}}},
          2: {3: {1: {1}}, 6: {1: {1}}},
          3: {4: {1: {1}}},
          4: {5: {1: {1}}},
          5: {},
          6: {7: {1: {1}}},
          7: {3: {1: {1}}}}

    g3 = {1: {2: {1: {1}}},
          2: {3: {1: {1}}, 6: {1: {1}}},
          3: {4: {1: {1}}, 8: {1: {1}}},
          4: {5: {1: {1}}},
          5: {},
          6: {7: {1: {1}}},
          7: {2: {1: {1}}},
          8: {9: {1: {1}}},
          9: {10: {1: {1}}},
          10: {11: {1: {1}}},
          11: {3: {1: {1}}}}

    g4 = {1: {2: {1: {1}}},
          2: {3: {1: {1}}, 4: {1: {1}}},
          4: {5: {1: {1}}},
          5: {6: {1: {1}}, 7: {1: {1}}},
          6: {2: {1: {1}}},
          7: {8: {1: {1}}},
          8: {5: {1: {1}}},
          3: {}}

    g5 = {1: {2: {1: {1}}},
          2: {3: {1: {1}}, 4: {1: {1}}},
          4: {5: {1: {1}}},
          5: {6: {1: {1}}, 7: {1: {1}}},
          6: {2: {1: {1}}},
          7: {8: {1: {1}}},
          8: {5: {1: {1}}},
          3: {9: {1: {1}}},
          9: {10: {1: {1}}, 11: {1: {1}}},
          11: {9: {1: {1}}},
          10: {}}

    g6 = {1: {2: {1: {1}}},
          2: {3: {1: {1}}, 4: {1: {1}}},
          4: {5: {1: {1}}},
          5: {6: {1: {1}}, 7: {1: {1}}},
          6: {2: {1: {1}}, 6: {1: {1}}},
          7: {8: {1: {1}}},
          8: {5: {1: {1}}},
          3: {9: {1: {1}}},
          9: {10: {1: {1}}, 11: {1: {1}}},
          11: {9: {1: {1}}},
          10: {}}

    g7 = {1: {2: {1: {1}}},
          2: {3: {1: {1}}, 4: {1: {1}}},
          4: {5: {1: {1}}},
          5: {6: {1: {1}}, 7: {1: {1}}},
          6: {2: {1: {1}}, 6: {1: {1}}},
          7: {8: {1: {1}}, 7: {1: {1}}},
          8: {5: {1: {1}}},
          3: {9: {1: {1}}},
          9: {10: {1: {1}}, 11: {1: {1}}},
          11: {9: {1: {1}}},
          10: {}}

    g8 = {1: {2: {1: {1}}, 5: {1: {1}}},
          2: {3: {1: {1}}, 2: {1: {1}}},
          3: {4: {1: {1}}},
          4: {8: {1: {1}}},
          5: {6: {1: {1}}},
          6: {7: {1: {1}}},
          7: {4: {1: {1}}},
          8: {9: {1: {1}}},
          9: {9: {1: {1}}, 10: {1: {1}}},
          10: {}}

    cases = [g1, g2, g3, g4, g5, g6, g7, g8]

    return fix_selfloops(cases[n])
