from __future__ import annotations
import re
from typing import List, Optional, Union

from .ir import IRInstr, Label, Goto, IfFalse, AssignInstr, BinOp, UnaryOp, PrintInstr, ReturnInstr

TEMP_RE = re.compile(r"^t\d+$")

# ---------- Utility: constant evaluation ----------

def is_const(x: str) -> bool:
    if x is None: return False
    try:
        float(x)
        return True
    except Exception:
        return x in ('0', '1')  # bools are already 0/1


def const_val(x: str) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        if x in ('0', '1'):
            return float(x)
        return None


def fmt_num(x: float) -> str:
    # keep int-looking numbers as ints
    if x.is_integer():
        return str(int(x))
    return str(x)


def eval_bin(op: str, a: str, b: str) -> Optional[str]:
    av = const_val(a)
    bv = const_val(b)
    if av is None or bv is None:
        return None
    # arithmetic
    if op == '+': return fmt_num(av + bv)
    if op == '-': return fmt_num(av - bv)
    if op == '*': return fmt_num(av * bv)
    if op == '/':
        if bv == 0: return None
        return fmt_num(av / bv)
    if op == '%':
        if av.is_integer() and bv.is_integer() and bv != 0:
            return fmt_num(float(int(av) % int(bv)))
        return None
    # comparisons -> 0/1
    if op in ('<', '<=', '>', '>=', '==', '!='):
        res = None
        if op == '<': res = av < bv
        elif op == '<=': res = av <= bv
        elif op == '>': res = av > bv
        elif op == '>=': res = av >= bv
        elif op == '==': res = av == bv
        elif op == '!=': res = av != bv
        return '1' if res else '0'
    # logical (treat nonzero as true)
    if op in ('&&', '||'):
        aval = av != 0
        bval = bv != 0
        if op == '&&':
            return '1' if (aval and bval) else '0'
        else:
            return '1' if (aval or bval) else '0'
    return None


def eval_unary(op: str, a: str) -> Optional[str]:
    av = const_val(a)
    if av is None:
        return None
    if op == '!':
        return '0' if av != 0 else '1'
    if op == '+':
        return fmt_num(+av)
    if op == '-':
        return fmt_num(-av)
    return None


def is_temp(name: str) -> bool:
    return isinstance(name, str) and TEMP_RE.match(name) is not None

# ---------- Pass 1: Constant folding & algebraic simplifications ----------

def constant_fold(ir: List[IRInstr]) -> List[IRInstr]:
    out: List[IRInstr] = []
    for ins in ir:
        if isinstance(ins, BinOp):
            # algebraic identities
            if is_const(ins.left) and is_const(ins.right):
                val = eval_bin(ins.op, ins.left, ins.right)
                if val is not None:
                    out.append(AssignInstr(ins.dst, val))
                    continue
            # x + 0, x - 0, x * 1, x / 1, x * 0, 0 * x
            if ins.op in ('+', '-') and is_const(ins.right) and const_val(ins.right) == 0:
                out.append(AssignInstr(ins.dst, ins.left))
                continue
            if ins.op == '*' and is_const(ins.right) and const_val(ins.right) == 1:
                out.append(AssignInstr(ins.dst, ins.left))
                continue
            if ins.op == '/' and is_const(ins.right) and const_val(ins.right) == 1:
                out.append(AssignInstr(ins.dst, ins.left))
                continue
            if ins.op == '*' and is_const(ins.right) and const_val(ins.right) == 0:
                out.append(AssignInstr(ins.dst, '0'))
                continue
            if ins.op == '*' and is_const(ins.left) and const_val(ins.left) == 0:
                out.append(AssignInstr(ins.dst, '0'))
                continue
            out.append(ins)
            continue
        if isinstance(ins, UnaryOp):
            if is_const(ins.operand):
                val = eval_unary(ins.op, ins.operand)
                if val is not None:
                    out.append(AssignInstr(ins.dst, val))
                    continue
            out.append(ins)
            continue
        # other instructions unchanged
        out.append(ins)
    return out

# ---------- Pass 2: Dead code elimination (temporaries) ----------

def used_vars(ins: IRInstr) -> List[str]:
    if isinstance(ins, BinOp):
        return [ins.left, ins.right]
    if isinstance(ins, UnaryOp):
        return [ins.operand]
    if isinstance(ins, AssignInstr):
        return [ins.src] if isinstance(ins.src, str) else []
    if isinstance(ins, IfFalse):
        return [ins.cond]
    if isinstance(ins, PrintInstr):
        return [ins.value]
    if isinstance(ins, ReturnInstr) and ins.value is not None:
        return [ins.value]
    return []


def defined_var(ins: IRInstr) -> Optional[str]:
    if isinstance(ins, (AssignInstr, BinOp, UnaryOp)):
        return ins.dst
    return None


def has_side_effect(ins: IRInstr) -> bool:
    if isinstance(ins, (PrintInstr, ReturnInstr, IfFalse, Goto, Label)):
        return True
    if isinstance(ins, AssignInstr) and not is_temp(ins.dst):
        return True  # writing to user variable is an effect
    return False


def dce(ir: List[IRInstr]) -> List[IRInstr]:
    live: set[str] = set()
    out_rev: List[IRInstr] = []
    for ins in reversed(ir):
        d = defined_var(ins)
        if has_side_effect(ins) or (d is not None and d in live) or (d is None):
            # keep instruction
            out_rev.append(ins)
            # update liveness with used vars
            for u in used_vars(ins):
                if isinstance(u, str) and not is_const(u):
                    live.add(u)
            if d is not None and d in live:
                live.remove(d)
        else:
            # d is a var defined but never used and no side effects -> drop
            # update liveness with used vars nonetheless (conservative)
            for u in used_vars(ins):
                if isinstance(u, str) and not is_const(u):
                    live.add(u)
            # not appended
    out_rev.reverse()
    return out_rev

# ---------- Driver ----------

def optimize_ir(ir: List[IRInstr]) -> List[IRInstr]:
    ir1 = constant_fold(ir)
    ir2 = dce(ir1)
    return ir2