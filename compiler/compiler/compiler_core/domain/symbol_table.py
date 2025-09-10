from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class Symbol:
    name: str
    type: str  # 'int' | 'float' | 'bool'

class Scope:
    def __init__(self, parent: Optional['Scope']=None):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, name: str, type_: str) -> bool:
        if name in self.symbols:
            return False
        self.symbols[name] = Symbol(name, type_)
        return True

    def resolve(self, name: str) -> Optional[Symbol]:
        scope: Optional['Scope'] = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None

class SymbolTable:
    def __init__(self):
        self.scopes: List[Scope] = []
        self.push_scope()  # global scope

    def push_scope(self):
        parent = self.scopes[-1] if self.scopes else None
        self.scopes.append(Scope(parent))

    def pop_scope(self):
        if self.scopes:
            self.scopes.pop()

    def current(self) -> Scope:
        return self.scopes[-1]

    def define(self, name: str, type_: str) -> bool:
        return self.current().define(name, type_)

    def resolve(self, name: str) -> Optional[Symbol]:
        return self.current().resolve(name)

    def to_json(self):
        arr = []
        for idx, scope in enumerate(self.scopes):
            arr.append({
                'level': idx,
                'symbols': {k: v.type for k, v in scope.symbols.items()}
            })
        return {'scopes': arr}