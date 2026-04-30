# optimizer.py

class CodeOptimizer:
    def optimize(self, ast):
        """
        Entry point for optimization.
        Returns an optimized AST.
        """
        if ast.get("type") != "Program":
            return ast

        return {
            "type": "Program",
            "body": self._optimize_statements(ast.get("body", []))
        }

    # ------------------------------------------------------------------
    # Statement optimization
    # ------------------------------------------------------------------

    def _optimize_statements(self, statements):
        optimized = []

        for stmt in statements:
            result = self._optimize_statement(stmt)

            if result is None:
                continue

            if isinstance(result, list):
                optimized.extend(result)
            else:
                optimized.append(result)

        return optimized

    def _optimize_statement(self, stmt):
        stmt_type = stmt.get("type")

        if stmt_type == "Assignment":
            return {
                "type": "Assignment",
                "target": stmt["target"],
                "value": self._optimize_expression(stmt["value"]),
                "line": stmt["line"]
            }

        if stmt_type == "Print":
            return {
                "type": "Print",
                "value": self._optimize_expression(stmt["value"]),
                "line": stmt["line"]
            }

        if stmt_type == "If":
            return self._optimize_if(stmt)

        if stmt_type == "While":
            return self._optimize_while(stmt)

        return stmt

    def _optimize_if(self, stmt):
        optimized_branches = []

        for branch in stmt.get("branches", []):
            optimized_condition = self._optimize_expression(branch["condition"])
            optimized_body = self._optimize_statements(branch["body"])

            literal_value, is_literal = self._get_literal_value(optimized_condition)

            # If condition is literally True, only this body can ever run.
            if is_literal and self._is_truthy(literal_value):
                return optimized_body

            # If condition is literally False, skip this branch.
            if is_literal and not self._is_truthy(literal_value):
                continue

            optimized_branches.append({
                "condition": optimized_condition,
                "body": optimized_body,
                "line": branch["line"]
            })

        else_body = stmt.get("else_body")
        optimized_else = None
        if else_body is not None:
            optimized_else = self._optimize_statements(else_body)

        # If all branches were removed and only else remains, replace if with else body.
        if not optimized_branches:
            if optimized_else is not None:
                return optimized_else
            return None

        return {
            "type": "If",
            "branches": optimized_branches,
            "else_body": optimized_else,
            "line": stmt["line"],
            "else_line": stmt.get("else_line")
        }

    def _optimize_while(self, stmt):
        optimized_condition = self._optimize_expression(stmt["condition"])
        optimized_body = self._optimize_statements(stmt["body"])

        literal_value, is_literal = self._get_literal_value(optimized_condition)

        # while False: remove completely
        if is_literal and not self._is_truthy(literal_value):
            return None

        return {
            "type": "While",
            "condition": optimized_condition,
            "body": optimized_body,
            "line": stmt["line"]
        }

    # ------------------------------------------------------------------
    # Expression optimization
    # ------------------------------------------------------------------

    def _optimize_expression(self, expr):
        expr_type = expr.get("type")

        if expr_type in ("Literal", "Identifier"):
            return expr

        if expr_type == "UnaryOp":
            return self._optimize_unary(expr)

        if expr_type == "BinaryOp":
            return self._optimize_binary(expr)

        if expr_type == "LogicalOp":
            return self._optimize_logical(expr)

        if expr_type == "Compare":
            return self._optimize_compare(expr)

        return expr

    def _optimize_unary(self, expr):
        operand = self._optimize_expression(expr["operand"])
        operator = expr["operator"]

        value, is_literal = self._get_literal_value(operand)
        if is_literal:
            try:
                if operator == "+":
                    return self._make_literal(+value, expr["line"])
                if operator == "-":
                    return self._make_literal(-value, expr["line"])
                if operator == "not":
                    return self._make_literal(not self._is_truthy(value), expr["line"])
            except Exception:
                pass

        return {
            "type": "UnaryOp",
            "operator": operator,
            "operand": operand,
            "line": expr["line"]
        }

    def _optimize_binary(self, expr):
        left = self._optimize_expression(expr["left"])
        right = self._optimize_expression(expr["right"])
        operator = expr["operator"]

        left_value, left_is_literal = self._get_literal_value(left)
        right_value, right_is_literal = self._get_literal_value(right)

        if left_is_literal and right_is_literal:
            try:
                if operator == "+":
                    return self._make_literal(left_value + right_value, expr["line"])
                if operator == "-":
                    return self._make_literal(left_value - right_value, expr["line"])
                if operator == "*":
                    return self._make_literal(left_value * right_value, expr["line"])
                if operator == "/":
                    return self._make_literal(left_value / right_value, expr["line"])
                if operator == "%":
                    return self._make_literal(left_value % right_value, expr["line"])
                if operator == "//":
                    return self._make_literal(left_value // right_value, expr["line"])
                if operator == "**":
                    return self._make_literal(left_value ** right_value, expr["line"])
            except Exception:
                pass

        return {
            "type": "BinaryOp",
            "operator": operator,
            "left": left,
            "right": right,
            "line": expr["line"]
        }

    def _optimize_logical(self, expr):
        left = self._optimize_expression(expr["left"])
        right = self._optimize_expression(expr["right"])
        operator = expr["operator"]

        left_value, left_is_literal = self._get_literal_value(left)
        right_value, right_is_literal = self._get_literal_value(right)

        # Match current code_generator semantics:
        # and/or evaluate to True/False, not Python's operand-returning behavior.
        if left_is_literal and right_is_literal:
            try:
                if operator == "and":
                    return self._make_literal(
                        self._is_truthy(left_value) and self._is_truthy(right_value),
                        expr["line"]
                    )
                if operator == "or":
                    return self._make_literal(
                        self._is_truthy(left_value) or self._is_truthy(right_value),
                        expr["line"]
                    )
            except Exception:
                pass

        # Simple short-circuit reductions
        if left_is_literal:
            if operator == "and":
                if not self._is_truthy(left_value):
                    return self._make_literal(False, expr["line"])
            if operator == "or":
                if self._is_truthy(left_value):
                    return self._make_literal(True, expr["line"])

        return {
            "type": "LogicalOp",
            "operator": operator,
            "left": left,
            "right": right,
            "line": expr["line"]
        }

    def _optimize_compare(self, expr):
        left = self._optimize_expression(expr["left"])
        optimized_comparisons = []

        all_literal = True
        current_left = left

        current_value, current_is_literal = self._get_literal_value(current_left)
        if not current_is_literal:
            all_literal = False

        for comp in expr.get("comparisons", []):
            optimized_right = self._optimize_expression(comp["right"])
            optimized_comparisons.append({
                "operator": comp["operator"],
                "right": optimized_right,
                "line": comp["line"]
            })

            right_value, right_is_literal = self._get_literal_value(optimized_right)
            if not right_is_literal:
                all_literal = False
            else:
                current_value = right_value

        if all_literal:
            try:
                result = self._evaluate_compare_literal_chain(left, optimized_comparisons)
                return self._make_literal(result, expr["line"])
            except Exception:
                pass

        return {
            "type": "Compare",
            "left": left,
            "comparisons": optimized_comparisons,
            "line": expr["line"]
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _evaluate_compare_literal_chain(self, left_expr, comparisons):
        left_value, _ = self._get_literal_value(left_expr)

        for comp in comparisons:
            right_value, _ = self._get_literal_value(comp["right"])
            operator = comp["operator"]

            if operator == "==":
                ok = left_value == right_value
            elif operator == "!=":
                ok = left_value != right_value
            elif operator == "<":
                ok = left_value < right_value
            elif operator == "<=":
                ok = left_value <= right_value
            elif operator == ">":
                ok = left_value > right_value
            elif operator == ">=":
                ok = left_value >= right_value
            else:
                raise ValueError(f"Unsupported comparison operator: {operator}")

            if not ok:
                return False

            left_value = right_value

        return True

    def _get_literal_value(self, expr):
        if expr.get("type") != "Literal":
            return None, False
        return expr.get("value"), True

    def _make_literal(self, value, line):
        if isinstance(value, bool):
            literal_type = "bool"
        elif isinstance(value, int) and not isinstance(value, bool):
            literal_type = "int"
        elif isinstance(value, float):
            literal_type = "float"
        elif isinstance(value, str):
            literal_type = "string"
        elif value is None:
            literal_type = "none"
        else:
            literal_type = "unknown"

        return {
            "type": "Literal",
            "value": value,
            "literal_type": literal_type,
            "line": line
        }

    def _is_truthy(self, value):
        return bool(value)