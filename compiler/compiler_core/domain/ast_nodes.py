from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

# === AST NODES ===

class Node: ...
class Stmt(Node): ...
class Expr(Node):
    inferred_type: str | None = None  # set by semantics

# Program
@dataclass
class Program(Node):
    body: List[Stmt]

# Functions
@dataclass
class Param(Node):
    type: str
    name: str

@dataclass
class FunctionDecl(Stmt):
    return_type: str
    name: str
    params: List[Param]
    body: 'Block'

# Statements
@dataclass
class Block(Stmt):
    statements: List[Stmt]

@dataclass
class VarDecl(Stmt):
    var_type: str
    name: str
    init: Optional[Expr]
    line: int
    col: int

@dataclass
class If(Stmt):
    cond: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]

@dataclass
class While(Stmt):
    cond: Expr
    body: Stmt

@dataclass
class For(Stmt):
    init: Optional[Stmt]
    cond: Optional[Expr]
    post: Optional[Stmt]
    body: Stmt

@dataclass
class Print(Stmt):
    expr: Expr

@dataclass
class Return(Stmt):
    expr: Optional[Expr]

@dataclass
class ExprStmt(Stmt):
    expr: Expr

# Expressions
@dataclass
class Assign(Expr):
    name: str
    value: Expr
    line: int
    col: int

@dataclass
class Call(Expr):
    name: str
    args: List[Expr]
    line: int
    col: int

@dataclass
class Literal(Expr):
    value: Any
    kind: str  # 'int' | 'float' | 'bool'

@dataclass
class Var(Expr):
    name: str
    line: int
    col: int

@dataclass
class Unary(Expr):
    op: str
    right: Expr

@dataclass
class Binary(Expr):
    left: Expr
    op: str
    right: Expr

@dataclass
class Grouping(Expr):
    expr: Expr

# === JSON helpers ===

def ast_to_dict(node: Node) -> Dict[str, Any]:
    if isinstance(node, Program):
        return {"type": "Program", "body": [ast_to_dict(s) for s in node.body]}
    if isinstance(node, FunctionDecl):
        return {
            "type": "FunctionDecl",
            "return_type": node.return_type,
            "name": node.name,
            "params": [{"type": p.type, "name": p.name} for p in node.params],
            "body": ast_to_dict(node.body),
        }
    if isinstance(node, Block):
        return {"type": "Block", "statements": [ast_to_dict(s) for s in node.statements]}
    if isinstance(node, VarDecl):
        return {"type": "VarDecl", "var_type": node.var_type, "name": node.name, "init": ast_to_dict(node.init) if node.init else None, "line": node.line, "col": node.col}
    if isinstance(node, If):
        return {"type": "If", "cond": ast_to_dict(node.cond), "then": ast_to_dict(node.then_branch), "else": ast_to_dict(node.else_branch) if node.else_branch else None}
    if isinstance(node, While):
        return {"type": "While", "cond": ast_to_dict(node.cond), "body": ast_to_dict(node.body)}
    if isinstance(node, For):
        return {"type": "For", "init": ast_to_dict(node.init) if node.init else None, "cond": ast_to_dict(node.cond) if node.cond else None, "post": ast_to_dict(node.post) if node.post else None, "body": ast_to_dict(node.body)}
    if isinstance(node, Print):
        return {"type": "Print", "expr": ast_to_dict(node.expr)}
    if isinstance(node, Return):
        return {"type": "Return", "expr": ast_to_dict(node.expr) if node.expr else None}
    if isinstance(node, ExprStmt):
        return {"type": "ExprStmt", "expr": ast_to_dict(node.expr)}
    if isinstance(node, Assign):
        return {"type": "Assign", "name": node.name, "value": ast_to_dict(node.value), "line": node.line, "col": node.col}
    if isinstance(node, Call):
        return {"type": "Call", "name": node.name, "args": [ast_to_dict(a) for a in node.args], "line": node.line, "col": node.col}
    if isinstance(node, Literal):
        return {"type": "Literal", "value": node.value, "kind": node.kind}
    if isinstance(node, Var):
        return {"type": "Var", "name": node.name, "line": node.line, "col": node.col}
    if isinstance(node, Unary):
        return {"type": "Unary", "op": node.op, "right": ast_to_dict(node.right)}
    if isinstance(node, Binary):
        return {"type": "Binary", "op": node.op, "left": ast_to_dict(node.left), "right": ast_to_dict(node.right)}
    if isinstance(node, Grouping):
        return {"type": "Grouping", "expr": ast_to_dict(node.expr)}
    raise TypeError(f"Unknown node type: {type(node)}")


def typed_ast_to_dict(node: Node) -> Dict[str, Any]:
    base = ast_to_dict(node)
    if isinstance(node, Expr):
        base["inferred"] = getattr(node, "inferred_type", None)
    if isinstance(node, Program):
        base["body"] = [typed_ast_to_dict(s) for s in node.body]
    elif isinstance(node, FunctionDecl):
        base["body"] = typed_ast_to_dict(node.body)
    elif isinstance(node, Block):
        base["statements"] = [typed_ast_to_dict(s) for s in node.statements]
    elif isinstance(node, If):
        base["cond"] = typed_ast_to_dict(node.cond)
        base["then"] = typed_ast_to_dict(node.then_branch)
        if node.else_branch: base["else"] = typed_ast_to_dict(node.else_branch)
    elif isinstance(node, While):
        base["cond"] = typed_ast_to_dict(node.cond)
        base["body"] = typed_ast_to_dict(node.body)
    elif isinstance(node, For):
        if node.init: base["init"] = typed_ast_to_dict(node.init)
        if node.cond: base["cond"] = typed_ast_to_dict(node.cond)
        if node.post: base["post"] = typed_ast_to_dict(node.post)
        base["body"] = typed_ast_to_dict(node.body)
    elif isinstance(node, Print):
        base["expr"] = typed_ast_to_dict(node.expr)
    elif isinstance(node, Return) and node.expr is not None:
        base["expr"] = typed_ast_to_dict(node.expr)
    elif isinstance(node, ExprStmt):
        base["expr"] = typed_ast_to_dict(node.expr)
    elif isinstance(node, Assign):
        base["value"] = typed_ast_to_dict(node.value)
    elif isinstance(node, Call):
        base["args"] = [typed_ast_to_dict(a) for a in node.args]
    elif isinstance(node, Unary):
        base["right"] = typed_ast_to_dict(node.right)
    elif isinstance(node, Binary):
        base["left"] = typed_ast_to_dict(node.left)
        base["right"] = typed_ast_to_dict(node.right)
    elif isinstance(node, Grouping):
        base["expr"] = typed_ast_to_dict(node.expr)
    return base