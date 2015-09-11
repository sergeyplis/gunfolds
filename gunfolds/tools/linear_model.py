from gunfolds.tools import ecj
from gunfolds.tools import bfutils as bfu
from gunfolds.tools.conversions import graph2adj, adjs2graph
from gunfolds.tools import graphkit as gk
import numpy as np
from progressbar import ProgressBar, Percentage
import scipy
from scipy import linalg, optimize
from statsmodels.tsa.api import VAR
from sympy.matrices import SparseMatrix



def symchol(M): # symbolic Cholesky
    B = SparseMatrix(M)
    t = B.row_structure_symbolic_cholesky()
    B = np.asarray(B)*0
    for i in range(B.shape[0]):
        B[i, t[i]] = 1
    return B

def G2SVAR(G):
    n = len(G)
    A, B = npG2SVAR(G)
    P, L, U = linalg.lu(B)
    A = linalg.inv(L).tolist()
    B = B.tolist()
    A = listplace(A, 0.0, 0.0)
    for i in range(0, n):
        A[i][i] = 1
    B = listplace(B, 0.0, 'e')
    for i in range(0, n):
        B[i][i] = 'e'
    return A, B, P

def G2AH(G):
    n = len(G)
    A, B = npG2SVAR(G)
    P, L, U = linalg.lu(B)
    A = linalg.inv(L).tolist()
    B = B.tolist()
    A = listplace(A, 0.0, 0.0)
    for i in range(0, n):
        A[i][i] = 1
    B = listplace(B, 0.0, 'e')
    for i in range(0, n):
        B[i][i] = 'e'
    return A, B, P

def bnf2CG(fname):
    d = eval(open(fname).read())
    G = {}
    for v in d:
        G[v] = {u: 1 for u in d[v]['pars']}
    G = ecj.tr(G)
    for v in G:
        ld = {u: 1 for u in G[v]}
        G[v] = ld
    return G

def npG2SVAR(G):
    n = len(G)
    A = [[0]*n]*n
    B = [[0]*n]*n
    for i in range(n):
        B[i][i] = 1

    for v in G:
        for w in G[v]:
            if G[v][w] in (1,3):
                A[w-1][v-1] = 1
            if G[v][w] in (2,3):
                B[w-1][v-1] = 1
    A = np.asarray(A)
    B = symchol(B)
    return A, B

def x2M(x, A, B, aidx, bidx):
    A[aidx] = x[:len(aidx[0])]
    B[bidx] = x[len(aidx[0]):]
    # B[(bidx[1],bidx[0])] = x[len(aidx[0]):]
    return A, B

def nllf(x, A, B, Y, aidx, bidx): # negative log likelihood
    A, B = x2M(x, A, B, aidx, bidx)
    T = Y.shape[1]
    X = Y[:, 1:] - np.dot(A, Y[:, :-1])
    ldB = T*np.log(abs(1./linalg.det(B)))
    return ldB + 0.5*np.trace( np.dot(np.dot(B.T, B), np.dot(X, X.T)))

def nllf2(x, A, B, YY, XX, YX, T, aidx, bidx): # negative log likelihood
    A, B = x2M(x, A, B, aidx, bidx)
    AYX = np.dot(A, YX.T)
    S = YY - AYX - AYX.T + np.dot(np.dot(A, XX), A.T)
    ldB = T*np.log(abs(1./linalg.det(B)))
    return 0.5*np.dot(np.dot(B.T, B).T.flat, S.flat) + ldB
    # return ldB + 0.5*np.trace( np.dot(np.dot(B.T, B), S))

def VARbic(nllf, K, T):
    return 2*nllf + K*np.log(T)

def listplace(l, a, b):
    return [listplace(x, a, b) if not np.isscalar(x) else b if x != a  else x for x in l]

# -------------------------------------------------------------------
# data generation
# -------------------------------------------------------------------

def randweights(n, c=0.1, factor=9):
    rw = scipy.random.randn(n)
    idx = scipy.where(abs(rw) < factor*c)
    if idx:
        rw[idx] = rw[idx]+scipy.sign(rw[idx])*c*factor
    return rw

def transitionMatrix(cg, minstrength=0.1):
    A = graph2adj(cg)
    edges = scipy.where(A == 1)
    A[edges] = randweights(edges[0].shape[0], c=minstrength)
    l = linalg.eig(A)[0]
    c = 0
    pbar = ProgressBar(widgets=['Searching for weights: ', Percentage(), ' '], maxval=10000).start()
    while max(l*scipy.conj(l)) > 1:
        A[edges] = randweights(edges[0].shape[0], c=c)
        c += 1
        l = linalg.eig(A)[0]
        pbar.update(c)
    pbar.finish()
    return A

