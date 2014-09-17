# This is a use-case of the tools in the tools directory. The example defines a graph and shows how to generate a figure that shows the graph at different undersampling rates. Running the file in python (python dbnplot.py) generates a figure in figures folder: shipfig.pdf


# system packages
import os, sys
import numpy as np
from random import random
import pickle as pkl
sys.path.append('tools')

# local packages
import dbn2latex as d2l
    

g = {
    '1': {'2': {(0, 1)},},
    '2': {'3': {(0, 1)}},
    '3': {'4': {(0, 1)}},
    '4': {'5': {(0, 1)}},
    '5': {'6': {(0, 1)}},
    '6': {'1': {(0, 1)}, '6': {(0, 1)}},
}

# fname = 'list.pkl'
# f = open(fname,'r')
# l = pkl.load(f)
# f.close()

#y = min(5,len(l))
#x = np.int(np.ceil(len(l)/float(y)))


# output file
foo = open('figures/shipfig_figure.tex', 'wb')
sys.stdout = foo

# generation of the output
ww = 6
d2l.gmatrix_fold(g,ww,1,R=2.5, w_gap=1, h_gap=2, mname='TT1')
d2l.matrix_fold(g,ww,1,R=2, w_gap=1, h_gap=2, stl=', below=5cm of TT1.west,anchor=west')


sys.stdout = sys.__stdout__              # remember to reset sys.stdout!
foo.flush()
foo.close()
PPP = os.getcwd()
os.chdir('figures')
os.system('pdflatex --shell-escape shipfig.tex 2>&1 > /dev/null')
os.chdir(PPP)
