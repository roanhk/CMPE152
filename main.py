# main.py

import os
import sys

from lexer import LexicalAnalyzer

# Use whichever parser filename you settled on.
# If you renamed parser.py to syntax_analyzer.py, this will still work.
try:
    from syntax_analyzer import Parser
except ImportError:
    from parser import Parser

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
            lines.append(ast_to_string(value, indent + 2))
        return "\n".join(lines)

    if isinstance(node, list):
        if not node:
            return f"{space}[]"
        lines = []
        for item in node:
            lines.append(ast_to_string(item, indent))
        return "\n".join(lines)

    return f"{space}{repr(node)}"


def print_ast(ast):
    print_header("3. PARSING / AST")
    print(ast_to_string(ast))


# ============================================================
# Intermediate Code Generator
# ============================================================

class IntermediateCodeGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def generate(self, ast):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0
        self._gen_statements(ast.get("body", []))
        return self.instructions

    def _new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def _new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def _emit(self, text):
        self.instructions.append(text)

    def _gen_statements(self, statements):
        for stmt in statements:
            self._gen_statement(stmt)

    def _gen_statement(self, stmt):
        stmt_type = stmt.get("type")

        if stmt_type == "Assignment":
            value_place = self._gen_expr(stmt["value"])
            self._emit(f"{stmt['target']} = {value_place}")
            return

        if stmt_type == "Print":
            value_place = self._gen_expr(stmt["value"])
            self._emit(f"PRINT {value_place}")
            return

        if stmt_type == "If":
            end_label = self._new_label()
            branch_labels = []

            for _ in stmt.get("branches", []):
                branch_labels.append(self._new_label())

            else_label = self._new_label() if stmt.get("else_body") is not None else end_label

            for i, branch in enumerate(stmt.get("branches", [])):
                cond_place = self._gen_expr(branch["condition"])
                self._emit(f"IF {cond_place} GOTO {branch_labels[i]}")

            self._emit(f"GOTO {else_label}")

            for i, branch in enumerate(stmt.get("branches", [])):
                self._emit(f"{branch_labels[i]}:")
                self._gen_statements(branch["body"])
                self._emit(f"GOTO {end_label}")

            if stmt.get("else_body") is not None:
                self._emit(f"{else_label}:")
                self._gen_statements(stmt["else_body"])

            self._emit(f"{end_label}:")
            return

        if stmt_type == "While":
            start_label = self._new_label()
            body_label = self._new_label()
            end_label = self._new_label()

            self._emit(f"{start_label}:")
            cond_place = self._gen_expr(stmt["condition"])
            self._emit(f"IF {cond_place} GOTO {body_label}")
            self._emit(f"GOTO {end_label}")
            self._emit(f"{body_label}:")
            self._gen_statements(stmt["body"])
            self._emit(f"GOTO {start_label}")
            self._emit(f"{end_label}:")
            return

    def _gen_expr(self, expr):
        expr_type = expr.get("type")

        if expr_type == "Literal":
            value = expr["value"]
            if isinstance(value, str):
                return value
            return str(value)

        if expr_type == "Identifier":
            return expr["name"]

        if expr_type == "UnaryOp":
            operand = self._gen_expr(expr["operand"])
            temp = self._new_temp()
            self._emit(f"{temp} = {expr['operator']} {operand}")
            return temp

        if expr_type == "BinaryOp":
            left = self._gen_expr(expr["left"])
            right = self._gen_expr(expr["right"])
            temp = self._new_temp()
            self._emit(f"{temp} = {left} {expr['operator']} {right}")
            return temp

        if expr_type == "LogicalOp":
            left = self._gen_expr(expr["left"])
            right = self._gen_expr(expr["right"])
            temp = self._new_temp()
            self._emit(f"{temp} = {left} {expr['operator']} {right}")
            return temp

        if expr_type == "Compare":
            current_left = self._gen_expr(expr["left"])
            result_temp = self._new_temp()

            if len(expr["comparisons"]) == 1:
                comp = expr["comparisons"][0]
                right = self._gen_expr(comp["right"])
                self._emit(f"{result_temp} = {current_left} {comp['operator']} {right}")
                return result_temp

            chain_temp = None
            for comp in expr["comparisons"]:
                right = self._gen_expr(comp["right"])
                temp = self._new_temp()
                self._emit(f"{temp} = {current_left} {comp['operator']} {right}")
                if chain_temp is None:
                    chain_temp = temp
                else:
                    merged = self._new_temp()
                    self._emit(f"{merged} = {chain_temp} and {temp}")
                    chain_temp = merged
                current_left = right
            return chain_temp

        return "UNKNOWN"