def sampleWeights(n, minstrength=0.1):
    r = scipy.randn(n)
    s = minstrength/np.min(np.abs(r))
    r = s*r
    return r

def transitionMatrix2(cg, minstrength=0.1):
    A = graph2adj(cg)
    edges = scipy.where(A == 1)
    A[edges] = sampleWeights(edges[0].shape[0], minstrength=minstrength)
    l = linalg.eig(A)[0]
    c = 0
    pbar = ProgressBar(widgets=['Searching for weights: ', Percentage(), ' '], maxval=10000).start()
    while max(l*scipy.conj(l)) > 1:
        A[edges] = sampleWeights(edges[0].shape[0], minstrength=minstrength)
        c += 1
        l = linalg.eig(A)[0]
        if c > pbar.maxval:
            raise ValueError
        pbar.update(c)
    pbar.finish()
    return A

def transitionMatrix3(cg, x0=None, minstrength=0.1):
    A = graph2adj(cg)
    edges = scipy.where(A == 1)

    try:
        s = x0.shape
        x = x0
    except AttributeError:
        A = initRandomMatrix(A, edges)
        x = A[edges]

    def objective(x):
        A[edges] = np.real(x)
        l = linalg.eig(A)[0]
        m = np.max(np.real(l*scipy.conj(l)))-0.99
        n = np.min(np.min(np.abs(x)), minstrength)-minstrength
        return m*m + 0.1*n*n

    o = np.zeros(len(edges))
    while np.min(np.abs(o[0])) < 0.8*minstrength:
        rpt = True
        while rpt:
            try:
                try:
                    o = optimize.fmin_bfgs(objective, x,
                                           gtol=1e-10, maxiter=100,
                                           disp=False, full_output=True)
                    A[edges] = np.real(o[0])
                    l = linalg.eig(A)[0]
                    if np.max(np.real(l*scipy.conj(l))) < 1:
                        rpt = False

                except:
                    rpt = True
            except Warning:
                x = scipy.randn(len(edges[0]))
                rpt = True
    A[edges] = np.real(o[0])
    return A

def initRandomMatrix(A, edges, maxtries=100, distribution='beta', stable=True):
    '''
    possible distributions:
    flat
    flatsigned
    beta
    normal
    uniform
    '''
    s = 2.0

    def init():
        if distribution == 'flat':
            x = np.ones(len(edges[0]))
        elif distribution == 'flatsigned':
            x = np.sign(scipy.randn(len(edges[0])))*scipy.ones(len(edges[0]))
        elif distribution == 'beta':
            x = np.random.beta(0.5, 0.5, len(edges[0]))*3-1.5
        elif distribution == 'normal':
            x = scipy.randn(len(edges[0]))
        elif distribution == 'uniform':
            x = np.sign(scipy.randn(len(edges[0])))*scipy.rand(len(edges[0]))
        else:
            raise ValueError('Wrong option!')
        return x

    def eigenvalue(A):
        l = linalg.eig(A)[0]
        s = np.max(np.real(l*scipy.conj(l)))
        return s

    x = init()
    A[edges] = x
    s = eigenvalue(A)
    alpha = np.random.rand()*(0.99-0.8)+0.8
    A = A/(alpha*s)
    s = eigenvalue(A)

    return A

def transitionMatrix4(g, minstrength=0.1, distribution='normal', maxtries=1000):
    A = graph2adj(g)
    edges = np.where(A == 1)
    s = 2.0
    c = 0
    pbar = ProgressBar(widgets=['Searching for weights: ',
                                Percentage(), ' '],
                       maxval=maxtries).start()
    while s > 1.0:
        minstrength -= 0.001
        A = initRandomMatrix(A, edges, distribution=distribution)
        x = A[edges]
        delta = minstrength/np.min(np.abs(x))
        A[edges] = delta*x
        l = linalg.eig(A)[0]
        s = np.max(np.real(l*scipy.conj(l)))
        c += 1
        if c > maxtries:
            return None
        pbar.update(c)
    pbar.finish()

    return A

def drawsamplesLG(A, nstd=0.1, samples=100):
    n = A.shape[0]
    data = scipy.zeros([n, samples])
    data[:, 0] = nstd*scipy.random.randn(A.shape[0])
    for i in range(1, samples):
        data[:, i] = scipy.dot(A, data[:, i-1]) \
                    + nstd*scipy.random.randn(A.shape[0])
    return data


def getAgraph(n, mp=2, st=0.5, verbose=True):
    keeptrying = True
    while keeptrying:
        G = gk.rnd_CG(n, maxindegree=mp, force_connected=True)
        try:
            A = transitionMarix2(G, minstrength=st)
            keeptrying = False
        except ValueError as e:
            if verbose:
                print "!!! Unable to find strong links for a stable matrix !!!"
                print "*** trying a different graph"
    return {'graph':      G,
            'transition': A,
            'converges':  len(bfu.call_undersamples(G))}

