#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 08:43:37 2020

@author: jamie
"""

from ClassicalTDVPStripped import Optimizer, tensor
from qmps.ground_state import Hamiltonian
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from tqdm import tqdm
import pickle


def ground_state():
    I = np.eye(2)
    g0, g1 = 1.5, 0.2
    
    H0 = Hamiltonian({'ZZ':-1, 'X':g0}).to_matrix()
    
    H = tensor([H0, I, I]) + tensor([I, H0, I]) + tensor([I, I, H0])
    
    Op = Optimizer()
    
    ground_state = Op.optimize.optimize(H.reshape(2,2,2,2,2,2,2,2))

    return ground_state

def loschmidt_evolve(DT, STEPS):
    print("Finding ground state before quench")
    print("\n##################################################\n")

    I = np.eye(2)
    g0, g1 = 1.5, 0.2
    
    H0 = Hamiltonian({'ZZ':-1, 'X':g0}).to_matrix()
    
    H = tensor([H0, I, I]) + tensor([I, H0, I]) + tensor([I, I, H0])
    
    Op = Optimizer()
    
    ground_state = Op.optimize.optimize(H.reshape(2,2,2,2,2,2,2,2))
    plt.plot(Op.optimize.energy_opt)
    
    print("Ground State Reached")
    print("\n##################################################\n")
    
    print("Evolving under quenched hamiltonian...")
    loschmidt_results = []
    loschmidt_results.append(ground_state)
    
    H1 = Hamiltonian({'ZZ':-1, 'X':g1}).to_matrix()
    
    H = tensor([H1, I, I]) + tensor([I, H1, I]) + tensor([I, I, H1])
    
    W = expm(1j * H * DT).reshape(2,2,2,2,2,2,2,2)
    
    init_params = ground_state.x
    for i in tqdm(range(STEPS)):
        
        U1, U2 = Op.evolve.paramU(init_params)
        
        record_optimize = np.random.rand(1)
        
        if record_optimize < 0.1:
            res_e = Op.evolve.exact_optimize(W, 
                                             U1.reshape(2,2,2,2), 
                                             U2.reshape(2,2,2,2), 
                                             initial_params = init_params,
                                             record = True)
            
            plt.figure()
            plt.plot(Op.evolve.cf_convergence)
            plt.title(f"Energy Convergence for run {i}")
            plt.show()

        else:
            res_e = Op.evolve.exact_optimize(W, 
                                             U1.reshape(2,2,2,2), 
                                             U2.reshape(2,2,2,2), 
                                             initial_params = init_params,
                                             record = False)

        
        loschmidt_results.append(res_e)
        init_params = res_e.x
        
    with open("loschmidt2.pkl", "wb") as f:
        pickle.dump(loschmidt_results, f)
    
    return loschmidt_results


def load_echos(file):
    with open(file, "rb") as f:
        res = pickle.load(f)

    return res


def plot_loschmidt():
    Op = Optimizer()
    gs = ground_state()
    evos = load_echos("loschmidt2.pkl")
    U1, U2 = Op.represent.paramU(gs.x)
    
    results = []
    log_res = []
    for e in evos:
        U1_, U2_ = Op.represent.paramU(e.x)
        U1_ = U1_.conj().T.reshape(2,2,2,2)
        U2_ = U2_.conj().T.reshape(2,2,2,2)
    
        overlap, _ = Op.represent.RE.exact_environment(U1.reshape(2,2,2,2), 
                                                       U2.reshape(2,2,2,2), 
                                                       U1_, U2_)
        
        results.append(overlap)
        
        log_res.append(-np.log10(np.abs(overlap)**2))
        
    plt.plot(log_res)
    return results, log_res


if __name__ == "__main__":
    l = plot_loschmidt()
        
    
    
    