def print_intermediate_code(ast):
    print_header("4. IMMEDIATE / INTERMEDIATE CODE")
    icg = IntermediateCodeGenerator()
    code = icg.generate(ast)
    if not code:
        print("(No intermediate code)")
        return
    for line in code:
        print(line)


# ============================================================
# Pseudo Assembly Generator
# ============================================================

class AssemblyCodeGenerator:
    def __init__(self):
        self.instructions = []
        self.label_count = 0

    def generate(self, ast):
        self.instructions = []
        self.label_count = 0
        self._gen_statements(ast.get("body", []))
        return self.instructions

    def _new_label(self):
        self.label_count += 1
        return f"LBL{self.label_count}"

    def _emit(self, text):
        self.instructions.append(text)

    def _gen_statements(self, statements):
        for stmt in statements:
            self._gen_statement(stmt)

    def _expr_to_text(self, expr):
        expr_type = expr.get("type")

        if expr_type == "Literal":
            value = expr["value"]
            if isinstance(value, str):
                return repr(value)
            return str(value)

        if expr_type == "Identifier":
            return expr["name"]

        if expr_type == "UnaryOp":
            operand = self._expr_to_text(expr["operand"])
            return f"({expr['operator']} {operand})"

        if expr_type == "BinaryOp":
            left = self._expr_to_text(expr["left"])
            right = self._expr_to_text(expr["right"])
            return f"({left} {expr['operator']} {right})"

        if expr_type == "LogicalOp":
            left = self._expr_to_text(expr["left"])
            right = self._expr_to_text(expr["right"])
            return f"({left} {expr['operator']} {right})"

        if expr_type == "Compare":
            left = self._expr_to_text(expr["left"])
            parts = []
            current = left
            for comp in expr["comparisons"]:
                right = self._expr_to_text(comp["right"])
                parts.append(f"{current} {comp['operator']} {right}")
                current = right
            return " and ".join(parts)

        return "UNKNOWN"

    def _gen_statement(self, stmt):
        stmt_type = stmt.get("type")

        if stmt_type == "Assignment":
            expr_text = self._expr_to_text(stmt["value"])
            self._emit(f"MOV {stmt['target']}, {expr_text}")
            return

        if stmt_type == "Print":
            expr_text = self._expr_to_text(stmt["value"])
            self._emit(f"PRINT {expr_text}")
            return

        if stmt_type == "If":
            end_label = self._new_label()
            next_labels = [self._new_label() for _ in stmt.get("branches", [])]
            else_label = self._new_label() if stmt.get("else_body") is not None else end_label

            for i, branch in enumerate(stmt.get("branches", [])):
                cond_text = self._expr_to_text(branch["condition"])
                self._emit(f"CMP {cond_text}, TRUE")
                self._emit(f"JE {next_labels[i]}")

            self._emit(f"JMP {else_label}")

            for i, branch in enumerate(stmt.get("branches", [])):
                self._emit(f"{next_labels[i]}:")
                self._gen_statements(branch["body"])
                self._emit(f"JMP {end_label}")

            if stmt.get("else_body") is not None:
                self._emit(f"{else_label}:")
                self._gen_statements(stmt["else_body"])

            self._emit(f"{end_label}:")
            return

        if stmt_type == "While":
            start_label = self._new_label()
            body_label = self._new_label()
            end_label = self._new_label()

            self._emit(f"{start_label}:")
            cond_text = self._expr_to_text(stmt["condition"])
            self._emit(f"CMP {cond_text}, TRUE")
            self._emit(f"JE {body_label}")
            self._emit(f"JMP {end_label}")
            self._emit(f"{body_label}:")
            self._gen_statements(stmt["body"])
            self._emit(f"JMP {start_label}")
            self._emit(f"{end_label}:")
            return


