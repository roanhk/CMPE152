# tokens.py

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # Special
    EOF = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()

    # Literals
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()

    # Keywords
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    PRINT = auto()
    TRUE = auto()
    FALSE = auto()
    NONE = auto()

    # Operators
    ASSIGN = auto()          # =
    PLUS = auto()            # +
    MINUS = auto()           # -
    MULTIPLY = auto()        # *
    DIVIDE = auto()          # /
    MODULO = auto()          # %
    POWER = auto()           # **
    FLOOR_DIVIDE = auto()    # //

    # Comparison Operators
    EQ = auto()              # ==
    NE = auto()              # !=
    LT = auto()              # <
    LE = auto()              # <=
    GT = auto()              # >
    GE = auto()              # >=

    # Logical Operators
    AND = auto()
    OR = auto()
    NOT = auto()

    # Delimiters / Symbols
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    LBRACKET = auto()        # [
    RBRACKET = auto()        # ]
    LBRACE = auto()          # {
    RBRACE = auto()          # }
    COLON = auto()           # :
    COMMA = auto()           # ,
    DOT = auto()             # .
    SEMICOLON = auto()       # ;


KEYWORDS = {
    "if": TokenType.IF,
    "elif": TokenType.ELIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
    "True": TokenType.TRUE,
    "False": TokenType.FALSE,
    "None": TokenType.NONE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


OPERATORS = {
    "=": TokenType.ASSIGN,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MULTIPLY,
    "/": TokenType.DIVIDE,
    "%": TokenType.MODULO,
    "**": TokenType.POWER,
    "//": TokenType.FLOOR_DIVIDE,
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<": TokenType.LT,
    "<=": TokenType.LE,
    ">": TokenType.GT,
    ">=": TokenType.GE,
}


DELIMITERS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    ";": TokenType.SEMICOLON,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return (
            f"Token(type={self.type.name}, "
            f"value={self.value!r}, "
            f"line={self.line}, "
            f"column={self.column})"
        )