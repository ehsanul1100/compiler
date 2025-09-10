from __future__ import annotations
from typing import List, Dict

from .codegen import BCInstr, BLabel, BJmp, BIfFalse, BMov, BUnary, BBin, BPrint, BRet, BFunc, BEndFunc, BCall

def remove_mov_self(code: List[BCInstr]) -> List[BCInstr]:
    return [ins for ins in code if not (isinstance(ins, BMov) and ins.dst == ins.src)]

def remove_jmp_to_next_label(code: List[BCInstr]) -> List[BCInstr]:
    out: List[BCInstr] = []; n = len(code); i = 0
    while i < n:
        ins = code[i]
        if isinstance(ins, BJmp) and i + 1 < n and isinstance(code[i+1], BLabel) and code[i+1].name == ins.label:
            i += 1; continue
        out.append(ins); i += 1
    return out

def collapse_consecutive_labels(code: List[BCInstr]) -> List[BCInstr]:
    out: List[BCInstr] = []; label_map: Dict[str,str] = {}; prev_label = None
    for ins in code:
        if isinstance(ins, BLabel):
            if prev_label is None: out.append(ins); prev_label = ins.name
            else: label_map[ins.name] = prev_label
        else:
            prev_label = None; out.append(ins)
    def remap(name: str) -> str:
        while name in label_map: name = label_map[name]
        return name
    remapped: List[BCInstr] = []
    for ins in out:
        if isinstance(ins, BJmp): remapped.append(BJmp(remap(ins.label)))
        elif isinstance(ins, BIfFalse): remapped.append(BIfFalse(ins.cond, remap(ins.label)))
        else: remapped.append(ins)
    return remapped

def peephole(code: List[BCInstr]) -> List[BCInstr]:
    code = remove_mov_self(code)
    code = remove_jmp_to_next_label(code)
    code = collapse_consecutive_labels(code)
    return code