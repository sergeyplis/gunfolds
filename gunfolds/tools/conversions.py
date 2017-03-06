""" This module contains graph format conversion functions """
import gmpy as gmp
import igraph
import networkx as nx
import numpy as np
import scipy


def g2num(g):
    """ Convert a graph into a binary format """
    n = len(g)
    n2 = n ** 2 + n
    num = 0
    for v in range(1, n + 1):
        for w in g[v]:
            num |= (1 << (n2 - v * n - w))
    return num


def ug2num(g):
    """ Convert non-empty edges into a tuple of (directed, bidriected) in binary format """
    n = len(g)
    n2 = n ** 2 + n
    num = 0
    mask = 0
    num2 = 0
    for v in g:
        for w in g[v]:
            if g[v][w] in (1, 3):
                mask = (1 << (n2 - v * n - w))
                num |= mask
            if g[v][w] in (2, 3):
                num2 |= mask
    return num, num2


def bg2num(g):
    """ Convert bidirected edges into a binary format """
    n = len(g)
    n2 = n ** 2 + n
    num = 0
    for v in g:
        for w in g[v]:
            if g[v][w] in (2, 3):
                num = num | (1 << (n2 - v * n - w))
    return num


def graph2nx(G):
    g = nx.DiGraph()
    for v in G:
        g.add_edges_from([(v, x) for x in G[v] if G[v][x] in (1, 3)])
    return g


def nx2graph(G):
    g = {n: {} for n in G}
    for n in G:
        g[n] = {x: 1 for x in G[n]}
    return g


def num2CG(num, n):
    """num2CG - converts a number  whose binary representaion encodes edge
    presence/absence into a compressed graph representaion

    """
    n2 = n * n
    G = {i + 1: {} for i in xrange(n)}
    if num == 0:
        return G
    bl = gmp.bit_length(num)
    idx = [n2 - i - 1 for i in xrange(bl) if num & (1 << i)]
    idx = np.unravel_index(idx, (n, n))
    x = idx[0] + 1
    y = idx[1] + 1
    for i in xrange(len(x)):
        G[x[i]][y[i]] = 1
    return G


def dict_format_converter(H):
    """ Convert a graph from the set style dictionary format to the integer style

        >>> test = {'1': {'1': {(0, 1)},
        ...   '2': {(0, 1), (2, 0)},
        ...   '3': {(0, 1), (2, 0)},
        ...   '4': {(2, 0)},
        ...   '5': {(0, 1)}},
        ...  '2': {'1': {(2, 0)}, '2': {(0, 1)}, '5': {(0, 1), (2, 0)}},
        ...  '3': {'1': {(0, 1), (2, 0)}, '2': {(0, 1)}, '5': {(0, 1)}},
        ...  '4': {'1': {(2, 0)},
        ...   '2': {(0, 1)},
        ...   '3': {(0, 1)},
        ...   '4': {(0, 1)},
        ...   '5': {(0, 1)}},
        ...  '5': {'1': {(0, 1)}, '2': {(0, 1), (2, 0)}, '5': {(0, 1)}}}
        >>> dict_format_converter(test)
        {1: {1: 1, 2: 3, 3: 3, 4: 2, 5: 1}, 2: {1: 2, 2: 1, 5: 3}, 3: {1: 3, 2: 1, 5: 1}, 4: {1: 2, 2: 1, 3: 1, 4: 1, 5: 1}, 5: {1: 1, 2: 3, 5: 1}}
        >>>
    """
    H_new = {}
    for vert_a in H:
        H_new[int(vert_a)] = {}
        for vert_b in H[vert_a]:
            edge_val = 0
            if (0, 1) in H[vert_a][vert_b]:
                edge_val = 1
            if (2, 0) in H[vert_a][vert_b]:
                edge_val = 2 if edge_val == 0 else 3
            if edge_val:
                H_new[int(vert_a)][int(vert_b)] = edge_val
    return H_new


#### Adjacency matrix functions

def graph2adj(G):
    """ Convert the directed edges to an adjacency matrix """
    n = len(G)
    A = scipy.zeros((n, n), dtype=np.int8)
    for v in G:
        A[int(v) - 1, [int(w)-1 for w in G[v] if G[v][w] in (1,3)]] = 1
    return A


def graph2badj(G):
    """ Convert the bidirected edges to an adjacency matrix """
    n = len(G)
    A = scipy.zeros((n, n), dtype=np.int8)
    for v in G:
        A[int(v) - 1, [int(w)-1 for w in G[v] if G[v][w] in (2,3)]] = 1
    return A


def adjs2graph(directed, bidirected):
    """ Convert an adjacency matrix of directed and bidirected edges to a graph """
    G = {i:{} for i in xrange(1, directed.shape[0] + 1)}
    for i in xrange(directed.shape[0]):
        for j in np.where(directed[i,:] == 1)[0] + 1:
            G[i + 1][j] = 1

    for i in xrange(bidirected.shape[0]):
        for j in xrange(bidirected.shape[1]):
            if bidirected[i, j] and j != i:
                if j + 1 in G[i + 1]:
                    G[i + 1][j + 1] = 3
                else:
                    G[i + 1][j + 1] = 2
    return G


def g2vec(g):
    A = graph2adj(g)
    B = graph2badj(g)
    return np.r_[A.flatten(), B[np.triu_indices(B.shape[0])]]


def vec2adj(v, n):
    A = np.zeros((n, n))
    B = np.zeros((n, n))
    A[:] = v[:n ** 2].reshape(n, n)
    B[np.triu_indices(n)] = v[n ** 2:]
    B = B + B.T
    return A, B


def vec2g(v, n):
    A, B = vec2adj(v, n)
    return adjs2graph(A, B)


def g2ig(g):
    """
    Converts our graph represenataion to an igraph for plotting
    """
    t = scipy.where(graph2adj(g) == 1)
    l = zip(t[0], t[1])
    ig = igraph.Graph(l, directed=True)
    ig.vs["name"] = scipy.sort([u for u in g])
    ig.vs["label"] = ig.vs["name"]
    return ig