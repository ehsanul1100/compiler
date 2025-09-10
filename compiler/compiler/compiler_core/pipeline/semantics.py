from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

from compiler_core.domain.ast_nodes import (
    Program, Block, VarDecl, If, While, For, Print, Return, ExprStmt,
    Assign, Literal, Var, Unary, Binary, Grouping, Stmt, Expr,
    FunctionDecl, Param, Call, typed_ast_to_dict
)
from compiler_core.domain.symbol_table import SymbolTable, Symbol
from compiler_core.domain.errors import ParseError

NUMERIC = {'int', 'float'}
BOOL = 'bool'
INT = 'int'
FLOAT = 'float'
VOID = 'void'
ERROR = 'error'

@dataclass
class FuncSig:
    ret: str
    params: List[Tuple[str, str]]  # (type, name)

class SemanticAnalyzer:
    def __init__(self):
        self.symtab = SymbolTable()
        self.errors: List[ParseError] = []
        self.funcs: Dict[str, FuncSig] = {}
        self.current_ret: Optional[str] = None

    def err(self, line: int, col: int, msg: str):
        self.errors.append(ParseError(msg, line, col))

    # entry
    def visit_program(self, node: Program):
        # collect function signatures
        for s in node.body:
            if isinstance(s, FunctionDecl):
                if s.name in self.funcs:
                    self.err(0, 0, f"Redeclaration of function '{s.name}'")
                else:
                    self.funcs[s.name] = FuncSig(s.return_type, [(p.type, p.name) for p in s.params])
        # analyze
        for s in node.body:
            if isinstance(s, FunctionDecl):
                self.visit_function(s)
            else:
                self.visit_stmt(s)
        return node

    # statements
    def visit_block(self, node: Block):
        self.symtab.push_scope()
        for s in node.statements:
            if isinstance(s, FunctionDecl):
                self.err(0, 0, "Nested function declarations not allowed")
            else:
                self.visit_stmt(s)
        self.symtab.pop_scope()
        return node

    def visit_function(self, node: FunctionDecl):
        saved_ret = self.current_ret
        self.current_ret = node.return_type
        self.symtab.push_scope()
        for p in node.params:
            if not self.symtab.define(p.name, p.type):
                self.err(0, 0, f"Parameter redeclared: {p.name}")
        self.visit_block(node.body)
        self.symtab.pop_scope()
        self.current_ret = saved_ret
        return node

    def visit_vardecl(self, node: VarDecl):
        if not self.symtab.define(node.name, node.var_type):
            self.err(node.line, node.col, f"Redeclaration of '{node.name}'")
        if node.init is not None:
            t = self.visit_expr(node.init)
            if not self.assignable(node.var_type, t):
                self.err(node.line, node.col, f"Cannot assign {t} to {node.var_type} in declaration '{node.name}'")
        return node

    def visit_if(self, node: If):
        t = self.visit_expr(node.cond)
        if t != BOOL:
            self.err(0, 0, "if condition must be bool")
        self.visit_stmt(node.then_branch)
        if node.else_branch:
            self.visit_stmt(node.else_branch)
        return node

    def visit_while(self, node: While):
        t = self.visit_expr(node.cond)
        if t != BOOL:
            self.err(0, 0, "while condition must be bool")
        self.visit_stmt(node.body)
        return node

    def visit_for(self, node: For):
        self.symtab.push_scope()
        if node.init:
            self.visit_stmt(node.init)
        if node.cond:
            t = self.visit_expr(node.cond)
            if t != BOOL:
                self.err(0, 0, "for condition must be bool")
        if node.post:
            self.visit_stmt(node.post)
        self.visit_stmt(node.body)
        self.symtab.pop_scope()
        return node

    def visit_print(self, node: Print):
        self.visit_expr(node.expr)
        return node

    def visit_return(self, node: Return):
        # Allow top-level return to end the program (no error).
        if self.current_ret is None:
            if node.expr is not None:
                self.visit_expr(node.expr)  # just type-check expression
            return node
        # In-function checks
        if node.expr is None:
            if self.current_ret != VOID:
                self.err(0, 0, f"Return value required for function returning {self.current_ret}")
        else:
            t = self.visit_expr(node.expr)
            if not self.assignable(self.current_ret, t):
                self.err(0, 0, f"Cannot return {t} from function returning {self.current_ret}")
        return node

    def visit_exprstmt(self, node: ExprStmt):
        self.visit_expr(node.expr)
        return node

    def visit_stmt(self, node: Stmt):
        if isinstance(node, Block):      return self.visit_block(node)
        if isinstance(node, VarDecl):    return self.visit_vardecl(node)
        if isinstance(node, If):         return self.visit_if(node)
        if isinstance(node, While):      return self.visit_while(node)
        if isinstance(node, For):        return self.visit_for(node)
        if isinstance(node, Print):      return self.visit_print(node)
        if isinstance(node, Return):     return self.visit_return(node)
        if isinstance(node, ExprStmt):   return self.visit_exprstmt(node)
        return node

    # expressions
    def visit_assign(self, node: Assign) -> str:
        sym = self.symtab.resolve(node.name)
        if sym is None:
            self.err(node.line, node.col, f"Undeclared variable '{node.name}'")
            node.inferred_type = ERROR
            self.visit_expr(node.value)
            return ERROR
        val_t = self.visit_expr(node.value)
        if not self.assignable(sym.type, val_t):
            self.err(node.line, node.col, f"Cannot assign {val_t} to {sym.type} variable '{node.name}'")
            node.inferred_type = ERROR
            return ERROR
        node.inferred_type = sym.type
        return sym.type

    def visit_call(self, node: Call) -> str:
        sig = self.funcs.get(node.name)
        if sig is None:
            self.err(node.line, node.col, f"Call to undefined function '{node.name}'")
            node.inferred_type = ERROR
            for a in node.args:
                self.visit_expr(a)
            return ERROR
        if len(node.args) != len(sig.params):
            self.err(node.line, node.col, f"Function '{node.name}' expects {len(sig.params)} arg(s), got {len(node.args)}")
        for (pt, _), arg in zip(sig.params, node.args):
            at = self.visit_expr(arg)
            if not self.assignable(pt, at):
                self.err(node.line, node.col, f"Argument type {at} incompatible with parameter {pt} in call to '{node.name}'")
        node.inferred_type = sig.ret
        return sig.ret

    def visit_literal(self, node: Literal) -> str:
        node.inferred_type = node.kind
        return node.kind

    def visit_var(self, node: Var) -> str:
        sym = self.symtab.resolve(node.name)
        if sym is None:
            self.err(node.line, node.col, f"Undeclared variable '{node.name}'")
            node.inferred_type = ERROR
            return ERROR
        node.inferred_type = sym.type
        return sym.type

    def visit_unary(self, node: Unary) -> str:
        t = self.visit_expr(node.right)
        if node.op == '!':
            if t != BOOL:
                self.err(0, 0, "'!' requires bool")
                node.inferred_type = ERROR
                return ERROR
            node.inferred_type = BOOL
            return BOOL
        if node.op in ('+', '-'):
            if t not in NUMERIC:
                self.err(0, 0, f"Unary '{node.op}' requires numeric operand")
                node.inferred_type = ERROR
                return ERROR
            node.inferred_type = t
            return t
        node.inferred_type = ERROR
        return ERROR

    def visit_binary(self, node: Binary) -> str:
        lt = self.visit_expr(node.left)
        rt = self.visit_expr(node.right)
        op = node.op
        if op in ('+','-','*','/'):
            if lt in NUMERIC and rt in NUMERIC:
                node.inferred_type = FLOAT if FLOAT in (lt, rt) else INT
                return node.inferred_type
            self.err(0,0, f"Operator '{op}' requires numeric operands")
            node.inferred_type = ERROR
            return ERROR
        if op == '%':
            if lt == INT and rt == INT:
                node.inferred_type = INT
                return INT
            self.err(0,0, "'%' requires int operands")
            node.inferred_type = ERROR
            return ERROR
        if op in ('<','<=','>','>='):
            if lt in NUMERIC and rt in NUMERIC:
                node.inferred_type = BOOL
                return BOOL
            self.err(0,0, f"Operator '{op}' requires numeric operands")
            node.inferred_type = ERROR
            return ERROR
        if op in ('==','!='):
            if lt == rt and lt != ERROR:
                node.inferred_type = BOOL
                return BOOL
            self.err(0,0, "'=='/'!=' require operands of the same type")
            node.inferred_type = ERROR
            return ERROR
        if op in ('&&','||'):
            if lt == BOOL and rt == BOOL:
                node.inferred_type = BOOL
                return BOOL
            self.err(0,0, "'&&'/'||' require bool operands")
            node.inferred_type = ERROR
            return ERROR
        self.err(0,0, f"Unknown operator '{op}'")
        node.inferred_type = ERROR
        return ERROR

    def visit_grouping(self, node: Grouping) -> str:
        t = self.visit_expr(node.expr)
        node.inferred_type = t
        return t

    def visit_expr(self, node: Expr) -> str:
        if isinstance(node, Assign):   return self.visit_assign(node)
        if isinstance(node, Call):     return self.visit_call(node)
        if isinstance(node, Literal):  return self.visit_literal(node)
        if isinstance(node, Var):      return self.visit_var(node)
        if isinstance(node, Unary):    return self.visit_unary(node)
        if isinstance(node, Binary):   return self.visit_binary(node)
        if isinstance(node, Grouping): return self.visit_grouping(node)
        node.inferred_type = ERROR
        return ERROR

    # helpers
    def assignable(self, to_type: str, from_type: str) -> bool:
        if to_type == from_type:
            return True
        if to_type == FLOAT and from_type == INT:
            return True
        if to_type == VOID:
            return from_type == VOID
        return False

def analyze(ast_root: Program):
    analyzer = SemanticAnalyzer()
    typed_root = analyzer.visit_program(ast_root)
    typed_json = typed_ast_to_dict(typed_root)
    sym_json = analyzer.symtab.to_json()
    errors = [e.__dict__ for e in analyzer.errors]
    return {
        'typed_root': typed_root,
        'typed_json': typed_json,
        'symbol_table': sym_json,
        'errors': errors,
        'func_table': {name: {'ret': sig.ret, 'params': sig.params} for name, sig in analyzer.funcs.items()},
    }
