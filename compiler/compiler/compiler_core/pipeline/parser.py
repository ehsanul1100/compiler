from __future__ import annotations
from typing import List, Optional, Tuple

from compiler_core.domain.tokens import Token, TokenType
from compiler_core.domain.ast_nodes import (
    Program, Block, VarDecl, If, While, For, Print, Return, ExprStmt,
    Assign, Literal, Var, Unary, Binary, Grouping, Stmt, Expr,
    FunctionDecl, Param, Call
)
from compiler_core.domain.errors import ParseError

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParseError] = []

    # -------------- utilities --------------
    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        if not self._at_end():
            self.current += 1
        return self._previous()

    def _check(self, *types: TokenType) -> bool:
        return (not self._at_end()) and (self._peek().type in types)

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _consume(self, ttype: TokenType, msg: str) -> Token:
        if self._check(ttype):
            return self._advance()
        self._error(self._peek(), msg)
        return self._advance()

    def _error(self, token: Token, message: str):
        self.errors.append(ParseError(message, token.line, token.col))
        self._synchronize()

    def _synchronize(self):
        self._advance()
        while not self._at_end():
            if self._previous().type == TokenType.SEMI:
                return
            if self._peek().type in (
                TokenType.KW_IF, TokenType.KW_WHILE, TokenType.KW_FOR,
                TokenType.KW_RETURN, TokenType.KW_INT, TokenType.KW_FLOAT,
                TokenType.KW_BOOL, TokenType.KW_VOID
            ):
                return
            if self._peek().type == TokenType.RBRACE:
                return
            self._advance()

    # -------------- entrypoint --------------
    def parse(self) -> Tuple[Program, List[ParseError]]:
        body: List[Stmt] = []
        while not self._at_end():
            body.append(self.declaration())
        return Program(body), self.errors

    # -------------- declarations --------------
    def declaration(self) -> Stmt:
        if self._match(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_VOID):
            type_tok = self._previous()
            name_tok = self._consume(TokenType.IDENT, "Expected identifier after type")
            if self._match(TokenType.LPAREN):
                # --- function declaration ---
                params = self.param_list()
                self._consume(TokenType.RPAREN, "Expected ')' after parameters")
                self._consume(TokenType.LBRACE, "Expected '{' before function body")
                body = self.block()  # block() now handles both cases safely
                return FunctionDecl(return_type=type_tok.lexeme, name=name_tok.lexeme, params=params, body=body)
            # --- variable declaration ---
            if type_tok.type == TokenType.KW_VOID:
                self._error(type_tok, "'void' is not allowed for variable declarations")
            init: Optional[Expr] = None
            if self._match(TokenType.ASSIGN):
                init = self.expression()
            self._consume(TokenType.SEMI, "Expected ';' after declaration")
            return VarDecl(var_type=type_tok.lexeme, name=name_tok.lexeme, init=init, line=type_tok.line, col=type_tok.col)
        return self.statement()

    def param_list(self) -> List[Param]:
        params: List[Param] = []
        if self._check(TokenType.RPAREN):
            return params
        while True:
            if not self._match(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL):
                self._error(self._peek(), "Expected parameter type (int|float|bool)")
                break
            ttype_tok = self._previous()
            name_tok = self._consume(TokenType.IDENT, "Expected parameter name")
            params.append(Param(type=ttype_tok.lexeme, name=name_tok.lexeme))
            if not self._match(TokenType.COMMA):
                break
        return params

    # -------------- statements --------------
    def statement(self) -> Stmt:
        if self._match(TokenType.KW_FOR):   return self.for_stmt()
        if self._match(TokenType.KW_WHILE): return self.while_stmt()
        if self._match(TokenType.KW_IF):    return self.if_stmt()
        if self._match(TokenType.KW_PRINT): return self.print_stmt()
        if self._match(TokenType.KW_RETURN):return self.return_stmt()
        if self._check(TokenType.LBRACE):   return self.block()
        return self.expr_stmt()

    def block(self) -> Block:
        # Robust: consume '{' if it's still there (function path),
        # or assume it was consumed by statement() (block statement path).
        if self._check(TokenType.LBRACE):
            self._advance()
        statements: List[Stmt] = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            statements.append(self.declaration())
        self._consume(TokenType.RBRACE, "Expected '}' after block")
        return Block(statements)

    def for_stmt(self) -> For:
        self._consume(TokenType.LPAREN, "Expected '(' after 'for'")
        # init
        if self._match(TokenType.SEMI):
            init = None
        elif self._match(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL):
            init = self.vardecl_after_type(self._previous())
        else:
            init = self.expr_stmt()
        # cond
        cond: Optional[Expr] = None
        if not self._check(TokenType.SEMI):
            cond = self.expression()
        self._consume(TokenType.SEMI, "Expected ';' after loop condition")
        # post
        post: Optional[Stmt] = None
        if not self._check(TokenType.RPAREN):
            post = self.expr_stmt_no_semi()
        self._consume(TokenType.RPAREN, "Expected ')' after for clauses")
        body = self.statement()
        return For(init=init, cond=cond, post=post, body=body)

    def vardecl_after_type(self, type_tok: Token) -> VarDecl:
        name = self._consume(TokenType.IDENT, "Expected variable name")
        init: Optional[Expr] = None
        if self._match(TokenType.ASSIGN):
            init = self.expression()
        self._consume(TokenType.SEMI, "Expected ';' after declaration")
        return VarDecl(var_type=type_tok.lexeme, name=name.lexeme, init=init, line=type_tok.line, col=type_tok.col)

    def while_stmt(self) -> While:
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        cond = self.expression()
        self._consume(TokenType.RPAREN, "Expected ')' after condition")
        body = self.statement()
        return While(cond=cond, body=body)

    def if_stmt(self) -> If:
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        cond = self.expression()
        self._consume(TokenType.RPAREN, "Expected ')' after condition")
        then_branch = self.statement()
        else_branch = None
        if self._match(TokenType.KW_ELSE):
            else_branch = self.statement()
        return If(cond=cond, then_branch=then_branch, else_branch=else_branch)

    def print_stmt(self) -> Print:
        self._consume(TokenType.LPAREN, "Expected '(' after 'print'")
        e = self.expression()
        self._consume(TokenType.RPAREN, "Expected ')' after expression")
        self._consume(TokenType.SEMI, "Expected ';' after print(...) expression")
        return Print(expr=e)

    def return_stmt(self) -> Return:
        e = None if self._check(TokenType.SEMI) else self.expression()
        self._consume(TokenType.SEMI, "Expected ';' after return")
        return Return(expr=e)

    def expr_stmt(self) -> ExprStmt:
        expr = self.expression()
        self._consume(TokenType.SEMI, "Expected ';' after expression")
        return ExprStmt(expr)

    def expr_stmt_no_semi(self) -> ExprStmt:
        expr = self.expression()
        return ExprStmt(expr)

    # -------------- expressions --------------
    def expression(self) -> Expr:
        return self.assignment()

    def assignment(self) -> Expr:
        expr = self.logic_or()
        if self._match(TokenType.ASSIGN):
            equals = self._previous()
            value = self.assignment()
            if isinstance(expr, Var):
                return Assign(expr.name, value, equals.line, equals.col)
            self._error(equals, "Invalid assignment target")
        return expr

    def logic_or(self) -> Expr:
        expr = self.logic_and()
        while self._match(TokenType.OR):
            expr = Binary(expr, '||', self.logic_and())
        return expr

    def logic_and(self) -> Expr:
        expr = self.equality()
        while self._match(TokenType.AND):
            expr = Binary(expr, '&&', self.equality())
        return expr

    def equality(self) -> Expr:
        expr = self.comparison()
        while self._match(TokenType.EQ, TokenType.NE):
            op = self._previous().lexeme
            expr = Binary(expr, op, self.comparison())
        return expr

    def comparison(self) -> Expr:
        expr = self.term()
        while self._match(TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            op = self._previous().lexeme
            expr = Binary(expr, op, self.term())
        return expr

    def term(self) -> Expr:
        expr = self.factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous().lexeme
            expr = Binary(expr, op, self.factor())
        return expr

    def factor(self) -> Expr:
        expr = self.unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._previous().lexeme
            expr = Binary(expr, op, self.unary())
        return expr

    def unary(self) -> Expr:
        if self._match(TokenType.BANG, TokenType.MINUS, TokenType.PLUS):
            op = self._previous().lexeme
            return Unary(op, self.unary())
        return self.primary()

    def primary(self) -> Expr:
        if self._match(TokenType.INT_LIT):
            return Literal(int(self._previous().lexeme), 'int')
        if self._match(TokenType.FLOAT_LIT):
            return Literal(float(self._previous().lexeme), 'float')
        if self._match(TokenType.BOOL_LIT):
            lex = self._previous().lexeme
            return Literal(True if lex == 'true' else False, 'bool')
        if self._match(TokenType.IDENT):
            t = self._previous()
            if self._match(TokenType.LPAREN):
                args: List[Expr] = []
                if not self._check(TokenType.RPAREN):
                    while True:
                        args.append(self.expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RPAREN, "Expected ')' after arguments")
                return Call(t.lexeme, args, t.line, t.col)
            return Var(t.lexeme, t.line, t.col)
        if self._match(TokenType.LPAREN):
            e = self.expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return Grouping(e)
        tok = self._peek()
        self._error(tok, f"Unexpected token: {tok.type.name}")
        return Literal(0, 'int')

# Public API
def parse(tokens: List[Token]):
    if tokens and isinstance(tokens[0], dict):
        from compiler_core.domain.tokens import Token as T, TokenType as TT
        converted: List[T] = []
        for d in tokens:
            ttype = d.get('type')
            if isinstance(ttype, str):
                ttype = getattr(TT, ttype)
            converted.append(T(ttype, d.get('lexeme',''), d.get('line',0), d.get('col',0)))
        tokens = converted
    parser = Parser(tokens)  # type: ignore
    ast_root, errors = parser.parse()
    return ast_root, [e.to_dict() for e in errors]
