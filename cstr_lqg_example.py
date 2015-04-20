# This is a CSTR LQG simulation based on Example 1.11 from Rawlings and Mayne.
#

import mpcsim as sim
import mpctools as mpc
import numpy as np
from scipy import linalg

def runsim(k, simcon, opnclsd, options):

    print "runsim: iteration %d " % k

    # unpack stuff from simulation container

    mvlist = simcon.mvlist
    dvlist = simcon.dvlist
    cvlist = simcon.cvlist
    xvlist = simcon.xvlist
    deltat = simcon.deltat

    # check for changes

    chsum = 0
    for mv in mvlist:
        chsum += mv.chflag
        mv.chflag = 0
    for dv in dvlist:
        chsum += dv.chflag
        dv.chflag = 0
    for cv in cvlist:
        chsum += cv.chflag
        cv.chflag = 0
    for xv in xvlist:
        chsum += xv.chflag
        xv.chflag = 0

    chsum += options.chflag
    options.chflag = 0

    # initialize values on first execution or when something changes

    if (k == 0 or chsum > 0):

        print "runsim: initialization"

        # Define problem size parameters

        Nx = 3
        Nu = 2
        Nd = 1
        Ny = Nx

        # Define sampe time in minutes
        
        Delta = deltat

        # Define a small number
        
        eps = 1e-6

        # Define model parameters
        
        T0 = 350
        c0 = 1
        r = .219
        k0 = 7.2e10
        E = 8750
        U = 54.94
        rho = 1000
        Cp = .239
        dH = -5e4

        # Define ode for CSTR simulation
        
        def ode(x,u,d):

            # Grab the states, controls, and disturbance.

            [c, T, h] = x[0:Nx]
            [Tc, F] = u[0:Nu]
            [F0] = d[0:Nd]

            # Now create the ODE.

            rate = k0*c*np.exp(-E/T)

            dxdt = [
                F0*(c0 - c)/(np.pi*r**2*h) - rate,
                F0*(T0 - T)/(np.pi*r**2*h)
                    - dH/(rho*Cp)*rate
                    + 2*U/(r*rho*Cp)*(Tc - T),    
                (F0 - F)/(np.pi*r**2)
            ]

            return dxdt

        # Create casadi function and simulator.

        ode_casadi = mpc.getCasadiFunc(ode,[Nx,Nu,Nd],["x","u","d"],funcname="ode")
        cstr = mpc.DiscreteSimulator(ode, Delta, [Nx,Nu,Nd], ["x","u","d"])

        # Set the steady-state values.

        cs = .878
        Ts = 324.5
        hs = .659
        Fs = .1
        Tcs = 300
        F0s = .1

        # Calculate steady-state values to high precision
        
        for i in range(10):
            [cs,Ts,hs] = cstr.sim([cs,Ts,hs],[Tcs,Fs],[F0s]).tolist()
        xs = np.array([cs,Ts,hs])
        us = np.array([Tcs,Fs])
        ds = np.array([F0s])
        ys = xs

        # Now get a linearization at this steady state.

        ss = mpc.util.getLinearization(ode_casadi, xs, us, ds, Delta)
        A = ss["A"]
        B = ss["B"]
        Bp = ss["Bp"]
        C = np.eye(Nx)

        # Weighting matrices for controller.

        Q = np.diag([cvlist[0].qvalue, 0.0, cvlist[1].qvalue])
        R = np.diag([mvlist[0].rvalue, mvlist[1].rvalue])

        # Apply gain mismatch factor

        B = options.gfac*B

        # Calculate lqr control

        [K, Pi] = mpc.util.dlqr(A,B,Q,R)

        # Specify which disturbance model to use.

#        useGoodDisturbanceModel = True # Can be false to pick the bad one with offset.

        # Set the disturbance model

#        if useGoodDisturbanceModel:

        if (options.dmod == 1.0):
            Nid = Ny # Number of integrating disturbances.
        else:
            Nid = Nu 

        Bd = np.zeros((Nx,Nid))  
        Cd = np.zeros((Ny,Nid))

