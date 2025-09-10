from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from compiler_core.domain.ast_nodes import (
    Program, Block, VarDecl, If, While, For, Print, Return, ExprStmt,
    Assign, Literal, Var, Unary, Binary, Grouping, Stmt, Expr,
    FunctionDecl, Call, Param
)

# ---- IR instructions ----

@dataclass
class IRInstr: ...

@dataclass
class Label(IRInstr):
    name: str
    def __str__(self): return f"{self.name}:"

@dataclass
class Goto(IRInstr):
    label: str
    def __str__(self): return f"goto {self.label}"

@dataclass
class IfFalse(IRInstr):
    cond: str
    label: str
    def __str__(self): return f"iffalse {self.cond} goto {self.label}"

@dataclass
class AssignInstr(IRInstr):
    dst: str
    src: str
    def __str__(self): return f"{self.dst} = {self.src}"

@dataclass
class BinOp(IRInstr):
    dst: str
    op: str
    left: str
    right: str
    def __str__(self): return f"{self.dst} = {self.left} {self.op} {self.right}"

@dataclass
class UnaryOp(IRInstr):
    dst: str
    op: str
    operand: str
    def __str__(self): return f"{self.dst} = {self.op}{self.operand}"

@dataclass
class PrintInstr(IRInstr):
    value: str
    def __str__(self): return f"print {self.value}"

@dataclass
class ReturnInstr(IRInstr):
    value: Optional[str]
    def __str__(self): return f"return {self.value if self.value is not None else ''}".rstrip()

# functions
@dataclass
class FuncStart(IRInstr):
    name: str
    params: List[str]
    def __str__(self): return f"func {self.name}({', '.join(self.params)})"

@dataclass
class FuncEnd(IRInstr):
    name: str
    def __str__(self): return f"endfunc {self.name}"

@dataclass
class CallInstr(IRInstr):
    dst: Optional[str]
    name: str
    args: List[str]
    def __str__(self):
        dst = self.dst if self.dst is not None else '_'
        return f"call {dst} = {self.name}({', '.join(self.args)})"

IR = List[IRInstr]

class IRBuilder:
    def __init__(self):
        self.code: IR = []
        self.temp_counter = 0
        self.label_counter = 0

    def emit(self, i: IRInstr): self.code.append(i)
    def new_temp(self) -> str: self.temp_counter += 1; return f"t{self.temp_counter}"
    def new_label(self, base: str = 'L') -> str: self.label_counter += 1; return f"{base}{self.label_counter}"

    # expr
    def gen_expr(self, e: Expr) -> str:
        if isinstance(e, Literal):
            if e.kind == 'bool': return '1' if bool(e.value) else '0'
            return str(e.value)
        if isinstance(e, Var): return e.name
        if isinstance(e, Assign):
            rhs = self.gen_expr(e.value); self.emit(AssignInstr(e.name, rhs)); return e.name
        if isinstance(e, Unary):
            t = self.new_temp(); self.emit(UnaryOp(t, e.op, self.gen_expr(e.right))); return t
        if isinstance(e, Binary):
            t = self.new_temp(); self.emit(BinOp(t, e.op, self.gen_expr(e.left), self.gen_expr(e.right))); return t
        if isinstance(e, Grouping): return self.gen_expr(e.expr)
        if isinstance(e, Call):
            # if inferred void -> dst None, else temp
            dst = None if getattr(e, 'inferred_type', None) == 'void' else self.new_temp()
            args = [self.gen_expr(a) for a in e.args]
            self.emit(CallInstr(dst, e.name, args))
            return '0' if dst is None else dst
        t = self.new_temp(); self.emit(AssignInstr(t, '0')); return t

    # stmt
    def gen_stmt(self, s: Stmt):
        if isinstance(s, Block):
            for st in s.statements: self.gen_stmt(st); return
        if isinstance(s, VarDecl):
            if s.init is not None:
                v = self.gen_expr(s.init); self.emit(AssignInstr(s.name, v)); return
            return
        if isinstance(s, If):
            else_lbl = self.new_label('Lelse'); end_lbl = self.new_label('Lend')
            c = self.gen_expr(s.cond); self.emit(IfFalse(c, else_lbl))
            self.gen_stmt(s.then_branch); self.emit(Goto(end_lbl))
            self.emit(Label(else_lbl));
            if s.else_branch: self.gen_stmt(s.else_branch)
            self.emit(Label(end_lbl)); return
        if isinstance(s, While):
            start = self.new_label('Lwhile'); end = self.new_label('Lwend')
            self.emit(Label(start)); c = self.gen_expr(s.cond); self.emit(IfFalse(c, end))
            self.gen_stmt(s.body); self.emit(Goto(start)); self.emit(Label(end)); return
        if isinstance(s, For):
            start = self.new_label('Lfor'); end = self.new_label('Lfend')
            if s.init: self.gen_stmt(s.init)
            self.emit(Label(start))
            if s.cond: self.emit(IfFalse(self.gen_expr(s.cond), end))
            self.gen_stmt(s.body)
            if s.post: self.gen_stmt(s.post)
            self.emit(Goto(start)); self.emit(Label(end)); return
        if isinstance(s, Print): self.emit(PrintInstr(self.gen_expr(s.expr))); return
        if isinstance(s, Return):
            v = self.gen_expr(s.expr) if s.expr is not None else None
            self.emit(ReturnInstr(v)); return
        if isinstance(s, ExprStmt): self.gen_expr(s.expr); return
        if isinstance(s, FunctionDecl):
            self.emit(FuncStart(s.name, [p.name for p in s.params]))
            self.gen_stmt(s.body)
            self.emit(FuncEnd(s.name)); return
        # else ignore

    def gen(self, root: Program) -> IR:
        for s in root.body: self.gen_stmt(s)
        return self.code

# API

def ir_gen(typed_root: Program) -> IR:
    return IRBuilder().gen(typed_root)