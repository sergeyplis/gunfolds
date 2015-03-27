#BFS implementation of subgraph and supergraph
#Gu to G1 algorithm
from itertools import combinations
from functools import wraps
import copy
import time
import sys,os
import numpy as np
import ipdb
from progressbar import ProgressBar, Percentage, \
    Bar, RotatingMarker, ETA, FileTransferSpeed

TOOLSPATH='./tools/'
sys.path.append(os.path.expanduser(TOOLSPATH))

import bfutils as bfu
import traversal as trv
import graphkit as gk
import comparison as cmp

def memo(func):
    cache = {}                        # Stored subproblem solutions
    @wraps(func)                      # Make wrap look like func
    def wrap(*args):                  # The memoized wrapper
        s = trv.gsig(args[0])         # Signature: just the g
        #s = tool.signature(args[0],args[2])# Signature: g and edges
        if s not in cache:            # Not already computed?
            cache[s] = func(*args)    # Compute & cache the solution
        return cache[s]               # Return the cached solution
    return wrap

def prune_conflicts(H, g, elist):
    """checks if adding an edge from the list to graph g causes a
    conflict with respect to H and if it does removes the edge
    from the list

    Arguments:
    - `H`: the undersampled graph
    - `g`: a graph under construction
    - `elist`: list of edges to check
    """
    l  = []
    for e in elist:
        gk.addanedge(g,e)
        if not bfu.call_u_conflicts(g, H): l.append(e)
        gk.delanedge(g,e)
    return l

def eqclass(H):
    '''
    Find all graphs in the same equivalence class with respect to
    graph H and any undesampling rate.
    '''
    g = {n:{} for n in H}
    s = set()

    @memo
    def addedges(g,H,edges):
        if edges:
            nedges = prune_conflicts(H, g, edges)
            n = len(nedges)

            if n == 0: return None

            for i in range(n):
                gk.addanedge(g,nedges[i])
                if bfu.call_u_equals(g, H): s.add(bfu.g2num(g))
                s.add(addedges(g,H,nedges[:i]+nedges[i+1:]))
                gk.delanedge(g,nedges[i])

    edges = gk.edgelist(gk.complement(g))
    addedges(g,H,edges)
    return s-set([None])

# these two functions come fromt his answer:
# http://stackoverflow.com/a/12174125
def set_bit(value, bit): return value | (1<<bit)
def clear_bit(value, bit): return value & ~(1<<bit)
def e2num(e,n): return (1<<(n*n +n - int(e[0],10)*n - int(e[1],10)))
def le2num(elist,n):
    num = 0
    for e in elist:
        num |= e2num(e,n)
    return num
def ekey2e(ekey,n):
    idx = np.unravel_index(n*n - ekey .bit_length() - 1 + 1,(n,n))
    idx = tuple([x+1 for x in idx])
    return ('%i %i'%idx).split(' ')

def cacheconflicts(num, cache):
    """Given a number representation of a graph and an iterable of
    conflicting subgraphs return True if the graph conflicts with any
    of them and false otherwise

    Arguments:
    - `num`: the number representation of a graph
    - `cache`: an iterable of number representations of conflicting graphs
    """
    conflict = False
    for c in cache:
        if num & c == c:
            return True
    return False

def add2set_(ds, H, cp, iter=1):
    n = len(H)
    n2 = n*n +n
    dsr = {}
    s = set()
    ss = set()
    pbar = ProgressBar(widgets=['%3s' % str(iter) +'%10s' % str(len(ds))+' ',
                                Bar(), ' '], maxval=len(ds.keys())).start()
    c = 0
    for gnum in ds:
        g = bfu.num2CG(gnum, n)
        gnum = bfu.g2num(g)
        c += 1
        pbar.update(c)
        glist = []
        elist = []
        eset = set()
        for e in ds[gnum]:
            if not e[1] in g[e[0]]:
                ekey = (1<<(n2 - int(e[0],10)*n - int(e[1],10)))
                if ekey in cp and cacheconflicts(gnum,cp[ekey]): continue

                gk.addanedge(g,e)
                num = bfu.g2num(g)
                if not num in s:                    
                    if not bfu.call_u_conflicts(g, H):
                        glist.append((num,ekey))
                        elist.append(e)
                        eset.add(ekey)
                        s.add(num)
                        if bfu.call_u_equals(g, H): ss.add(num)
                gk.delanedge(g,e)

        for gn,e in glist:
            if e in cp:
                dsr[gn] = [ekey2e(k,n) for k in eset - cp[e]]
            else:
                dsr[gn] = elist
    pbar.finish()
    return dsr, ss

def confpairs(H):
    n = len(H)
    g = {n:{} for n in H}
    d = {}

    edges = gk.edgelist(gk.complement(g))
    edges = prune_conflicts(H, g, edges)

    for p in combinations(edges,2):
        gk.addedges(g,p)
        if bfu.call_u_conflicts(g, H):
            n1 = e2num(p[0],n)
            n2 = e2num(p[1],n)
            d.setdefault(n1,set()).add(n2)
            d.setdefault(n2,set()).add(n1)
        gk.deledges(g,p)

    return d


def iteqclass(H):
    '''
    Find all graphs in the same equivalence class with respect to
    graph H and any undesampling rate.
    '''
    if cmp.isSclique(H):
        print 'not running on superclique'
        return None
    g = {n:{} for n in H}
    s = set()
    Hnum = bfu.ug2num(H)
    if Hnum[1]==0: s.add(Hnum[0])

    cp = confpairs(H)

    edges = gk.edgelist(gk.complement(g))

    ds = {bfu.g2num(g): edges}

    print '%3s'%'i'+'%10s'%' graphs'
    for i in range(len(H)**2):
        ds, ss = add2set_(ds, H, cp, iter=i)
        s = s | ss
        if not ds: break

    return s

def getrates(g,H):
    n = len(H)
    au = bfu.call_undersamples(g)
    return list(np.where(map(lambda x: x == H, au))[0])

def withrates(s,H):
    n = len(H)
    d = {g:set() for g in s}
    for g in s:
        d[g] = getrates(bfu.num2CG(g,n),H)
    return d

def add2set(gset, elist, H):
    n = len(H)

    s = set()
    ss = set()

    eremove = {e: True for e in elist}

    for gnum in gset:
        g = bfu.num2CG(gnum, n)
        for e in elist:
            if not e[1] in g[e[0]]:
                gk.addanedge(g,e)
                num = bfu.g2num(g)
                if not num in s:
                    au = bfu.call_undersamples(g)
                    if not gk.checkconflict(H, g, au=au):
                        eremove[e] = False
                        s.add(num)
                        if gk.checkequality(H, g, au=au): ss.add(num)
                gk.delanedge(g,e)

    for e in eremove:
        if eremove[e]: elist.remove(e)

    return s, ss, elist

def eqclass_list(H):
    '''
    Find all graphs in the same equivalence class with respect to
    graph H and any undesampling rate.
    '''
    g = {n:{} for n in H}
    s = set()

    edges = gk.edgelist(gk.complement(g))
    #edges = prune_conflicts(H, g, edges)

    gset = set([bfu.g2num(g)])
    for i in range(len(H)**2):
        print i
        gset, ss, edges = add2set(gset, edges, H)
        s = s | ss
        if not edges: break

    return s

def main():
    g = bfu.ringmore(6,1);
    H = bfu.undersample(g,1);
    ss = iteqclass(H)
    print ss

if __name__ == "__main__":
    main()