def getAring(n, density=0.1, st=0.5, verbose=True, dist='flatsigned'):
    keeptrying = True
    plusedges = bfu.dens2edgenum(density, n)
    while keeptrying:
        G = gk.ringmore(n, plusedges)
        try:
            A = transitionMatrix4(G, minstrength=st, distribution=dist)
            try:
                s = A.shape
                keeptrying = False
            except AttributeError:
                keeptrying = True
        except ValueError:
            if verbose:
                print "!!! Unable to find strong links for a stable matrix !!!"
                print "*** trying a different graph"
    return {'graph':      G,
            'transition': A,
            'converges':  len(bfu.call_undersamples(G))}



# -------------------------------------------------------------------
# estimation
# -------------------------------------------------------------------

def scoreAGraph(G, data, x0 = None):
    A, B = npG2SVAR(G)
    K = scipy.sum(abs(A)+abs(B))
    a_idx = np.where(A != 0)
    b_idx = np.where(B != 0)
    if x0:
        o = optimize.fmin_bfgs(nllf, x0, args=(A, B, data, a_idx, b_idx),
                               disp=False, full_output=True)
    else:
        o = optimize.fmin_bfgs(nllf, scipy.randn(K),
                               args=(np.double(A), np.double(B),
                                     data, a_idx, b_idx),
                               disp=False, full_output=True)
    return 2*o(1) + K*np.log(T) #VARbic(o[1],K,data.shape[1])

def estimateG(G, YY, XX, YX, T, x0=None):
    A, B = npG2SVAR(G)
    K = scipy.sum(abs(A)+abs(B))
    a_idx = np.where(A != 0)
    b_idx = np.where(B != 0)
    try:
        s = x0.shape
        x = x0
    except AttributeError:
        x = scipy.randn(K)
    o = optimize.fmin_bfgs(nllf2, x,
                           args=(np.double(A), np.double(B),
                                 YY, XX, YX, T, a_idx, b_idx),
                           disp=False, full_output=True)
    A, B = x2M(o[0], np.double(A), np.double(B), a_idx, b_idx)
    return  A, B


def data2AB(data, x0=None):
    n = data.shape[0]
    T = data.shape[1]
    YY = np.dot(data[:, 1:], data[:, 1:].T)
    XX = np.dot(data[:, :-1], data[:, :-1].T)
    YX = np.dot(data[:, 1:], data[:, :-1].T)

    model = VAR(data.T)
    r = model.fit(1)
    A = r.coefs[0,:,:]

    # A = np.ones((n,n))
    B = np.ones((n, n))
    np.fill_diagonal(B, 0)
    B[np.triu_indices(n)] = 0
    K = np.int(scipy.sum(abs(B)))#abs(A)+abs(B)))

    a_idx = np.where(A != 0)
    b_idx = np.where(B != 0)
    np.fill_diagonal(B, 1)

    try:
        s = x0.shape
        x = x0
    except AttributeError:
        x = np.r_[A.flatten(), 0.1*scipy.randn(K)]
    o = optimize.fmin_bfgs(nllf2, x,
                           args=(np.double(A), np.double(B),
                                 YY, XX, YX, T, a_idx, b_idx),
                           gtol=1e-12, maxiter=500,
                           disp=False, full_output=True)
    A, B = x2M(o[0], np.double(A), np.double(B), a_idx, b_idx)
    B = B+B.T
    return  A, B

def amap(f, a):
    v = np.vectorize(f)
    return v(a)

def AB2intAB(A,B, th=0.09):
    A[amap(lambda x: abs(x) > th, A)] = 1
    A[amap(lambda x: abs(x) < 1, A)] = 0
    B[amap(lambda x: abs(x) > th, B)] = 1
    B[amap(lambda x: np.abs(x) < 1, B)] = 0
    np.fill_diagonal(B,0)
    return A, B

def data2graph(data,x0=None):
    A, B = data2AB(data, x0=x0)
    Ab, Bb = AB2intAB(A, B)
    return adjs2graph(Ab, Bb)

def data2VARgraph(data, pval=0.05):
    model = VAR(data.T)
    r = model.fit(1)
    A = r.coefs[0,:,:]
    n = A.shape[0]
    g = {i:{} for i in range(1, n+1)}

    for i in range(n):
        for j in range(n):
            if np.abs(A[j, i]) > pval:
                g[i+1][j+1] = 1

    return g

