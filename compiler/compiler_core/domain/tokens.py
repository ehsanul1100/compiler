from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    # Single-char
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); PERCENT = auto()
    LPAREN = auto(); RPAREN = auto(); LBRACE = auto(); RBRACE = auto()
    COMMA = auto(); SEMI = auto(); BANG = auto(); ASSIGN = auto()

    # One-or-two-char
    LT = auto(); LE = auto(); GT = auto(); GE = auto()
    EQ = auto(); NE = auto()
    AND = auto(); OR = auto()

    # Literals & identifiers
    IDENT = auto(); INT_LIT = auto(); FLOAT_LIT = auto(); BOOL_LIT = auto()

    # Keywords
    KW_INT = auto(); KW_FLOAT = auto(); KW_BOOL = auto(); KW_VOID = auto()
    KW_IF = auto(); KW_ELSE = auto(); KW_WHILE = auto(); KW_FOR = auto()
    KW_RETURN = auto(); KW_PRINT = auto()

    EOF = auto()

KEYWORDS = {
    'int': TokenType.KW_INT,
    'float': TokenType.KW_FLOAT,
    'bool': TokenType.KW_BOOL,
    'void': TokenType.KW_VOID,
    'if': TokenType.KW_IF,
    'else': TokenType.KW_ELSE,
    'while': TokenType.KW_WHILE,
    'for': TokenType.KW_FOR,
    'return': TokenType.KW_RETURN,
    'print': TokenType.KW_PRINT,
    'true': TokenType.BOOL_LIT,
    'false': TokenType.BOOL_LIT,
}

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int