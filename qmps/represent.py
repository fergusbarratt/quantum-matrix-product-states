from .tools import cT, direct_sum, unitary_extension

import numpy as np

from math import log as mlog
def log2(x): return mlog(x, 2)

from numpy import concatenate, allclose, tensordot, swapaxes
from scipy.linalg import null_space, norm
import cirq

def sampled_tomography_env_objective_function(U, V, reps=10000):
    """sampled_environment_objective_function: return norm of diffe       rence of (sampled) bloch vectors
       of qubit 0 in 

        | | |   | | | 
        | ---   | | |       
        |  v    | | |  
        | ---   | | |  
        | | |   | | |           (2)
        --- |   --- |  
         u  |    v  |  
        --- |   --- |  
        | | | = | | |             
        ρ | |   σ | |  

    """
    qbs = cirq.LineQubit.range(3)
    r = 0

    LHS, RHS = cirq.Circuit(), cirq.Circuit()
    LHS.append([State2(U, V)(*qbs)])
    RHS.append([Environment2(V)(*qbs[:2])])

    LHS = sampled_bloch_vector_of(qbs[0], LHS, reps)
    RHS = sampled_bloch_vector_of(qbs[0], RHS, reps)
    return norm(LHS-RHS)

def full_tomography_env_objective_function(U, V):
    """full_environment_objective_function: return norm of difference of bloch vectors
       of qubit 0 in 

        | | |   | | | 
        | ---   | | |       
        |  v    | | |  
        | ---   | | |  
        | | |   | | |           (2)
        --- |   --- |  
         u  |    v  |  
        --- |   --- |  
        | | | = | | |             
        j | |   j | |  

    """
    qbs = cirq.LineQubit.range(3)
    r = 0

    LHS, RHS = cirq.Circuit(), cirq.Circuit()
    LHS.append([State(U, V)(*qbs)])
    RHS.append([V(*qbs[:2])])

    sim = cirq.Simulator()
    LHS = sim.simulate(LHS).bloch_vector_of(qbs[0])
    RHS = sim.simulate(RHS).bloch_vector_of(qbs[0])
    return norm(LHS-RHS)

class Tensor(cirq.Gate):
    def __init__(self, unitary, symbol):
        self.U = unitary
        self.n_qubits = int(log2(unitary.shape[0]))
        self.symbol = symbol

    def _unitary_(self):
        return self.U

    def num_qubits(self):
        return self.n_qubits

    def _circuit_diagram_info_(self, args):
        return [self.symbol] * self.n_qubits

    def __pow__(self, power, modulo=None):
        if power == -1:
            return self.__class__(self.U.conj().T, symbol=self.symbol + '†')
        else:
            return self.__class__(np.linalg.multi_dot([self.U] * power))

class StateTensor(Tensor):
    pass

class Environment(Tensor):
    pass

class FullStateTensor(StateTensor):
    """StateTensor: represent state tensor as a unitary"""

    def __init__(self, unitary, symbol='U'):
        super().__init__(unitary, symbol)

    def raise_power(self, power):
        return PowerCircuit(state=self, power=power)


class ShallowStateTensor(StateTensor):
    """ShallowStateTensor: shallow state tensor based on the QAOA circuit"""

    def __init__(self, bond_dim, βγs):
        self.βγs = βγs
        self.p = len(βγs)
        self.n_qubits = int(log2(bond_dim)) + 1

    def num_qubits(self):
        return self.n_qubits

    def _decompose_(self, qubits):
        return [[cirq.X(qubit) ** β for qubit in qubits] + \
                [cirq.ZZ(qubits[i], qubits[i + 1]) ** γ for i in range(self.n_qubits - 1)]
                for β, γ in split_2s(self.βγs)]

    def _circuit_diagram_info_(self, args):
        return ['U'] * self.n_qubits

class FullEnvironment(Environment):
    """Environment: represents the environment tensor as a unitary"""

    def __init__(self, unitary, symbol='V'):
        super().__init__(unitary, symbol)



class ShallowEnvironment(Environment):
    """ShallowEnvironmentTensor: shallow environment tensor based on the QAOA circuit"""

    def __init__(self, bond_dim, βγs):
        self.βγs = βγs
        self.p = len(βγs)
        self.n_qubits = 2 * int(log2(bond_dim))

    def num_qubits(self):
        return self.n_qubits

    def _decompose_(self, qubits):
        return [[cirq.X(qubit) ** β for qubit in qubits] +
                [cirq.ZZ(qubits[i], qubits[i + 1]) ** γ for i in range(self.n_qubits - 1)]
                for β, γ in split_2s(self.βγs)]

    def _circuit_diagram_info_(self, args):
        return ['V'] * self.n_qubits

class PowerCircuit(cirq.Gate):
    def __init__(self, state:FullStateTensor, power):
        self.power = power
        self.state = state

    def _decompose_(self, qubits):
        n_u_qubits = self.state.num_qubits()
        return (FullStateTensor(self.state.U)(*qubits[i:n_u_qubits + i]) for i in reversed(range(self.power)))

    def num_qubits(self):
        return self.state.num_qubits() + (self.power - 1)

    def _set_power(self, power):
        self.power = power


class State(cirq.Gate):
    def __init__(self, u: StateTensor, v: Environment, n=1):
        self.u = u
        self.v = v
        self.n_phys_qubits = n
        self.bond_dim = int(2 ** (u.num_qubits() - 1))

    def _decompose_(self, qubits):
        v_qbs = self.v.num_qubits()
        u_qbs = self.u.num_qubits()
        n = self.n_phys_qubits
        return [self.v(*qubits[n:n+v_qbs])] + [self.u(*qubits[i:i+u_qbs]) for i in range(n)]

    def num_qubits(self):
        return self.n_phys_qubits + self.v.num_qubits()
