# semantic_analyzer.py

from errors import SemanticError


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.symbol_table = {}

    def analyze(self, ast):
        """
        Entry point for semantic analysis.
        Returns a list of semantic errors.
        """
        self.errors = []
        self.symbol_table = {}

        if ast.get("type") != "Program":
            self._add_error("Invalid AST root. Expected Program.", line=0)
            return self.errors

        self._analyze_statements(ast.get("body", []), self.symbol_table)
        return self.errors

    # ------------------------------------------------------------------
    # Statement analysis
    # ------------------------------------------------------------------

    def _analyze_statements(self, statements, symbol_table):
        for stmt in statements:
            self._analyze_statement(stmt, symbol_table)

    def _analyze_statement(self, stmt, symbol_table):
        stmt_type = stmt.get("type")

        if stmt_type == "Assignment":
            expr_type = self._infer_expression_type(stmt["value"], symbol_table)
            symbol_table[stmt["target"]] = expr_type
            return

        if stmt_type == "Print":
            self._infer_expression_type(stmt["value"], symbol_table)
            return

        if stmt_type == "If":
            self._analyze_if(stmt, symbol_table)
            return

        if stmt_type == "While":
            self._analyze_while(stmt, symbol_table)
            return

        self._add_error(
            f"Unknown statement type '{stmt_type}'",
            line=stmt.get("line", 0)
        )

    def _analyze_if(self, stmt, symbol_table):
        """
        Conservative branch analysis:
        - analyze each branch independently
        - only promote variables after the if when:
          1) there is an else branch
          2) the variable exists in all branches
        - if types disagree across branches, resulting type becomes 'unknown'
        """
        branches = stmt.get("branches", [])
        else_body = stmt.get("else_body")
        branch_tables = []

        for branch in branches:
            self._infer_expression_type(branch["condition"], symbol_table)

            branch_scope = dict(symbol_table)
            self._analyze_statements(branch["body"], branch_scope)
            branch_tables.append(branch_scope)

        if else_body is not None:
            else_scope = dict(symbol_table)
            self._analyze_statements(else_body, else_scope)
            branch_tables.append(else_scope)

            merged = self._merge_branch_symbol_tables(branch_tables)
            symbol_table.clear()
            symbol_table.update(merged)

    def _analyze_while(self, stmt, symbol_table):
        """
        Conservative loop analysis:
        - analyze condition in current scope
        - analyze body in a copy
        - do not promote newly defined loop variables outside the loop,
          because the loop may execute zero times
        """
        self._infer_expression_type(stmt["condition"], symbol_table)

        loop_scope = dict(symbol_table)
        self._analyze_statements(stmt["body"], loop_scope)

    def _merge_branch_symbol_tables(self, branch_tables):
        if not branch_tables:
            return {}

        common_names = set(branch_tables[0].keys())
        for table in branch_tables[1:]:
            common_names &= set(table.keys())

        merged = {}
        for name in common_names:
            types = {table[name] for table in branch_tables}
            if len(types) == 1:
                merged[name] = types.pop()
            else:
                merged[name] = "unknown"

        return merged

    # ------------------------------------------------------------------
    # Expression analysis / type inference
    # ------------------------------------------------------------------

    def _infer_expression_type(self, expr, symbol_table):
        expr_type = expr.get("type")

        if expr_type == "Literal":
            return expr.get("literal_type", "unknown")

        if expr_type == "Identifier":
            return self._infer_identifier_type(expr, symbol_table)

        if expr_type == "UnaryOp":
            return self._infer_unary_type(expr, symbol_table)

        if expr_type == "BinaryOp":
            return self._infer_binary_type(expr, symbol_table)

        if expr_type == "LogicalOp":
            return self._infer_logical_type(expr, symbol_table)

        if expr_type == "Compare":
            return self._infer_compare_type(expr, symbol_table)

        self._add_error(
            f"Unknown expression type '{expr_type}'",
            line=expr.get("line", 0)
        )
        return "unknown"

    def _infer_identifier_type(self, expr, symbol_table):
        name = expr.get("name")
        line = expr.get("line", 0)

        if name not in symbol_table:
            self._add_error(
                f"Variable '{name}' used before assignment",
                line=line
            )
            return "unknown"

        return symbol_table[name]

    def _infer_unary_type(self, expr, symbol_table):
        operator = expr.get("operator")
        operand_type = self._infer_expression_type(expr.get("operand"), symbol_table)
        line = expr.get("line", 0)

        if operator in ("+", "-"):
            if operand_type not in ("int", "float", "unknown"):
                self._add_error(
                    f"Unary '{operator}' requires a numeric operand",
                    line=line
                )
                return "unknown"
            return operand_type

        if operator == "not":
            return "bool"

        self._add_error(
            f"Unsupported unary operator '{operator}'",
            line=line
        )
        return "unknown"

    def _infer_binary_type(self, expr, symbol_table):
        operator = expr.get("operator")
        left_type = self._infer_expression_type(expr.get("left"), symbol_table)
        right_type = self._infer_expression_type(expr.get("right"), symbol_table)
        line = expr.get("line", 0)

        if operator == "+":
            if self._is_numeric(left_type) and self._is_numeric(right_type):
                return self._numeric_result_type(left_type, right_type)

            if left_type == "string" and right_type == "string":
                return "string"

            if "unknown" not in (left_type, right_type):
                self._add_error(
                    "Operator '+' requires both operands to be numbers or both to be strings",
                    line=line
                )
            return "unknown"

        if operator in ("-", "*", "/", "%", "//", "**"):
            if self._is_numeric(left_type) and self._is_numeric(right_type):
                if operator == "/":
                    return "float"
                return self._numeric_result_type(left_type, right_type)

            if "unknown" not in (left_type, right_type):
                self._add_error(
                    f"Operator '{operator}' requires numeric operands",
                    line=line
                )
            return "unknown"

        self._add_error(
            f"Unsupported binary operator '{operator}'",
            line=line
        )
        return "unknown"

    def _infer_logical_type(self, expr, symbol_table):
        self._infer_expression_type(expr.get("left"), symbol_table)
        self._infer_expression_type(expr.get("right"), symbol_table)
        return "bool"

    def _infer_compare_type(self, expr, symbol_table):
        left_type = self._infer_expression_type(expr.get("left"), symbol_table)
        current_left_type = left_type

        for comp in expr.get("comparisons", []):
            operator = comp.get("operator")
            right_expr = comp.get("right")
            right_type = self._infer_expression_type(right_expr, symbol_table)
            line = comp.get("line", expr.get("line", 0))

            if operator in ("<", "<=", ">", ">="):
                if not self._comparison_types_compatible(current_left_type, right_type):
                    if "unknown" not in (current_left_type, right_type):
                        self._add_error(
                            f"Operator '{operator}' used with incompatible operand types",
                            line=line
                        )

            elif operator in ("==", "!="):
                pass

            else:
                self._add_error(
                    f"Unsupported comparison operator '{operator}'",
                    line=line
                )

            current_left_type = right_type

        return "bool"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_numeric(self, type_name):
        return type_name in ("int", "float")

    def _numeric_result_type(self, left_type, right_type):
        if "float" in (left_type, right_type):
            return "float"
        if left_type == "int" and right_type == "int":
            return "int"
        return "unknown"

    def _comparison_types_compatible(self, left_type, right_type):
        if left_type == "unknown" or right_type == "unknown":
            return True

        if self._is_numeric(left_type) and self._is_numeric(right_type):
            return True

        if left_type == right_type:
            return True

        return False

    def _add_error(self, message, line=None, column=None):
        self.errors.append(
            SemanticError(message, line=line, column=column).to_dict()
        )