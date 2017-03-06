# tools to construct (random) graphs
from gunfolds.tools.conversions import nx2graph, graph2adj
from gunfolds.tools import ecj
from itertools import combinations
import networkx as nx
import numpy as np
from numpy.random import randint
import random as std_random



def edgelist(g):  # directed
    '''
    return a list of tuples for edges of g
    '''
    l = []
    for n in g:
        l.extend([(n, e) for e in g[n] if g[n][e] in (1, 3)])
    return l


def inedgelist(g):  # missing directed iterator
    '''
    iterate over the list of tuples for edges of g
    '''
    n = len(g)
    for v in g:
        for i in xrange(1, n + 1):
            if not i in g[v]:
                yield (v, i)
            elif g[v][i] not in (1, 3):
                yield (v, i)


def inbedgelist(g):  # missing bidirected iterator
    '''
    iterate over the list of tuples for edges of g
    '''
    for v in g:
        for w in g:
            if v != w:
                if not w in g[v]:
                    yield (v, w)
                elif g[v][w] not in (2, 3):
                    yield (v, w)


def bedgelist(g):
    """ bidirected edge list with flips """
    l = []
    for n in g:
        l.extend([tuple(sorted((n, e))) for e in g[n] if g[n][e] in (2, 3)])
    l = list(set(l))
    l = l + map(lambda x: (x[1], x[0]), l)
    return l


def superclique(n):
    """ All possible edges """
    g = {}
    for i in range(n):
        g[i + 1] = {j + 1: 3 for j in range(n) if j != i}
        g[i + 1][i + 1] = 1
    return g


def complement(G):
    """ return the complement of G """
    n = len(G)
    sq = superclique(n)
    for v in G:
        for w in G[v]:
            sq[v][w] = sq[v][w] - G[v][w]
            if sq[v][w] == 0:
                del sq[v][w]
    return sq


def gtranspose(G):
    """ Transpose (rev. edges of) G """
    GT = {u: {} for u in G}
    for u in G:
        for v in G[u]:
            if G[u][v] in (1,3):
                GT[v][u] = 1        # Add all reverse edges
    return GT


def scale_free(n, alpha=0.7, beta=0.25,
               delta_in=0.2, delta_out=0.2):
    g = nx.scale_free_graph(n, alpha=alpha,
                            beta=beta,
                            delta_in=delta_in, delta_out=delta_out)
    g = nx2graph(g)
    g = gtranspose(g)
    addAring(g)
    return g


def randH(n, d1, d2):
    """ Generate a random H with n nodes """
    g = ringmore(n, d1)
    pairs = [x for x in combinations(g.keys(), 2)]
    for p in np.random.permutation(pairs)[:d2]:
        g[p[0]][p[1]] = g[p[0]].get(p[1], 0) + 2
        g[p[1]][p[0]] = g[p[1]].get(p[0], 0) + 2
    return g


def ring(n, permute=False):
    g = {}
    names = [x+1 for x in range(n)]
    if permute:
        names = np.random.permutation(names) 
    for i in range(n-1):
        g[names[i]] = {names[i+1]: 1}
    g[names[n-1]] = {names[0]: 1}
    return g


def addAring(g):
    """ Add a ring to g in place """
    for i in range(1, len(g)):
        if g[i].get(i + 1) == 2:
            g[i][i + 1] = 3
        else:
            g[i][i + 1] = 1
    if g[i].get(1) == 2:
        g[i][1] = 3
    else:
        g[i][1] = 1


def upairs(n, k):
    '''
    n unique nonsequential pairs
    '''
    s = set()
    for p in randint(n, size=(3 * k, 2)):
        if p[1] - p[0] == 1:
            continue
        s.add(tuple(p))
    return list(s)[:k]


def ringarcs(g, n):
    for edge in upairs(len(g), n):
        g[edge[0] + 1][edge[1] + 1] = 1
    return g


def ringmore(n, m, permute=False):
    return ringarcs(ring(n,permute=permute), m)


def digonly(H):
    """returns a subgraph of H contatining all directed edges of H

    Arguments:
    - `H`: undersampled graph
    """
    g = {n: {} for n in H}
    for v in g:
        g[v] = {w: 1 for w in H[v] if not H[v][w] == 2}
    return g


def OCE(g1, g2):
    '''
    omission/commision error of g1 referenced to g2
    '''
    s1 = set(edgelist(g1))
    s2 = set(edgelist(g2))
    omitted = len(s2 - s1)
    comitted = len(s1 - s2)

    s1 = set(bedgelist(g1))
    s2 = set(bedgelist(g2))
    bomitted = len(s2 - s1)
    bcomitted = len(s1 - s2)

    return {'directed': (omitted, comitted),
            'bidirected': (bomitted, bcomitted)}


def clean_leaf_nodes(g):
    for v in g:
        g[v] = {w: g[v][w] for w in g[v] if g[v][w] > 0}


def cerror(d):
    return d['OCE']['directed'][1] / np.double(len(d['gt']['graph']) ** 2 - len(edgelist(d['gt']['graph'])))


def oerror(d):
    return d['OCE']['directed'][0] / np.double(len(edgelist(d['gt']['graph'])))


def bidirected_no_fork(g):
    be = bedgelist(g)
    T = gtranspose(g)
    for e in be:
        if not set(T[e[0]].keys()) & set(T[e[1]].keys()):
            return True
    return False


def no_parents(g):
    T = gtranspose(g)
    for n in T:
        if not T[n]:
            return True
    return False


def no_children(g):
    for n in g:
        if not g[n]:
            return True
    return False


def scc_unreachable(g):
    if bidirected_no_fork(g):
        return True
    if no_parents(g):
        return True
    if no_children(g):
        return True
    return False

# unlike functions from traversal package these do no checking


def addanedge(g, e):
    g[e[0]][e[1]] = 1


def delanedge(g, e):
    g[e[0]].pop(e[1], None)


def addedges(g, es):
    for e in es:
        addanedge(g, e)


def deledges(g, es):
    for e in es:
        delanedge(g, e)


def isdedgesubset(g2star, g2):
    '''
    check if g2star directed edges are a subset of those of g2
    '''
    for n in g2star:
        for h in g2star[n]:
            if h in g2[n]:
                # if g2star has a directed edge and g2 does not
                if g2star[n][h] in (1,3) and g2[n][h] == 2:
                    return False
            else:
                return False
    return True


def isedgesubset(g2star, g2):
    '''
    check if all g2star edges are a subset of those of g2
    '''
    for n in g2star:
        for h in g2star[n]:
            if h in g2[n]:
                # Everything is a subset of 3 (both edge types)
                if g2[n][h] != 3:
                    # Either they both should have a directed edge, or
                    # both should have a bidirected edge
                    if g2star[n][h] != g2[n][h]:
                        return False
            else:
                return False
    return True
