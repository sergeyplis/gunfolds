from gunfolds.tools.conversions import num2CG, graph2nx, nx2graph
from gunfolds.tools.bfutils import undersample
from gunfolds.tools import ecj
#import gmpy as gmp
import networkx as nx
import numpy as np
import operator
import scipy

np.random.RandomState()


def has_self_loops(G):
    for u in G:
        if G[u].has_key(u):
            return True
    return False


def randSCC(n):
    G = num2CG(scipy.random.randint(2 ** (n ** 2)), n)
    while (len(ecj.scc(G)) > 1) or gcd4scc(G) > 1:
        G = num2CG(scipy.random.randint(2 ** (n ** 2)), n)
    return G


def SM_fixed(Gstar, G, iter=5):
    compat = []
    for j in range(0, iter):
        if Gstar == undersample(G, j):
            compat.append(j)
    return compat


def SM_converging(Gstar, G):
    """Gstar is the undersampled reference graph, while G is the starting
    graph. The  code searches  over all undersampled  version of  G to
    find all matches with Gstar
    """
    compat = []
    GG = G
    Gprev = G
    if G == Gstar:
        return [0]
    j = 1
    G = undersample(GG, j)
    while not (G == Gprev):
        if Gstar == G:
            compat.append(j)
        j += 1
        Gprev = G
        G = undersample(GG, j)
    return compat


def search_match(Gstar, G, iter=5):
    if gcd4scc(G) > 1:
        return SM_fixed(Gstar, G, iter=iter)
    return SM_converging(Gstar, G)


def has_sink(G):
    return not reduce(operator.and_, [bool(G[n]) for n in G], True)


def has_root(G):
    return has_sink(ecj.tr(G))


def gcd4scc(SCC):
    g = graph2nx(SCC)
    return ecj.listgcd(map(lambda x: len(x) - 1, nx.simple_cycles(g)))


def compatible_at_u(uGstar):
    compat = []
    n = len(uGstar)
    numG = 2 ** (n ** 2)
    # pbar = Percentage()
    for i in range(1, numG):
        G = num2CG(i, n)
        # pbar.update(i+1)
        if len(ecj.scc(G)) > 1:
            continue
        l = search_match(uGstar, G, iter=5)
        if l:
            compat.append((l, G))
    # pbar.finish()
    return compat
