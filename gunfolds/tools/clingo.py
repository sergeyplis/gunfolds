""" This module contains clingo interaction functions """
from __future__ import print_function

import subprocess
from subprocess import CalledProcessError
import sys, os
import numpy as np
from gunfolds.tools import bfutils as bfu
import ipdb


CLINGOPATH=''
CAPSIZE=1000
THREADS=''

def rate(u, file=sys.stdout):
    s = """
% Define a range of u:s
%urange(1..2).
% u(U) is true for only one U
% in the range defined above
%1 { u(U): urange(U) } 1.
    """ + "u("+str(u)+")."
    print(s, file=file)

def uprogram(file=sys.stdout):
    s = """
% Input to this program:
% edgeu = edges in GU
% confu = bidirected edges in GU
% u = known u, if there is one
% node(1..n)
% edge1 = edge in the learned graph G1
% Guess edge1:s
{ edge1(X,Y) } :- node(X),node(Y).
% For now there are no confs
% Derive all edges up to length U of G1
edge(X,Y,1) :- edge1(X,Y).
edge(X,Y,L) :- edge(X,Z,L-1),edge1(Z,Y),
L <= U, u(U).
% Edges of length U,
% are edgeu:s of the learning result
derived_edgeu(X,Y) :- edge(X,Y,L), u(L).
% Find the confus that would show up for the G1
% Only considered when X < Y here
derived_confu(X,Y) :- edge(Z,X,L), edge(Z,Y,L),
node(X),node(Y),node(Z),
X < Y, L < U, u(U).
% Check that derived edgeu:s
% match the input edgeu:s
:- edgeu(X,Y), not derived_edgeu(X,Y),
node(X),node(Y).
:- not edgeu(X,Y), derived_edgeu(X,Y),
node(X),node(Y).
% Check that derived confus
% match the input confu
:- derived_confu(X,Y), not confu(X,Y),
node(X),node(Y), X < Y.
:- not derived_confu(X,Y), confu(X,Y),
node(X),node(Y), X < Y.
% Only show edge1 and u variables
#show.
#show edge1/2.
#show u/1.
    """
    print(s, file=file)

def g2clingo(g, file=sys.stdout):
    """ Save a graph to a file of grounded terms for clingo """
    n = len(g)
    print('node(1..'+str(n)+').', file=file)
    for v in g:
        for w in g[v]:
            if g[v][w] == 1: print('edgeu('+str(v)+','+str(w)+').', file=file)
            if g[v][w] == 2: print('confu('+str(v)+','+str(w)+').', file=file)
            if g[v][w] == 3:
                print('edgeu('+str(v)+','+str(w)+').', file=file)
                print('confu('+str(v)+','+str(w)+').', file=file)

def eqclass(g,
            urate=2,
            timeout=0,
            threads=THREADS,
            capsize=CAPSIZE,
            graphfile='gu.pl',
            ufile='drawu.pl',
            program='supersample.pl',
            cpath=CLINGOPATH,
            ppath='./',
            nameid=''):

    cmdline = cpath+'clingo '+threads+' --time-limit='+str(timeout)\
      +' -n '+str(capsize)+' '+ppath+graphfile+nameid+' '+ppath+ufile\
      +nameid+' '+ppath+program+nameid

    with open(ppath+graphfile+nameid,'w') as f:
        g2clingo(g,file=f)

    with open(ppath+ufile+nameid,'w') as f:
        rate(urate,file=f)

    with open(ppath+program+nameid,'w') as f:
        uprogram(file=f)

    try:
        p = subprocess.Popen(cmdline.split(),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             close_fds=True)
    except subprocess.CalledProcessError:
        pass
    p_status = p.wait()
    (output, err) = p.communicate()
    p.stdout.close()
    os.remove(ppath+graphfile+nameid)
    os.remove(ppath+program+nameid)
    os.remove(ppath+ufile+nameid)
    answers = clingo2g(output)

    return answers



def a2edgetuple(answer):
    edges = [x for x in answer if 'edge1' in x]
    u = [x for x in answer if x[0]=='u'][0]
    return edges,u


def clingo2g(output):
    s = set()
    answers = filterAnswers(output.split('\n'))
    answers = [a2edgetuple(x) for x in answers]
    l = [(c2edgepairs(x[0]),x[1]) for x in answers]
    l = [(bfu.g2num(edgepairs2g(x[0])),int(x[1][2:-1])) for x in l]
    return l


def c2edgepairs(clist):
    return [x[6:-1].split(',') for x in clist]


def wc2edgepairs(clist):
    return [map(int,x[6:-1].split(',')) for x in clist]


def nodenum(edgepairs):
    nodes = 0
    for e in edgepairs:
        nodes = np.max([nodes, np.max(map(int,e))])
    return nodes

def edgepairs2g(edgepairs):
    n = nodenum(edgepairs)
    g = {x+1:{} for x in range(n)}
    for e in edgepairs:
        g[int(e[0])][int(e[1])] = 1
    return g


def wedgepairs2g(edgepairs):
    n = nodenum(edgepairs)
    g = {x+1:{} for x in range(n)}
    for e in edgepairs:
        g[e[0]][e[1]] = 1
    return g


def filterAnswers(slist):
    alist = []
    anAnswer = False
    for e in slist:
        if anAnswer:
            alist.append(e.split(' '))
            anAnswer=False
        if  e[:6] == "Answer":
            anAnswer = True
    return alist