#        if useGoodDisturbanceModel:

        if (options.dmod == 1.0):
            Cd[0,0] = 1
            Cd[2,1] = 1
            Bd[:,2] = B[:,1] # or Bp[:,0]
        else:
            Cd[0,0] = 1
            Cd[2,1] = 1

        # Check rank condition for augmented system.

        svds = linalg.svdvals(np.bmat([[np.eye(Nx) - A, -Bd],[C,Cd]]))
        rank = sum(svds > 1e-10)
        if rank < Nx + Nid:
            print "***Warning: augmented system is not detectable!"

        # Build augmented system.

#        Qw = eps*np.eye(Nx + Nid)
#        Qw[-1,-1] = 1
#        Rv = eps*np.diag(xs**2)

        if (Nid == 2):
            Qw = np.diag([xvlist[0].mnoise, xvlist[1].mnoise, xvlist[2].mnoise,
                    eps, 1])
        if (Nid == 3):
            Qw = np.diag([xvlist[0].mnoise, xvlist[1].mnoise, xvlist[2].mnoise,
                    eps, eps, 1])
        Rv = np.diag([cvlist[0].mnoise, eps, cvlist[1].mnoise])

        Aaug = np.bmat([[A,Bd],[np.zeros((Nid,Nx)),np.eye(Nid)]]).A 
        Baug = np.vstack((B,np.zeros((Nid,Nu))))
        Caug = np.hstack((C,Cd))

        # Get steady-state Kalman filter.

        [L, P] = mpc.util.dlqe(Aaug, Caug, Qw, Rv)
        Lx = L[:Nx,:]
        Ld = L[Nx:,:]

        # Steady-state target selector matrices.

        contVars = [0,2] # Concentration and height.
        H = np.zeros((Nu,Ny))
        for i in range(len(contVars)):
            H[i,contVars[i]] = 1
        G = np.bmat([[np.eye(Nx) - A, -B],[H.dot(C), np.zeros((H.shape[0], Nu))]]).A

        # Closed-loop matrix

        Acl = A + B.dot(K)

        # Store initial values for variables

        x_k = np.zeros((Nx))
        xhat_k = np.zeros((Nx))
        dhat_k = np.zeros((Nid))

        xvlist[0].value = xs[0]
        xvlist[1].value = xs[1]
        xvlist[2].value = xs[2]
        xvlist[0].est   = xs[0]
        xvlist[1].est   = xs[1]
        xvlist[2].est   = xs[2]
        mvlist[0].value = us[0]
        mvlist[1].value = us[1]
        dvlist[0].est   = dhat_k

        # Store values in simulation container

        simcon.proc   = cstr
        simcon.mod = []
        simcon.mod.append(A)
        simcon.mod.append(B)
        simcon.mod.append(C)
        simcon.mod.append(Bd)
        simcon.mod.append(Cd)
        simcon.mod.append(us)
        simcon.mod.append(xs)
        simcon.mod.append(ys)
        simcon.mod.append(ds)
        simcon.mod.append(Lx)
        simcon.mod.append(Ld)
        simcon.mod.append(H)
        simcon.mod.append(G)
        simcon.mod.append(Nx)
        simcon.mod.append(K)
        simcon.mod.append(Acl)

    # Get stored values

    A     = simcon.mod[0]
    B     = simcon.mod[1]
    C     = simcon.mod[2]
    Bd    = simcon.mod[3]
    Cd    = simcon.mod[4]
    us    = simcon.mod[5]
    xs    = simcon.mod[6]
    ys    = simcon.mod[7]
    ds    = simcon.mod[8]
    Lx    = simcon.mod[9]
    Ld    = simcon.mod[10]
    H     = simcon.mod[11]
    G     = simcon.mod[12]
    Nx    = simcon.mod[13]
    K     = simcon.mod[14]
    Acl   = simcon.mod[15]

    # Get variable values

    x_km1    = [xvlist[0].value, xvlist[1].value, xvlist[2].value] - xs
    u_km1    = [mvlist[0].value, mvlist[1].value] - us
    d_km1    = dvlist[0].value - ds
    xhat_km1 = [xvlist[0].est, xvlist[1].est, xvlist[2].est] - xs
    dhat_km1 = dvlist[0].est

    # Advance the process.

    x_k = simcon.proc.sim(x_km1 + xs, u_km1 + us, d_km1 + ds) - xs
    y_k = C.dot(x_k)

    # Add noise to the outputs

    if (options.fnoise > 0.0):

        y_k[0] += options.fnoise*np.random.normal(0.0, cvlist[0].noise)
        y_k[2] += options.fnoise*np.random.normal(0.0, cvlist[1].noise)
    
    # Estimate the state.

    xhatm_k = A.dot(xhat_km1) + Bd.dot(dhat_km1) + B.dot(u_km1)
    dhatm_k = dhat_km1
    err_k = y_k - C.dot(xhatm_k) - Cd.dot(dhatm_k)
    xhat_k = xhatm_k + Lx.dot(err_k)
    dhat_k = dhatm_k + Ld.dot(err_k)
    yhat_k = C.dot(xhat_k) + Cd.dot(dhat_k)
    
    # Initialize the input

    u_k = u_km1

    # Update open and closed-loop predictions

    mvlist[0].olpred[0] = u_k[0] + us[0]
    mvlist[1].olpred[0] = u_k[1] + us[1]
    dvlist[0].olpred[0] = d_km1  + ds[0]
    xvlist[0].olpred[0] = xhat_k[0] + xs[0]
    xvlist[1].olpred[0] = xhat_k[1] + xs[1]
    xvlist[2].olpred[0] = xhat_k[2] + xs[2]
    cvlist[0].olpred[0] = yhat_k[0] + ys[0]
    cvlist[1].olpred[0] = yhat_k[2] + ys[2]

    mvlist[0].clpred[0] = mvlist[0].olpred[0]
    mvlist[1].clpred[0] = mvlist[1].olpred[0]
    dvlist[0].clpred[0] = dvlist[0].olpred[0]
    xvlist[0].clpred[0] = xvlist[0].olpred[0]
    xvlist[1].clpred[0] = xvlist[1].olpred[0]
    xvlist[2].clpred[0] = xvlist[2].olpred[0]
    cvlist[0].clpred[0] = cvlist[0].olpred[0]
    cvlist[1].clpred[0] = cvlist[1].olpred[0]

    xof_km1 = xhat_k

    for i in range(0,(xvlist[0].Nf - 1)):
    
        xof_k = A.dot(xof_km1) + B.dot(u_km1) + Bd.dot(dhat_k)
        yof_k = C.dot(xof_k) + Cd.dot(dhat_k)

        mvlist[0].olpred[i+1] = u_k[0] + us[0]
        mvlist[1].olpred[i+1] = u_k[1] + us[1]
        dvlist[0].olpred[i+1] = d_km1  + ds[0]
        xvlist[0].olpred[i+1] = xof_k[0] + xs[0]
        xvlist[1].olpred[i+1] = xof_k[1] + xs[1]
        xvlist[2].olpred[i+1] = xof_k[2] + xs[2]
        cvlist[0].olpred[i+1] = yof_k[0] + ys[0]
        cvlist[1].olpred[i+1] = yof_k[2] + ys[2]

        mvlist[0].clpred[i+1] = mvlist[0].olpred[i+1]
        mvlist[1].clpred[i+1] = mvlist[1].olpred[i+1]
        dvlist[0].clpred[i+1] = dvlist[0].olpred[i+1]
        xvlist[0].clpred[i+1] = xvlist[0].olpred[i+1]
        xvlist[1].clpred[i+1] = xvlist[1].olpred[i+1]
        xvlist[2].clpred[i+1] = xvlist[2].olpred[i+1]
        cvlist[0].clpred[i+1] = cvlist[0].olpred[i+1]
        cvlist[1].clpred[i+1] = cvlist[1].olpred[i+1]

        xof_km1 = xof_k

    # calculate mpc input adjustment in control is on

    if (opnclsd.status.get() == 1):

        # Steady-state target.

        ysp = [cvlist[0].setpoint, 0.0, cvlist[1].setpoint] - ys
        rhs = np.concatenate((Bd.dot(dhat_k), H.dot(ysp - Cd.dot(dhat_k))))
        qsp = linalg.solve(G,rhs)
        xsp = qsp[:Nx]
        usp = qsp[Nx:]

        # Regulator.

        u_k = K.dot(xhat_k - xsp) + usp

        # Clip the inputs if necessary

        for i in range(0,simcon.nmvs):

            if(u_k[i] + us[i] > mvlist[i].maxlim): u_k[i] = mvlist[i].maxlim - us[i]
            if(u_k[i] + us[i] < mvlist[i].minlim): u_k[i] = mvlist[i].minlim - us[i]

        # Update closed-loop predictions

        mvlist[0].clpred[0] = u_k[0] + us[0]  
        mvlist[1].clpred[0] = u_k[1] + us[1]
        xvlist[0].clpred[0] = xhat_k[0] + xs[0]
        xvlist[1].clpred[0] = xhat_k[1] + xs[1]
        xvlist[2].clpred[0] = xhat_k[2] + xs[2]
        cvlist[0].clpred[0] = yhat_k[0] + ys[0]
        cvlist[1].clpred[0] = yhat_k[2] + ys[2]

        xcf_km1 = xhat_k - xsp
    
        for i in range(0,(xvlist[0].Nf - 1)):

            xcf_k = Acl.dot(xcf_km1)
            ycf_k = C.dot(xcf_k)
            ucf_k = K.dot(xcf_k)

            mvlist[0].clpred[i+1] = ucf_k[0] + usp[0] + us[0]
            mvlist[1].clpred[i+1] = ucf_k[1] + usp[1] + us[1]
            xvlist[0].clpred[i+1] = xcf_k[0] + xsp[0] + xs[0]
            xvlist[1].clpred[i+1] = xcf_k[1] + xsp[1] + xs[1]
            xvlist[2].clpred[i+1] = xcf_k[2] + xsp[2] + xs[2]
            cvlist[0].clpred[i+1] = ycf_k[0] + ysp[0] + ys[0]
            cvlist[1].clpred[i+1] = ycf_k[2] + ysp[2] + ys[2]

            xcf_km1 = xcf_k

    # Store variable values

    mvlist[0].value = u_k[0] + us[0]
    mvlist[1].value = u_k[1] + us[1]
    xvlist[0].value = x_k[0] + xs[0]
    xvlist[1].value = x_k[1] + xs[1]
    xvlist[2].value = x_k[2] + xs[2]
    xvlist[0].est   = xhat_k[0] + xs[0]
    xvlist[1].est   = xhat_k[1] + xs[1]
    xvlist[2].est   = xhat_k[2] + xs[2]
    dvlist[0].est   = dhat_k
    cvlist[0].value = y_k[0] + ys[0]
    cvlist[1].value = y_k[2] + ys[2]

