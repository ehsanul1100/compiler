from . import __init__ # noqa
from typing import List
from compiler_core.domain.tokens import Token, TokenType, KEYWORDS

class Lexer:
        def __init__(self, src: str):
            self.src = src
            self.pos = 0
            self.line = 1
            self.col = 1
            self.n = len(src)

        def _peek(self, k=0):
            i = self.pos + k
            return self.src[i] if i < self.n else '\0'

        def _advance(self):
            ch = self._peek()
            self.pos += 1
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            return ch

        def _add(self, ttype, lexeme, line, col):
            return Token(ttype, lexeme, line, col)

        def _skip_ws_and_comments(self):
            while True:
                ch = self._peek()
                if ch in ' \t\r\n':
                    self._advance()
                    continue
                # // line comment
                if ch == '/' and self._peek(1) == '/':
                    while self._peek() not in ('\n', '\0'):
                        self._advance()
                    continue
                # /* block comment */
                if ch == '/' and self._peek(1) == '*':
                    self._advance()
                    self._advance()
                    while not (self._peek() == '*' and self._peek(1) == '/'):
                        if self._peek() == '\0':
                            return
                        self._advance()
                    self._advance()
                    self._advance()  # consume */
                    continue
                break

        def tokenize(self) -> List[Token]:
            out: List[Token] = []
            while True:
                self._skip_ws_and_comments()
                start_line, start_col = self.line, self.col
                ch = self._peek()
                if ch == '\0':
                    out.append(self._add(TokenType.EOF, '', start_line, start_col))
                    return out

                # identifiers / keywords
                if ch.isalpha() or ch == '_':
                    lex = []
                    while self._peek().isalnum() or self._peek() == '_':
                        lex.append(self._advance())
                    lexeme = ''.join(lex)
                    ttype = KEYWORDS.get(lexeme, TokenType.IDENT)
                    # normalize true/false to BOOL_LIT
                    if ttype == TokenType.BOOL_LIT:
                        return_token = self._add(TokenType.BOOL_LIT, lexeme, start_line, start_col)
                    else:
                        return_token = self._add(ttype, lexeme, start_line, start_col)
                    out.append(return_token)
                    continue

                # numbers (int/float)
                if ch.isdigit():
                    lex = []
                    is_float = False
                    while self._peek().isdigit():
                        lex.append(self._advance())
                    if self._peek() == '.' and self._peek(1).isdigit():
                        is_float = True
                        lex.append(self._advance())
                        while self._peek().isdigit():
                            lex.append(self._advance())
                    lexeme = ''.join(lex)
                    out.append(self._add(TokenType.FLOAT_LIT if is_float else TokenType.INT_LIT, lexeme, start_line, start_col))
                    continue

                # operators & punctuation (two-char)
                two = ch + self._peek(1)
                if two in ('<=', '>=', '==', '!=', '&&', '||'):
                    self._advance()
                    self._advance()
                    mapping = {
                        '<=': TokenType.LE, '>=': TokenType.GE, '==': TokenType.EQ, '!=': TokenType.NE,
                        '&&': TokenType.AND, '||': TokenType.OR,
                    }
                    out.append(self._add(mapping[two], two, start_line, start_col))
                    continue

                # single-char tokens
                single_map = {
                    '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR, '/': TokenType.SLASH, '%': TokenType.PERCENT,
                    '(': TokenType.LPAREN, ')': TokenType.RPAREN, '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                    ',': TokenType.COMMA, ';': TokenType.SEMI, '!': TokenType.BANG, '=': TokenType.ASSIGN,
                    '<': TokenType.LT, '>': TokenType.GT,
                }
                if ch in single_map:
                    out.append(self._add(single_map[self._advance()], ch, start_line, start_col))
                    continue

                # unknown char → consume and continue (error-friendly; later we add Errors)
                self._advance()
            return out

def lex(src: str) -> List[Token]:
        return Lexer(src).tokenize()