# main.py

import os
import sys

from lexer import LexicalAnalyzer

# Use whichever parser filename you settled on.
# If you renamed parser.py to syntax_analyzer.py, this will still work.
try:
    from syntax_analyzer import Parser
except ImportError:
    from ast import Parser

from semantic_analyzer import SemanticAnalyzer
from optimizer import CodeOptimizer
from code_generator import CodeGenerator
from test_cases import TEST_CASES
from errors import format_error


# ============================================================
# Pretty printers
# ============================================================

def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_error_block(title, errors, default_type):
    print_header(title)
    for err in errors:
        if isinstance(err, dict) and "type" not in err:
            err = {**err, "type": default_type}
        print(format_error(err))


def print_source(source_code):
    print_header("1. SOURCE CODE")
    lines = source_code.splitlines()
    for i, line in enumerate(lines, start=1):
        print(f"{i:>3}: {line}")


def print_tokens(tokens):
    print_header("2. LEXING / TOKENIZATION")
    for tok in tokens:
        print(
            f"Line {tok.line:>2}, Col {tok.column:>2} | "
            f"{tok.type.name:<15} | {repr(tok.value)}"
        )


def ast_to_string(node, indent=0):
    space = "  " * indent

    if isinstance(node, dict):
        lines = []
        node_type = node.get("type", "Object")
        lines.append(f"{space}{node_type}")
        for key, value in node.items():
            if key == "type":
                continue
            lines.append(f"{space}  {key}:")
            lines.append(ast_to_string(value, i