"""
Approximation of functions by linear combination of basis functions in
function spaces and the least squares method or the collocation method
for determining the coefficients.
"""
import sympy as sm
import numpy as np
import matplotlib.pyplot as plt
#import scitools.std as plt

def least_squares(f, psi, Omega):
    """
    Given a function f(x) on an interval Omega (2-list)
    return the best approximation to f(x) in the space V
    spanned by the functions in the list psi.
    """
    N = len(psi) - 1
    A = sm.zeros((N+1, N+1))
    b = sm.zeros((N+1, 1))
    x = sm.Symbol('x')
    print '...evaluating matrix...',
    for i in range(N+1):
        for j in range(i, N+1):
            print '(%d,%d)' % (i, j)

            integrand = psi[i]*psi[j]
            I = sm.integrate(integrand, (x, Omega[0], Omega[1]))
            if isinstance(I, sm.Integral):
                # Could not integrate symbolically, use numerical int.
                print 'numerical integration of', integrand
                integrand = sm.lambdify([x], integrand)
                I = sm.mpmath.quad(integrand, [Omega[0], Omega[1]])
            A[i,j] = A[j,i] = I
        integrand = psi[i]*f
        I = sm.integrate(integrand, (x, Omega[0], Omega[1]))
        if isinstance(I, sm.Integral):
            # Could not integrate symbolically, use numerical int.
            print 'numerical integration of', integrand
            integrand = sm.lambdify([x], integrand)
            I = sm.mpmath.quad(integrand, [Omega[0], Omega[1]])
        b[i,0] = I
    print
    print 'A:\n', A, '\nb:\n', b
    c = A.LUsolve(b)  # symbolic solve
    print 'coeff:', c

    # c is a sympy Matrix object, numbers are in c[i,0]
    u = sum(c[i,0]*psi[i] for i in range(len(psi)))
    print 'approximation:', u
    return u, [c[i,0] for i in range(len(c))]

def numerical_linsys_solve(A, b, floating_point_calc='sumpy'):
    """
    Given a linear system Au=b as sympy arrays, solve the
    system using different floating-point software.
    floating_point_calc may be 'sympy', 'numpy.float64',
    'numpy.float32'.
    This function is used to investigate ill-conditioning
    of linear systems arising from approximation methods.
    """
    if floating_point_calc == 'sympy':
        #sm.mpmath.mp.dsp = 10  # does not affect the computations here
        A = sm.mpmath.fp.matrix(A)
        b = sm.mpmath.fp.matrix(b)
        print 'A:\n', A, '\nb:\n', b
        c = sm.mpmath.fp.lu_solve(A, b)
        #c = sm.mpmath.lu_solve(A, b) # more accurate
        print 'sympy.mpmath.fp.lu_solve:', c
    elif floating_point_calc.startswith('numpy'):
        import numpy as np
        # Double precision (float64) by default
        A = np.array(A.evalf())
        b = np.array(b.evalf())
        if floating_point_calc == 'numpy.float32':
            # Single precision
            A = A.astype(np.float32)
            b = b.astype(np.float32)
        c = np.linalg.solve(A, b)
        print 'numpy.linalg.solve, %s:' % floating_point_calc, c


def least_squares_orth(f, psi, Omega):
    """
    Same as least_squares, but for orthogonal
    basis such that one avoids calling up standard
    Gaussian elimination.
    """
    N = len(psi) - 1
    A = [0]*(N+1)       # plain list to hold symbolic expressions
    b = [0]*(N+1)
    x = sm.Symbol('x')
    print '...evaluating matrix...',
    for i in range(N+1):
        print '(%d,%d)' % (i, i)
        # Assume orthogonal psi can be be integrated symbolically...
        A[i] = sm.integrate(psi[i]**2, (x, Omega[0], Omega[1]))

        # Fallback on numerical integration if f*psi is too difficult
        # to integrate
        integrand = psi[i]*f
        I = sm.integrate(integrand,  (x, Omega[0], Omega[1]))
        if isinstance(I, sm.Integral):
            print 'numerical integration of', integrand
            integrand = sm.lambdify([x], integrand)
            I = sm.mpmath.quad(integrand, [Omega[0], Omega[1]])
        b[i] = I
    print 'A:\n', A, '\nb:\n', b
    c = [b[i]/A[i] for i in range(len(b))]
    print 'coeff:', c
    u = 0
    for i in range(len(psi)):
        u += c[i]*psi[i]
    # Alternative:
    # u = sum(c[i,0]*psi[i] for i in range(len(psi)))
    print 'approximation:', u
    return u, c

def trapezoidal(values, dx):
    """
    Integrate a function whose values on a mesh with spacing dx
    are in the array values.
    """
    #return dx*np.sum(values)
    return dx*(np.sum(values) - 0.5*values[0] - 0.5*values[-1])


