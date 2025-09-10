from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from .ir import (
    IRInstr, Label as IRLabel, Goto as IRGoto, IfFalse as IRIfFalse,
    AssignInstr as IRAssign, BinOp as IRBin, UnaryOp as IRUnary, PrintInstr as IRPrint, ReturnInstr as IRReturn,
    FuncStart as IRFuncStart, FuncEnd as IRFuncEnd, CallInstr as IRCall
)

# ---- Bytecode ----

@dataclass
class BCInstr: ...

@dataclass
class BLabel(BCInstr):
    name: str
    def __str__(self): return f"{self.name}:"

@dataclass
class BJmp(BCInstr):
    label: str
    def __str__(self): return f"JMP {self.label}"

@dataclass
class BIfFalse(BCInstr):
    cond: str
    label: str
    def __str__(self): return f"IFFALSE {self.cond} {self.label}"

@dataclass
class BMov(BCInstr):
    dst: str; src: str
    def __str__(self): return f"MOV {self.dst}, {self.src}"

@dataclass
class BUnary(BCInstr):
    dst: str; op: str; src: str
    def __str__(self): return f"UNARY {self.dst}, {self.op}, {self.src}"

@dataclass
class BBin(BCInstr):
    dst: str; op: str; left: str; right: str
    def __str__(self): return f"BIN {self.dst}, {self.op}, {self.left}, {self.right}"

@dataclass
class BPrint(BCInstr):
    value: str
    def __str__(self): return f"PRINT {self.value}"

@dataclass
class BRet(BCInstr):
    value: Optional[str]
    def __str__(self): return f"RET {self.value if self.value is not None else ''}".rstrip()

@dataclass
class BFunc(BCInstr):
    name: str
    params: List[str]
    def __str__(self): return f"FUNC {self.name}({', '.join(self.params)})"

@dataclass
class BEndFunc(BCInstr):
    name: str
    def __str__(self): return f"ENDFUNC {self.name}"

@dataclass
class BCall(BCInstr):
    dst: Optional[str]
    name: str
    args: List[str]
    def __str__(self):
        dst = self.dst if self.dst is not None else '_'
        return f"CALL {dst} = {self.name}({', '.join(self.args)})"

Bytecode = List[BCInstr]

class Codegen:
    def __init__(self): self.out: Bytecode = []
    def emit(self, ins: BCInstr): self.out.append(ins)

    def gen(self, ir: List[IRInstr]) -> Bytecode:
        for ins in ir:
            if isinstance(ins, IRLabel): self.emit(BLabel(ins.name))
            elif isinstance(ins, IRGoto): self.emit(BJmp(ins.label))
            elif isinstance(ins, IRIfFalse): self.emit(BIfFalse(ins.cond, ins.label))
            elif isinstance(ins, IRAssign): self.emit(BMov(ins.dst, ins.src))
            elif isinstance(ins, IRUnary): self.emit(BUnary(ins.dst, ins.op, ins.operand))
            elif isinstance(ins, IRBin): self.emit(BBin(ins.dst, ins.op, ins.left, ins.right))
            elif isinstance(ins, IRPrint): self.emit(BPrint(ins.value))
            elif isinstance(ins, IRReturn): self.emit(BRet(ins.value))
            elif isinstance(ins, IRFuncStart): self.emit(BFunc(ins.name, ins.params))
            elif isinstance(ins, IRFuncEnd): self.emit(BEndFunc(ins.name))
            elif isinstance(ins, IRCall): self.emit(BCall(ins.dst, ins.name, ins.args))
        return self.out

# API

def codegen(ir: List[IRInstr]) -> Bytecode:
    return Codegen().gen(ir)