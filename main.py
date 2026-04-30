# main.py

from lexer import LexicalAnalyzer
from syntax_analyzer import Parser
from semantic_analyzer import SemanticAnalyzer
from optimizer import CodeOptimizer
from code_generator import CodeGenerator
from test_cases import TEST_CASES
from errors import format_error


def print_error_block(title, errors, default_type):
    print(title)
    for err in errors:
        if isinstance(err, dict) and "type" not in err:
            err = {**err, "type": default_type}
        print(format_error(err))


def compile_source(source_code: str, test_case_name: str = "Input Program"):
    print("=" * 60)
    print(f"Compiling: {test_case_name}")
    print("=" * 60)

    # 1. Lexical Analysis
    lexer = LexicalAnalyzer(source_code)
    tokens, lexical_errors = lexer.tokenize()

    if lexical_errors:
        print_error_block("Lexical Errors:", lexical_errors, "Lexical Error")
        return

    # 2. Syntax Analysis / Parsing
    parser = Parser(tokens)
    ast, syntax_errors = parser.parse()

    if syntax_errors:
        print_error_block("Syntax Errors:", syntax_errors, "Syntax Error")
        return

    # 3. Semantic Analysis
    semantic_analyzer = SemanticAnalyzer()
    semantic_errors = semantic_analyzer.analyze(ast)

    if semantic_errors:
        print_error_block("Semantic Errors:", semantic_errors, "Semantic Error")
        return

    # 4. Optimization
    optimizer = CodeOptimizer()
    optimized_ast = optimizer.optimize(ast)

    # 5. Code Generation / Interpretation
    code_generator = CodeGenerator()

    try:
        result = code_generator.generate(optimized_ast)
        print("Compilation Successful.")
        print("Output:")
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
        print("Runtime Error:")
        print(format_error(runtime_error))


def main():
    if len(TEST_CASES) < 3:
        print("Error: At least THREE test cases are required.")
        return

    for i, test in enumerate(TEST_CASES[:3], start=1):
        compile_source(test["source"], f"Test Case {i}: {test['name']}")
        print()


if __name__ == "__main__":
    main()