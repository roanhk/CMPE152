# main.py

from lexer import LexicalAnalyzer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from optimizer import CodeOptimizer
from code_generator import CodeGenerator
from test_cases import TEST_CASES


def compile_source(source_code: str, test_case_name: str = "Input Program"):
    print("=" * 60)
    print(f"Compiling: {test_case_name}")
    print("=" * 60)

    # 1. Lexical Analysis
    lexer = LexicalAnalyzer(source_code)
    tokens, lexical_errors = lexer.tokenize()

    if lexical_errors:
        print("Lexical Errors:")
        for err in lexical_errors:
            print(f"Line {err['line']}: {err['message']}")
        return

    # 2. Syntax Analysis / Parsing
    parser = Parser(tokens)
    ast, syntax_errors = parser.parse()

    if syntax_errors:
        print("Syntax Errors:")
        for err in syntax_errors:
            print(f"Line {err['line']}: {err['message']}")
        return

    # 3. Semantic Analysis
    semantic_analyzer = SemanticAnalyzer()
    semantic_errors = semantic_analyzer.analyze(ast)

    if semantic_errors:
        print("Semantic Errors:")
        for err in semantic_errors:
            print(f"Line {err['line']}: {err['message']}")
        return

    # 4. Optimization
    optimizer = CodeOptimizer()
    optimized_ast = optimizer.optimize(ast)

    # 5. Code Generation / Interpretation
    code_generator = CodeGenerator()
    result = code_generator.generate(optimized_ast)

    print("Compilation Successful.")
    print("Output:")
    print(result)


def main():
    # Run exactly three test cases
    for i, test in enumerate(TEST_CASES[:3], start=1):
        compile_source(test["source"], f"Test Case {i}: {test['name']}")


if __name__ == "__main__":
    main()