def print_assembly_code(ast):
    print_header("5. ASSEMBLY CODE (PSEUDO)")
    acg = AssemblyCodeGenerator()
    code = acg.generate(ast)
    if not code:
        print("(No assembly code)")
        return
    for line in code:
        print(line)


# ============================================================
# Compilation pipeline
# ============================================================

def compile_source(source_code: str, source_name: str = "Input Program", show_steps: bool = True):
    print("\n" + "#" * 60)
    print(f"COMPILING: {source_name}")
    print("#" * 60)

    if show_steps:
        print_source(source_code)

    # 1. Lexing / Tokenization
    lexer = LexicalAnalyzer(source_code)
    tokens, lexical_errors = lexer.tokenize()

    if show_steps:
        print_tokens(tokens)

    if lexical_errors:
        print_error_block("LEXICAL ERRORS", lexical_errors, "Lexical Error")
        return

    # 2. Parsing
    parser = Parser(tokens)
    ast, syntax_errors = parser.parse()

    if show_steps:
        print_ast(ast)

    if syntax_errors:
        print_error_block("SYNTAX ERRORS", syntax_errors, "Syntax Error")
        return

    # 3. Semantic Analysis
    semantic_analyzer = SemanticAnalyzer()
    semantic_errors = semantic_analyzer.analyze(ast)

    if semantic_errors:
        print_error_block("SEMANTIC ERRORS", semantic_errors, "Semantic Error")
        return

    # 4. Optimization
    optimizer = CodeOptimizer()
    optimized_ast = optimizer.optimize(ast)

    if show_steps:
        print_header("OPTIMIZED AST")
        print(ast_to_string(optimized_ast))
        print_intermediate_code(optimized_ast)
        print_assembly_code(optimized_ast)

    # 5. Execution
    code_generator = CodeGenerator()

    try:
        result = code_generator.generate(optimized_ast)
        print_header("6. FINAL EXECUTION OUTPUT")
        if result.strip():
            print(result)
        else:
            print("(No output)")
    except Exception as e:
        runtime_error = {
            "line": None,
            "column": None,
            "type": "Runtime Error",
            "message": str(e)
        }
        print_error_block("RUNTIME ERROR", [runtime_error], "Runtime Error")


def compile_file(file_path: str, show_steps: bool = True):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    if not file_path.endswith(".txt"):
        print("Error: Only .txt files are supported.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            source_code = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    compile_source(source_code, f"File: {file_path}", show_steps=show_steps)


def run_test_cases(show_steps: bool = True):
    if len(TEST_CASES) < 3:
        print("Error: At least THREE test cases are required.")
        return

    for i, test in enumerate(TEST_CASES[:3], start=1):
        compile_source(test["source"], f"Test Case {i}: {test['name']}", show_steps=show_steps)


def main():
    # Usage:
    # python3 main.py
    # python3 main.py program.txt
    # python3 main.py program.txt --no-steps

    show_steps = True

    if "--no-steps" in sys.argv:
        show_steps = False

    args = [arg for arg in sys.argv[1:] if arg != "--no-steps"]

    if len(args) >= 1:
        compile_file(args[0], show_steps=show_steps)
    else:
        run_test_cases(show_steps=show_steps)


if __name__ == "__main__":
    main()