# set up cstr mpc example

simname = 'CSTR LQG Example'

# define variables

MV1 = sim.MVobj(name='Tc', desc='mv - coolant temp.', units='(K)', 
               pltmin=299.0, pltmax=301.0, minlim=299.2, maxlim=300.8,
               value=300.0, Nf=60)

MV2 = sim.MVobj(name='F', desc='mv - outlet flow', units='(kL/min)', 
               pltmin=0.090, pltmax=0.125, minlim=0.095, maxlim=0.120,
               value=0.1, Nf=60)

DV1 = sim.MVobj(name='F0', desc='dv - inlet flow', units='(kL/min)', 
               pltmin=0.090, pltmax=0.125, minlim=0.0, maxlim=1.0,
               value=0.1, Nf=60)

XV1 = sim.XVobj(name='c', desc='xv - concentration A', units='(mol/L)', 
               pltmin=0.87, pltmax=0.88, 
               value=0.877825, Nf=60)

XV2 = sim.XVobj(name='T', desc='xv - temperature', units='(K)', 
               pltmin=324, pltmax=327, 
               value=324.496, Nf=60)

XV3 = sim.XVobj(name='h', desc='xv - level', units='(m)', 
               pltmin=0.64, pltmax=0.74, 
               value=0.659, Nf=60)

CV1 = sim.XVobj(name='c', desc='cv - concentration A', units='(mol/L)', 
               pltmin=0.87, pltmax=0.88, noise =.0001,
               value=0.877825, setpoint=0.877825, Nf=60)

CV2 = sim.XVobj(name='h', desc='cv - level', units='(m)', 
               pltmin=0.64, pltmax=0.74, noise=.01,
               value=0.659, setpoint=0.659, Nf=60)

# load up variable lists

MVlist = [MV1,MV2]
DVlist = [DV1]
XVlist = [XV1,XV2,XV3]
CVlist = [CV1,CV2]
DeltaT = 1
N      = 120
refint = 10.0
simcon = sim.SimCon(simname=simname,
                    mvlist=MVlist, dvlist=DVlist, cvlist=CVlist, xvlist=XVlist,
                    N=N, refint=refint, runsim=runsim, deltat=DeltaT)

# build the GUI and start it up

sim.makegui(simcon)