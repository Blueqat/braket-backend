"""Blueqat Backend for converting the circuit to Braket Circuit"""
from functools import singledispatch
from typing import Union

from blueqat.gate import *
from blueqat.backends.backendbase import Backend
from braket.circuits import Circuit as BraketCircuit


class BraketConverterBackend(Backend):
    @staticmethod
    def run(gates: list[Operation], n_qubits: int):
        measured = [0] * n_qubits
        c = BraketCircuit()
        for g in gates:
            pass


name_alias = {
    "r": "phaseshift",
    "sdg": "si",
    "sx": "v",
    "sxdg": "vi",
    "tdg": "ti",
    "cr": "cphaseshift",
    "cx": "cnot",
    "rxx": "xx",
    "ryy": "yy",
    "rzz": "zz",
}


@singledispatch
def _apply(op: Operation, n_qubits: int, c: BraketCircuit) -> None:
    raise TypeError(op)


@_apply.register
def _apply_1qubitgate(g: Union[HGate, IGate, PhaseGate, RXGate, RYGate, RZGate,
                               SGate, SDagGate, SXGate, SXDagGate, TGate,
                               TDagGate, XGate, YGate, ZGate], n_qubits: int,
                      c: BraketCircuit) -> None:
    name = name_alias.get(str(g.lowername)) or str(g.lowername)
    method = getattr(c, name)
    for t in g.target_iter(n_qubits):
        method(*g.params, t)


@_apply.register
def _apply_2qubitgate(g: Union[CPhaseGate, CXGate, CYGate, CZGate,
                               RXXGate, RYYGate, RZZGate, SwapGate, ZZGate],
                      n_qubits: int, c: BraketCircuit) -> None:
    name = name_alias.get(str(g.lowername)) or str(g.lowername)
    method = getattr(c, name)
    for t in g.control_target_iter(n_qubits):
        method(*g.params, t)


@_apply.register
def _apply_ccx(g: ToffoliGate, n_qubits: int, c: BraketCircuit) -> None:
    c1, c2, t = g.targets
    c.ccnot(c1, c2, t)
