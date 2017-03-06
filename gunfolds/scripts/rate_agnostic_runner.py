from gunfolds.tools.calc_procs import get_process_count
from gunfolds.tools import bfutils
import gunfolds.tools.graphkit as gk
from gunfolds.tools import traversal
import gunfolds.tools.unknownrate as ur
import gunfolds.tools.zickle as zkl
from multiprocessing import Pool, Process, Queue
import functools
import time, sys, os
import socket
import scipy
import timeout_decorator
from timeout_decorator import TimeoutError

TIMEOUT=24*3600 # seconds timeout
KEY = 'ral_async'
UMAX = 4
INPNUM = 1  # number of randomized starts per graph
CAPSIZE = 1000  # stop traversing after growing equivalence class tothis size
REPEATS = 100
PNUM = 50#get_process_count(INPNUM)

#@timeout_decorator.timeout(TIMEOUT)#, use_signals=False)
@timeout_decorator.timeout(TIMEOUT, use_signals=False)
def ra_caller(g2, fold):
    startTime = int(round(time.time() * 1000))
    s = ur.liteqclass(g2, verbose=False, capsize=CAPSIZE)
    endTime = int(round(time.time() * 1000))
    ra_time = endTime-startTime
    return s, ra_time

def ra_wrapper(fold, n=10, k=10):
    scipy.random.seed()
    l = {}
    while True:
        try:
            g = gk.ringmore(n, k)  # random ring of given density
            gs = bfutils.call_undersamples(g)
            for u in range(1, min([len(gs), UMAX])):
                g2 = bfutils.undersample(g, u)
                print fold, ': ', traversal.density(g), ':',
                try:
                    s, ra_time = ra_caller(g2, fold)
                except TimeoutError:
                    s = None
                    ra_time = None
                if s is not None:
                    print len(s), u
                else:
                    print 'timeout'
                l[u] = {'eq': s, 'ms': ra_time}
        except MemoryError:
            print 'memory error... retrying'
            continue
        break
    return {'gt': g, 'solutions': l}


if __name__ == '__main__':
    print 'processes: ', PNUM, INPNUM

    densities = {5: [0.2],
                 6: [0.2, .25, .3],
                 7: [0.2, .25, .3],
                 8: [0.25, 0.3],
                 9: [.2],
                 10: [.15, 0.2, 0.25, 0.3],
                 15: [0.2],
                 20: [0.1],  # 0.15, 0.2, 0.25, 0.3],
                 25: [0.1],
                 30: [0.1],
                 35: [0.1],
                 40: [0.1],
                 50: [0.05, 0.1],
                 60: [0.05, 0.1]}

    for nodes in [10]:
        z = {}
        pool=Pool(processes=PNUM)
        for dens in densities[nodes]:
            print "{:2}: {:8} : {:10} : {:10}  {:10}".format('id', 'densityi(G)', 'density(H)', 'eq class', 'time')
            e = bfutils.dens2edgenum(dens, n=nodes)
            eqclasses =  pool.map(functools.partial(ra_wrapper, n=nodes, k=e),range(REPEATS))
            z[dens] = eqclasses
            zkl.save(z[dens],
                     socket.gethostname().split('.')[0]+\
                     '_nodes_'+str(nodes)+'_density_'+\
                     str(dens)+'_'+KEY+'_.zkl')

            print ''
            print '----'
            print ''
        pool.close()
        pool.join()
        zkl.save(z,socket.gethostname().split('.')[0]+'_nodes_'+str(nodes)+'_'+KEY+'_.zkl')
        for dens in densities[nodes]:
            os.remove(socket.gethostname().split('.')[0]+\
                      '_nodes_'+str(nodes)+'_density_'+str(dens)+'_'+KEY+'_.zkl')
