import scipy.weave as weave
from scipy.weave import converters

"""
Real-Time Fluid Dynamics for Games by Jos Stam (2003).
Parts of author's work are also protected
under U. S. patent #6,266,071 B1 [Patent].
"""

def set_bnd(N_X, N_Y, b, x, toric=False):
    if toric:
        tmp = x.copy()
        x[0,:] = tmp[N_X+1,:]
        
    else:
        """
        We assume that the fluid is contained in a box with solid walls: no flow
        should exit the walls. This simply means that the horizontal component of
        the velocity should be zero on the vertical walls, while the vertical
        component of the velocity should be zero on the horizontal walls. For the
        density and other fields considered in the code we simply assume
        continuity. The following code implements these conditions.
        """
        if b == 1:
            x[0,:] = -x[1,:]
            x[N_X+1,:] = -x[N_X,:]
        else:
            x[0,:] = x[1,:]
            x[N_X+1,:] = x[N_X,:]
        if b == 2:
            x[:,0] = -x[:,1]
            x[:,N_Y+1] = -x[:,N_Y]
        else:
            x[:,0] = x[:,1]
            x[:,N_Y+1] = x[:,N_Y]
        # edges
        x[0,0] = 0.5*(x[1,0]+x[0,1])
        x[0,N_Y+1] = 0.5*(x[1,N_Y+1]+x[0,N_Y])
        x[N_X+1,0] = 0.5*(x[N_X,0]+x[N_X+1,1])
        x[N_X+1,N_Y+1] = 0.5*(x[N_X,N_Y+1]+x[N_X+1,N_Y])


def lin_solve(N_X, N_Y, b, x, x0, a, c):
    for k in range(0, 20):
        x[1:N_X+1,1:N_Y+1] = (x0[1:N_X+1,1:N_Y+1]
                          +a*(x[0:N_X,1:N_Y+1]  +
                              x[2:N_X+2,1:N_Y+1]+
                              x[1:N_X+1,0:N_Y]  +
                              x[1:N_X+1,2:N_Y+2]))/c
        set_bnd(N_X, N_Y, b, x)


# Addition of forces: the density increases due to sources
def add_source(N_X, N_Y, x, s, dt):
    x += dt*s


# Diffusion: the density diffuses at a certain rate
def diffuse (N_X, N_Y, b, x, x0, diff, dt):
    """
    The basic idea behind our method is to find the densities which when
    diffused backward in time yield the densities we started with.  The
    simplest iterative solver which works well in practice is Gauss-Seidel
    relaxation.
    """
    a = dt*diff*N_X*N_Y
    lin_solve(N_X, N_Y, b, x, x0, a, 1+4*a)


# Advection: the density follows the velocity field
def advect (N_X, N_Y, b, d, d0, u, v, dt):
    """
    The basic idea behind the advection step. Instead of moving the cell
    centers forward in time through the velocity field, we look for the
    particles which end up exactly at the cell centers by tracing backwards in
    time from the cell centers.
    """
    code = """
           #define MAX(a,b) ((a)<(b) ? (b) : (a))
           #define MIN(a,b) ((a)>(b) ? (b) : (a))

           float x, y, s1, s0, t1, t0;
           int i0, i1, j0, j1;
           for (int i=1; i<(N_X+1); ++i) {
               for (int j=1; j<(N_Y+1); ++j) {
                   x = MIN(MAX(i-dt0*u(i,j),0.5),N_X+0.5);
                   y = MIN(MAX(j-dt0*v(i,j),0.5),N_Y+0.5);
                   i0 = int(x);
                   i1 = i0+1;
                   j0 = int(y);
                   j1 = j0+1;
                   s1 = x-i0;
                   s0 = 1-s1;
                   t1 = y-j0;
                   t0 = 1-t1;
                   d(i,j) = s0*(t0*d0(i0,j0)+t1*d0(i0,j1))+ 
                            s1*(t0*d0(i1,j0)+t1*d0(i1,j1));
                   }
               }
           #undef MIN
           #undef MAX
           """
    dt0 = dt*N_X
    # Does not work yet
    weave.inline(code, ['N_X', 'N_Y', 'u', 'v', 'd', 'd0', 'dt0'],
                 type_converters=converters.blitz,
                 compiler='gcc')
    # for i in range(1, N+1):
    #     for j in range(1, N+1):
    #         x = min(max(i-dt0*u[i,j],0.5),N+0.5)
    #         y = min(max(j-dt0*v[i,j],0.5),N+0.5)
    #         i0 = int(x)
    #         i1 = i0+1
    #         j0 = int(y)
    #         j1 = j0+1
    #         s1 = x-i0
    #         s0 = 1-s1
    #         t1 = y-j0
    #         t0 = 1-t1
    #         d[i,j] = s0*(t0*d0[i0,j0]+t1*d0[i0,j1])+ \
    #                  s1*(t0*d0[i1,j0]+t1*d0[i1,j1])
    set_bnd (N_X, N_Y, b, d)


def project(N_X, N_Y, u, v, p, div):
    h = 1.0/N_X
    div[1:N_X+1,1:N_Y+1] = -0.5*h*(u[2:N_X+2,1:N_Y+1]
                               -u[0:N_X,1:N_Y+1]
                               +v[1:N_X+1,2:N_Y+2]
                               -v[1:N_X+1,0:N_Y])
    p[1:N_X+1,1:N_Y+1] = 0
    set_bnd (N_X, N_Y, 0, div)
    set_bnd (N_X, N_Y, 0, p)
    lin_solve (N_X, N_Y, 0, p, div, 1, 4)
    # ??? not in the paper /h
    u[1:N_X+1,1:N_Y+1] -= 0.5*(p[2:N_X+2,1:N_Y+1]-p[0:N_X,1:N_Y+1])/h
    # ??? not in the paper /h
    v[1:N_X+1,1:N_Y+1] -= 0.5*(p[1:N_X+1,2:N_Y+2]-p[1:N_X+1,0:N_Y])/h
    set_bnd (N_X, N_Y, 1, u)
    set_bnd (N_X, N_Y, 2, v)

# Evolving density: advection, diffusion, addition of sources
def dens_step (N_X, N_Y, x, x0, u, v, diff, dt):
    add_source(N_X, N_Y, x, x0, dt)
    x0, x = x, x0 # swap
    diffuse(N_X, N_Y, 0, x, x0, diff, dt)
    x0, x = x, x0 # swap
    advect(N_X, N_Y, 0, x, x0, u, v, dt)

# Evolving velocity: self-advection, viscous diffusion, addition of forces
def vel_step (N_X, N_Y, u, v, u0, v0, visc, dt):
    add_source(N_X, N_Y, u, u0, dt)
    add_source(N_X, N_Y, v, v0, dt);
    u0, u = u, u0 # swap
    diffuse(N_X, N_Y, 1, u, u0, visc, dt)
    v0, v = v, v0 # swap
    diffuse(N_X, N_Y, 2, v, v0, visc, dt)
    project(N_X, N_Y, u, v, u0, v0)
    u0, u = u, u0 # swap
    v0, v = v, v0 # swap
    advect(N_X, N_Y, 1, u, u0, u0, v0, dt)
    advect(N_X, N_Y, 2, v, v0, u0, v0, dt)
    project(N_X, N_Y, u, v, u0, v0)
