# code_generator.py

class CodeGenerator:
    def __init__(self):
        self.symbol_table = {}
        self.output = []

    def generate(self, ast):
        """
        Interprets the AST and returns the program output as a string.
        """
        self.symbol_table = {}
        self.output = []

        if ast.get("type") != "Program":
            raise ValueError("Invalid AST root. Expected Program.")

        self._execute_statements(ast.get("body", []))
        return "\n".join(self.output)

    # ------------------------------------------------------------------
    # Statement execution
    # ------------------------------------------------------------------

    def _execute_statements(self, statements):
        for stmt in statements:
            self._execute_statement(stmt)

    def _execute_statement(self, stmt):
        stmt_type = stmt.get("type")

        if stmt_type == "Assignment":
            value = self._evaluate_expression(stmt["value"])
            self.symbol_table[stmt["target"]] = value
            return

        if stmt_type == "Print":
            value = self._evaluate_expression(stmt["value"])
            self.output.append(self._format_output(value))
            return

        if stmt_type == "If":
            self._execute_if(stmt)
            return

        if stmt_type == "While":
            self._execute_while(stmt)
            return

        raise ValueError(f"Unknown statement type: {stmt_type}")

    def _execute_if(self, stmt):
        for branch in stmt.get("branches", []):
            condition_value = self._evaluate_expression(branch["condition"])
            if self._is_truthy(condition_value):
                self._execute_statements(branch["body"])
                return

        else_body = stmt.get("else_body")
        if else_body is not None:
            self._execute_statements(else_body)

    def _execute_while(self, stmt):
        while self._is_truthy(self._evaluate_expression(stmt["condition"])):
            self._execute_statements(stmt["body"])

    # ------------------------------------------------------------------
    # Expression evaluation
    # ------------------------------------------------------------------

    def _evaluate_expression(self, expr):
        expr_type = expr.get("type")

        if expr_type == "Literal":
            return self._convert_literal(expr)

        if expr_type == "Identifier":
            name = expr["name"]
            if name not in self.symbol_table:
                raise NameError(f"Variable '{name}' used before assignment")
            return self.symbol_table[name]

        if expr_type == "UnaryOp":
            return self._evaluate_unary(expr)

        if expr_type == "BinaryOp":
            return self._evaluate_binary(expr)

        if expr_type == "LogicalOp":
            return self._evaluate_logical(expr)

        if expr_type == "Compare":
            return self._evaluate_compare(expr)

        raise ValueError(f"Unknown expression type: {expr_type}")

    def _convert_literal(self, expr):
        literal_type = expr.get("literal_type")
        value = expr.get("value")

        if literal_type == "string":
            return self._strip_quotes(value)

        return value

    def _evaluate_unary(self, expr):
        operator = expr["operator"]
        operand = self._evaluate_expression(expr["operand"])

        if operator == "+":
            return +operand
        if operator == "-":
            return -operand
        if operator == "not":
            return not self._is_truthy(operand)

        raise ValueError(f"Unsupported unary operator: {operator}")

    def _evaluate_binary(self, expr):
        operator = expr["operator"]
        left = self._evaluate_expression(expr["left"])
        right = self._evaluate_expression(expr["right"])

        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            return left / right
        if operator == "%":
            return left % right
        if operator == "//":
            return left // right
        if operator == "**":
            return left ** right

        raise ValueError(f"Unsupported binary operator: {operator}")

    def _evaluate_logical(self, expr):
        operator = expr["operator"]

        if operator == "and":
            left = self._evaluate_expression(expr["left"])
            if not self._is_truthy(left):
                return False
            right = self._evaluate_expression(expr["right"])
            return self._is_truthy(right)

        if operator == "or":
            left = self._evaluate_expression(expr["left"])
            if self._is_truthy(left):
                return True
            right = self._evaluate_expression(expr["right"])
            return self._is_truthy(right)

        raise ValueError(f"Unsupported logical operator: {operator}")

    def _evaluate_compare(self, expr):
        left = self._evaluate_expression(expr["left"])

        for comp in expr.get("comparisons", []):
            operator = comp["operator"]
            right = self._evaluate_expression(comp["right"])

            if not self._apply_comparison(left, operator, right):
                return False

            left = right

        return True

    def _apply_comparison(self, left, operator, right):
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right

        raise ValueError(f"Unsupported comparison operator: {operator}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _strip_quotes(self, value):
        if isinstance(value, str) and len(value) >= 2:
            if (value[0] == value[-1]) and value[0] in ("'", '"'):
                return value[1:-1]
        return value

    def _is_truthy(self, value):
        return bool(value)

    def _format_output(self, value):
        if value is True:
            return "True"
        if value is False:
            return "False"
        if value is None:
            return "None"
        return str(value)