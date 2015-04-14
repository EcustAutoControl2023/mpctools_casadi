# Control of the Van der Pol
# oscillator using mpc_tools_casadi.
import mpctools as mpc
import numpy as np

#<<ENDCHUNK>>

# Define model and get simulator.
Delta = .5
Nt = 20
Nx = 2
Nu = 1
def ode(x,u):
    dxdt = [
        (1 - x[1]*x[1])*x[0] - x[1] + u,
        x[0]]
    return np.array(dxdt)

#<<ENDCHUNK>>

# Create a simulator.
vdp = mpc.OneStepSimulator(ode,
    Delta, Nx, Nu, vector=True)

#<<ENDCHUNK>>

# Then get nonlinear casadi functions
# and rk4 discretization.
def ode_rk4(x,u):
    return mpc.util.rk4(ode, x, [u], Delta=Delta)
ode_rk4_casadi = mpc.getCasadiFunc(ode_rk4,
    [Nx,Nu], ["x","u"], funcname="F")

#<<ENDCHUNK>>

# Define stage cost and terminal weight.
def lfunc(x,u):
    return mpc.mtimes(x.T,x) + mpc.mtimes(u.T,u)
l = mpc.getCasadiFunc(lfunc,
    [Nx,Nu], ["x","u"], funcname="l")

def Pffunc(x): return 10*mpc.mtimes(x.T,x)
Pf = mpc.getCasadiFunc(Pffunc,
    [Nx], ["x"], funcname="Pf")

#<<ENDCHUNK>>

# Bounds on u.
lb = {"u" : -.75*np.ones((Nt,Nu))}
ub = {"u" : np.ones((Nt,Nu))}
bounds = dict(uub=[1],ulb=[-.75])

#<<ENDCHUNK>>

# Make optimizers.
x0 = np.array([0,1])
N = {"x":Nx, "u":Nu, "t":Nt}
solver = mpc.nmpc(f=ode_rk4_casadi,N=N,
    verbosity=0,l=l,x0=x0,Pf=Pf,
    lb=lb,ub=ub,runOptimization=False)

#<<ENDCHUNK>>

# Now simulate.
Nsim = 20
times = Delta*Nsim*np.linspace(0,1,Nsim+1)
x = np.zeros((Nsim+1,Nx))
x[0,:] = x0
u = np.zeros((Nsim,Nu))
for t in range(Nsim):
    # Fix initial state.
    solver.fixvar("x",0,x[t,:])
    
    #<<ENDCHUNK>>    
    
    # Solve nlp.
    solver.solve()
    
    #<<ENDCHUNK>>    
    
    # Print stats.
    print "%d: %s" % (t,solver.stats["status"])
    u[t,:] = solver.var["u",0,:]
    
    #<<ENDCHUNK>>    
    
    # Simulate.
    x[t+1,:] = vdp.sim(x[t,:],u[t,:])

#<<ENDCHUNK>>
    
# Plots.
mpc.plots.mpcplot(x.T,u.T,times)
