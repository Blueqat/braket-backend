"""Blueqat Backend for converting the circuit to Braket Circuit"""
from functools import singledispatch
from math import pi
from typing import Dict, Iterable, List, Optional, Tuple

from blueqat import Circuit as BlueqatCircuit
from blueqat import BlueqatGlobalSetting
from blueqat.gate import *
from blueqat.backends.backendbase import Backend
from blueqat.backends.onequbitgate_decomposer import ryrz_decomposer
from braket.circuits import Circuit as BraketCircuit


BASIS: Dict[str, List[str]] = {
    'ionq': ['cx', 'zz', 'swap'],
    'rigetti': ['cx', 'cz', 'cphase', 'swap'],
}


class BraketConverterBackend(Backend):
    @staticmethod
    def run(gates: List[Operation], n_qubits: int,
            transpile: Optional[List[str]] = None,
            avoid_empty_circuit: bool = True) -> BraketCircuit:
        if transpile:
            c = BlueqatCircuit(n_qubits=n_qubits, ops=gates)
            c = c.run_with_2q_decomposition(basis=transpile, mat1_decomposer=ryrz_decomposer)
            gates = c.ops
        if len(gates) == 0 and avoid_empty_circuit:
            if n_qubits == 0:
                raise ValueError('0 qubits circuit is always empty.')
            gates = BlueqatCircuit().i[n_qubits - 1].ops
        bc = BraketCircuit()
        for g in gates:
            _apply(g, n_qubits, bc)
        return bc


name_alias = {
    "phase": "phaseshift",
    "sdg": "si",
    "sx": "v",
    "sxdg": "vi",
    "tdg": "ti",
    "cphase": "cphaseshift",
    "cx": "cnot",
    "rxx": "xx",
    "ryy": "yy",
    "rzz": "zz",
}


def normalize_angles(angles: Iterable[float]) -> Tuple:
    """Normalize angle to 0..2π for iterator of angles."""
    return tuple(ang % (2 * pi) for ang in angles)


@singledispatch
def _apply(op: Operation, n_qubits: int, c: BraketCircuit) -> None:
    raise TypeError(op)


@_apply.register(HGate)
@_apply.register(IGate)
@_apply.register(PhaseGate)
@_apply.register(RXGate)
@_apply.register(RYGate)
@_apply.register(RZGate)
@_apply.register(SGate)
@_apply.register(SDagGate)
@_apply.register(SXGate)
@_apply.register(SXDagGate)
@_apply.register(TGate)
@_apply.register(TDagGate)
@_apply.register(XGate)
@_apply.register(YGate)
@_apply.register(ZGate)
def _apply_1qubitgate(g: OneQubitGate, n_qubits: int,
                      c: BraketCircuit) -> None:
    name = name_alias.get(str(g.lowername)) or str(g.lowername)
    method = getattr(c, name)
    for t in g.target_iter(n_qubits):
        method(t, *normalize_angles(g.params))


@_apply.register(CPhaseGate)
@_apply.register(CXGate)
@_apply.register(CYGate)
@_apply.register(CZGate)
@_apply.register(RXXGate)
@_apply.register(RYYGate)
@_apply.register(RZZGate)
@_apply.register(SwapGate)
def _apply_2qubitgate(g: TwoQubitGate, n_qubits: int,
                      c: BraketCircuit) -> None:
    name = name_alias.get(str(g.lowername)) or str(g.lowername)
    method = getattr(c, name)
    for t in g.control_target_iter(n_qubits):
        method(*t, *normalize_angles(g.params))


@_apply.register
def _apply_ccx(g: ToffoliGate, _: int, c: BraketCircuit) -> None:
    c1, c2, t = g.targets
    c.ccnot(c1, c2, t)


@_apply.register
def _apply_cswap(g: CSwapGate, _: int, c: BraketCircuit) -> None:
    c, t1, t2 = g.targets
    c.cswap(c, t1, t2)


def register_backend(name: str = 'braketconverter',
                     allow_overwrite: bool = False) -> None:
    """Register BraketConverterBackend to Blueqat."""
    BlueqatGlobalSetting.register_backend(name, BraketConverterBackend,
                                          allow_overwrite)


def convert(c: BlueqatCircuit,
            transpile: Optional[List[str]] = None,
            avoid_empty_circuit: bool = True) -> BraketCircuit:
    """Convert circuit.

    Args:
    c: Blueqat circuit which to be converted
    transpile: If a list of 2-qubit gates is given, transpile the circuit with
    specified gates as a basis. If None, don't transpile.
    avoid_empty_circuit: If True and given circuit or transpiled circuit is empty,
    insert dummy I gate.

    Returns:
    Converted Braket Circuit
    """
    return BraketConverterBackend.run(c.ops, c.n_qubits, transpile, avoid_empty_circuit)