def least_squares_numerical(f, psi, N, x,
                            integration_method='scipy',
                            orthogonal_basis=False):
    """
    Given a function f(x) (Python function), a basis specified by the
    Python function psi(x, i), and a mesh x (array), return the best
    approximation to f(x) in in the space V spanned by the functions
    in the list psi. The best approximation is represented as an array
    of values corresponding to x.  All calculations are performed
    numerically. integration_method can be `scipy` or `trapezoidal`
    (the latter uses x as mesh for evaluating f).
    """
    A = np.zeros((N+1, N+1))
    b = np.zeros(N+1)
    if not callable(f) or not callable(psi):
        raise TypeError('f and psi must be callable Python functions')
    Omega = [x[0], x[-1]]
    dx = x[1] - x[0]       # assume uniform partition

    import scipy.integrate

    print '...evaluating matrix...',
    for i in range(N+1):
        j_limit = i+1 if orthogonal_basis else N+1
        for j in range(i, j_limit):
            print '(%d,%d)' % (i, j)
            if integration_method == 'scipy':
                A_ij = scipy.integrate.quad(
                    lambda x: psi(x,i)*psi(x,j),
                    Omega[0], Omega[1], epsabs=1E-9, epsrel=1E-9)[0]
            elif integration_method == 'sympy':
                A_ij = sm.mpmath.quad(
                    lambda x: psi(x,i)*psi(x,j),
                    [Omega[0], Omega[1]])
            else:
                values = psi(x,i)*psi(x,j)
                A_ij = trapezoidal(values, dx)
            A[i,j] = A[j,i] = A_ij

        if integration_method == 'scipy':
            b_i = scipy.integrate.quad(
                lambda x: f(x)*psi(x,i), Omega[0], Omega[1],
                epsabs=1E-9, epsrel=1E-9)[0]
        elif integration_method == 'sympy':
            b_i = sm.mpmath.quad(
                lambda x: f(x)*psi(x,i), [Omega[0], Omega[1]])
        else:
            values = f(x)*psi(x,i)
            b_i = trapezoidal(values, dx)
        b[i] = b_i

    c = b/np.diag(A) if orthogonal_basis else np.linalg.solve(A, b)
    u = sum(c[i]*psi(x, i) for i in range(N+1))
    return u, c


def interpolation(f, psi, points):
    """
    Given a function f(x), return the approximation to
    f(x) in the space V, spanned by psi, that interpolates
    f at the given points. Must have len(points) = len(psi)
    """
    N = len(psi) - 1
    A = sm.zeros((N+1, N+1))
    b = sm.zeros((N+1, 1))
    # Wrap psi and f in Python functions rather than expressions
    # so that we can evaluate psi at points[i] (alternative to subs?)
    x = sm.Symbol('x')
    psi = [sm.lambdify([x], psi[i]) for i in range(N+1)]
    f = sm.lambdify([x], f)
    print '...evaluating matrix...'
    for i in range(N+1):
        for j in range(N+1):
            print '(%d,%d)' % (i, j)
            A[i,j] = psi[j](points[i])
        b[i,0] = f(points[i])
    print
    print 'A:\n', A, '\nb:\n', b
    c = A.LUsolve(b)
    print 'coeff:', c
    u = 0
    for i in range(len(psi)):
        u += c[i,0]*psi[i](x)
    # Alternative:
    # u = sum(c[i,0]*psi[i] for i in range(len(psi)))
    print 'approximation:', sm.simplify(u)
    return u, c

collocation = interpolation  # synonym in this module

def comparison_plot(f, u, Omega, filename='tmp',
                    plot_title='', ymin=None, ymax=None,
                    u_legend='approximation'):
    """Compare f(x) and u(x) for x in Omega in a plot."""
    x = sm.Symbol('x')
    print 'f:', f

    f = sm.lambdify([x], f, modules="numpy")
    u = sm.lambdify([x], u, modules="numpy")
    if len(Omega) != 2:
        raise ValueError('Omega=%s must be an interval (2-list)' % str(Omega))
    # When doing symbolics, Omega can easily contain symbolic expressions,
    # assume .evalf() will work in that case to obtain numerical
    # expressions, which then must be converted to float before calling
    # linspace below
    if not isinstance(Omega[0], (int,float)):
        Omega[0] = float(Omega[0].evalf())
    if not isinstance(Omega[1], (int,float)):
        Omega[1] = float(Omega[1].evalf())

    resolution = 601  # no of points in plot
    xcoor = np.linspace(Omega[0], Omega[1], resolution)
    # Vectorized functions expressions does not work with
    # lambdify'ed functions without the modules="numpy"
    exact  = f(xcoor)
    approx = u(xcoor)
    plt.plot(xcoor, approx, '-')
    plt.hold('on')
    plt.plot(xcoor, exact, '--')
    plt.legend([u_legend, 'exact'])
    plt.title(plot_title)
    plt.xlabel('x')
    if ymin is not None and ymax is not None:
        plt.axis([xcoor[0], xcoor[-1], ymin, ymax])
    plt.savefig(filename + '.pdf')
    plt.savefig(filename + '.png')
    plt.show()

if __name__ == '__main__':
    print 'Module file not meant for execution.'


