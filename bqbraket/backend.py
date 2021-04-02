"""Blueqat Backend for converting the circuit to Braket Circuit"""
from functools import singledispatch

from blueqat import Circuit as BlueqatCircuit
from blueqat import BlueqatGlobalSetting
from blueqat.gate import *
from blueqat.backends.backendbase import Backend
from braket.circuits import Circuit as BraketCircuit


class BraketConverterBackend(Backend):
    @staticmethod
    def run(gates: list[Operation], n_qubits: int) -> BraketCircuit:
        c = BraketCircuit()
        for g in gates:
            _apply(g, n_qubits, c)
        return c


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
        method(*g.params, t)


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
        method(*g.params, *t)


@_apply.register
def _apply_ccx(g: ToffoliGate, _: int, c: BraketCircuit) -> None:
    c1, c2, t = g.targets
    c.ccnot(c1, c2, t)


def register_backend(name: str = 'braketconverter',
                     allow_overwrite: bool = False) -> None:
    """Register BraketConverterBackend to Blueqat."""
    BlueqatGlobalSetting.register_backend(name, BraketConverterBackend,
                                          allow_overwrite)


def convert(c: BlueqatCircuit) -> BraketCircuit:
    """Convert circuit."""
    return BraketConverterBackend.run(c.ops, c.n_qubits)