# this is for the SAT solver project
def stableVAR(n,density=0.1,dist='beta'):
    """
    This function keeps trying to create a random graph and a random
    corresponding transition matrix until it succeeds.

    Arguments:
    - `n`: number of nodes in the graph
    - `density`: ratio of total nodes to n^2 possible nodes
    - `dist`: distribution from which to sample the weights. Available
      options are flat, flatsigned, beta, normal, uniform
    """
    scipy.random.seed()
    sst = 0.9
    r = None
    while not r:
        r = getAring(n, density, sst, False, dist=dist)
        if sst < 0.03:
            sst -= 0.001
        else:
            sst -= 0.01
        if sst < 0:
            sst = 0.02
    return r['graph'], r['transition']

def genData(n, rate=2, density=0.1, burnin=100, ssize=2000, noise=0.1):
    """
    Given a number of nodes this function randomly generates a ring
    SCC and the corresponding stable transition matrix. It tries until
    succeeds and for some graph densities and parameters of the
    distribution of transition matrix values it may take
    forever. Please play with the dist parameter to stableVAR. Then
    using this transition matrix it generates `ssize` samples of data
    and undersamples them by `rate` discarding the `burnin` number of
    samples at the beginning.

    Arguments:
    - `n`: number of nodes in the desired graph
    - `rate`: undersampling rate (1 - no undersampling)
    - `density`: density of the graph to be generted
    - `burnin`: number of samples to discard since the beginning of VAR sampling
    - `ssize`: how many samples to keep at the causal sampling rate
    - `noise`: noise standard deviation for the VAR model
    """
    g, Agt = stableVAR(n, density=density)
    data = drawsamplesLG(Agt, samples=burnin + ssize * 2, nstd=noise)
    data = data[:, burnin:]
    return g, Agt, data[:,::rate]

def estimateSVAR(data, th=0.09):
    A, B = data2AB(data)
    A, B = AB2intAB(A, B, th=th)
    return A, B

# option #1
def randomSVAR(n, rate=2, density=0.1, th=0.09, burnin=100, ssize=2000, noise=0.1):
    """
    Given a number of nodes this function randomly generates a ring
    SCC and the corresponding stable transition matrix. It tries until
    succeeds and for some graph densities and parameters of the
    distribution of transition matrix values it may take
    forever. Please play with the dist parameter to stableVAR. Then
    using this transition matrix it generates `ssize` samples of data
    and undersamples them by `rate` discarding the `burnin` number of
    samples at the beginning. For these data the funcion solves the
    SVAR estimation maximizing log likelihood and returns the A and B
    matrices.

    Arguments:
    - `n`: number of nodes in the desired graph
    - `rate`: undersampling rate (1 - no undersampling)
    - `density`: density of the graph to be generted
    - `th`: threshold for discarding edges in A and B
    - `burnin`: number of samples to discard since the beginning of VAR sampling
    - `ssize`: how many samples to keep at the causal sampling rate
    - `noise`: noise standard deviation for the VAR model
    """
    g, Agt, data = genData(n, rate=rate, density=density,
                           burnin=burnin, ssize=ssize, noise=noise)
    A, B = estimateSVAR(data, th=th)

    return {'graph': g,
            'transition': Agt,
            'estimate': adjs2graph(A, B),
            'directed': A,
            'bidirected': B
            }

# option #2
def noiseData(data, noise=0.1):
    h, w = data.shape
    return data + np.random.randn(h,w)*noise

def randomSVARs(n, repeats=100, rate=2, density=0.1, th=0.09,
                burnin=100, ssize=2000, noise=0.1, strap_noise = 0.1):
    """
    does what requested - help is on the way

    Arguments:
    - `n`: number of nodes in the desired graph
    - `repeats`: how many times to add noise and re-estiamte
    - `rate`: undersampling rate (1 - no undersampling)
    - `density`: density of the graph to be generted
    - `th`: threshold for discarding edges in A and B
    - `burnin`: number of samples to discard since the beginning of VAR sampling
    - `ssize`: how many samples to keep at the causal sampling rate
    - `noise`: noise standard deviation for the VAR model
    - `strap_noise`: amount of noise for bootstrapping
    """
    g, Agt, data = genData(n, rate=rate, density=density,
                           burnin=burnin, ssize=ssize, noise=noise)

    As = []
    Bs = []
    A, B = estimateSVAR(data, th=th)
    As.append(A)
    Bs.append(B)

    for i in range(repeats-1):
        A, B = estimateSVAR(noiseData(data, noise=strap_noise), th=th)
        As.append(A)
        Bs.append(B)

    A = 1 - np.mean(As, axis=0)
    B = 1 - np.mean(Bs, axis=0)
    
    return {'graph': g,
            'transition': Agt,
            'directed': A,
            'bidirected': B
            }

# option #3
