from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional

from .codegen import BCInstr, BLabel, BJmp, BIfFalse, BMov, BUnary, BBin, BPrint, BRet, BFunc, BEndFunc, BCall

def _parse_num(x: str) -> Optional[float]:
    try: return float(x)
    except Exception: return None

@dataclass
class Frame:
    env: Dict[str, float]
    ret_pc: int
    ret_dst: Optional[str]

class VM:
    def __init__(self, code: List[BCInstr]):
        self.code = code
        self.labels: Dict[str, int] = {}
        self.func_meta: Dict[str, Dict[str, int | List[str]]] = {}
        self._index()
        self.pc = 0
        self.n = len(code)
        self.stack: List[Frame] = []
        self.global_env: Dict[str, float] = {}
        self.env: Dict[str, float] = self.global_env
        self.output: List[str] = []

    def _index(self):
        # Build label map and function start/end ranges
        func_stack: List[str] = []
        for i, ins in enumerate(self.code):
            if isinstance(ins, BLabel):
                self.labels[ins.name] = i
            elif isinstance(ins, BFunc):
                self.func_meta[ins.name] = {'start': i, 'end': i, 'params': ins.params}
                func_stack.append(ins.name)
            elif isinstance(ins, BEndFunc):
                if func_stack:
                    name = func_stack.pop()
                    self.func_meta[name]['end'] = i  # type: ignore

    def _is_true(self, v: float) -> bool: return v != 0.0
    def _fmt(self, v: float) -> str: return str(int(v)) if v.is_integer() else str(v)

    def _get(self, x: str) -> float:
        v = _parse_num(x)
        if v is not None: return v
        if x in self.env: return self.env[x]
        return self.global_env.get(x, 0.0)

    def _set(self, name: str, val: float): self.env[name] = val

    def step(self) -> bool:
        if self.pc >= self.n: return False
        ins = self.code[self.pc]; self.pc += 1

        # Skip function bodies during global execution
        if isinstance(ins, BFunc):
            if not self.stack:
                end = int(self.func_meta.get(ins.name, {}).get('end', self.pc - 1))
                self.pc = end + 1
                return True
            return True  # inside a call we never land on BFunc

        if isinstance(ins, BEndFunc):
            # Implicit return 0 when a function ends without RET
            if self.stack:
                frame = self.stack.pop()
                self.env = frame.env
                if frame.ret_dst is not None:
                    self._set(frame.ret_dst, 0.0)
                self.pc = frame.ret_pc
            return True

        if isinstance(ins, BLabel):
            return True

        if isinstance(ins, BJmp):
            self.pc = self.labels.get(ins.label, self.pc); return True

        if isinstance(ins, BIfFalse):
            if not self._is_true(self._get(ins.cond)):
                self.pc = self.labels.get(ins.label, self.pc)
            return True

        if isinstance(ins, BMov):
            self._set(ins.dst, self._get(ins.src)); return True

        if isinstance(ins, BUnary):
            a = self._get(ins.src)
            if ins.op == '!': v = 0.0 if self._is_true(a) else 1.0
            elif ins.op == '+': v = +a
            elif ins.op == '-': v = -a
            else: raise RuntimeError(f"Unknown unary op {ins.op}")
            self._set(ins.dst, v); return True

        if isinstance(ins, BBin):
            a = self._get(ins.left); b = self._get(ins.right); op = ins.op
            if   op == '+': v = a + b
            elif op == '-': v = a - b
            elif op == '*': v = a * b
            elif op == '/': v = a / b
            elif op == '%': v = float(int(a) % int(b))
            elif op == '<': v = 1.0 if a < b else 0.0
            elif op == '<=': v = 1.0 if a <= b else 0.0
            elif op == '>': v = 1.0 if a > b else 0.0
            elif op == '>=': v = 1.0 if a >= b else 0.0
            elif op == '==': v = 1.0 if a == b else 0.0
            elif op == '!=': v = 1.0 if a != b else 0.0
            elif op == '&&': v = 1.0 if (a != 0 and b != 0) else 0.0
            elif op == '||': v = 1.0 if (a != 0 or b != 0) else 0.0
            else: raise RuntimeError(f"Unknown bin op {op}")
            self._set(ins.dst, v); return True

        if isinstance(ins, BPrint):
            self.output.append(self._fmt(self._get(ins.value))); return True

        if isinstance(ins, BCall):
            meta = self.func_meta.get(ins.name)
            if meta is None:  # unknown func => no-op
                return True
            params = list(meta['params'])  # type: ignore
            arg_vals = [self._get(a) for a in ins.args]
            # push caller frame
            self.stack.append(Frame(env=self.env, ret_pc=self.pc, ret_dst=ins.dst))
            # new local env
            self.env = {}
            for i, p in enumerate(params):
                self.env[p] = arg_vals[i] if i < len(arg_vals) else 0.0
            # jump to first instruction after BFunc
            self.pc = int(meta['start']) + 1  # type: ignore
            return True

        if isinstance(ins, BRet):
            if not self.stack:
                # global RET -> end program (no extra line)
                self.pc = self.n
                return False
            frame = self.stack.pop()
            ret_val = self._get(ins.value) if ins.value is not None else 0.0
            self.env = frame.env
            if frame.ret_dst is not None:
                self._set(frame.ret_dst, ret_val)
            self.pc = frame.ret_pc
            return True

        return True

    def run(self) -> str:
        while self.step():
            pass
        return "\n".join(self.output)

def run(bytecode: List[BCInstr]) -> str:
    return VM(bytecode).run()
