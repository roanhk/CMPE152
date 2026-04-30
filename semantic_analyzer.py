# semantic_analyzer.py

from errors import SemanticError

try:
    from ast_nodes import (
        Program, Assignment, Print, If, IfBranch, While,
        Literal, Identifier, UnaryOp, BinaryOp, LogicalOp,
        CompareOp, ComparisonPart
    )
    AST_NODES_AVAILABLE = True
except ImportError:
    AST_NODES_AVAILABLE = False


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.symbol_table = {}

    def analyze(self, tree):
        self.errors = []
        self.symbol_table = {}

        # Accept either dict-style AST or AST-node-style tree
        if self._is_dict_program(tree):
            self._analyze_dict_program(tree, self.symbol_table)
            return self.errors

        if AST_NODES_AVAILABLE and isinstance(tree, Program):
            self.visit(tree, self.symbol_table)
            return self.errors

        self._add_error("Invalid AST root. Expected Program.", line=0)
        return self.errors

    # ==========================================================
    # DICT-STYLE AST SUPPORT
    # ==========================================================

    def _is_dict_program(self, tree):
        return isinstance(tree, dict) and tree.get("type") == "Program"

    def _analyze_dict_program(self, tree, scope):
        for stmt in tree.get("body", []):
            self._analyze_dict_statement(stmt, scope)

    def _analyze_dict_statement(self, stmt, scope):
        stmt_type = stmt.get("type")

        if stmt_type == "Assignment":
            expr_type = self._infer_dict_expression_type(stmt["value"], scope)
            scope[stmt["target"]] = expr_type
            return

        if stmt_type == "Print":
            self._infer_dict_expression_type(stmt["value"], scope)
            return

        if stmt_type == "If":
            self._analyze_dict_if(stmt, scope)
            return

        if stmt_type == "While":
            self._analyze_dict_while(stmt, scope)
            return

        self._add_error(
            f"Unknown statement type '{stmt_type}'",
            line=stmt.get("line", 0)
        )

    def _analyze_dict_if(self, stmt, scope):
        branches = stmt.get("branches", [])
        else_body = stmt.get("else_body")
        branch_scopes = []

        for branch in branches:
            self._infer_dict_expression_type(branch["condition"], scope)

            local_scope = dict(scope)
            for child_stmt in branch["body"]:
                self._analyze_dict_statement(child_stmt, local_scope)
            branch_scopes.append(local_scope)

        if else_body is not None:
            else_scope = dict(scope)
            for child_stmt in else_body:
                self._analyze_dict_statement(child_stmt, else_scope)
            branch_scopes.append(else_scope)

            merged_scope = self._merge_branch_scopes(branch_scopes)
            scope.clear()
            scope.update(merged_scope)

    def _analyze_dict_while(self, stmt, scope):
        self._infer_dict_expression_type(stmt["condition"], scope)

        loop_scope = dict(scope)
        for child_stmt in stmt["body"]:
            self._analyze_dict_statement(child_stmt, loop_scope)

    def _infer_dict_expression_type(self, expr, scope):
        expr_type = expr.get("type")

        if expr_type == "Literal":
            return expr.get("literal_type", "unknown")

        if expr_type == "Identifier":
            name = expr.get("name")
            if name not in scope:
                self._add_error(
                    f"Variable '{name}' used before assignment",
                    line=expr.get("line", 0)
                )
                return "unknown"
            return scope[name]

        if expr_type == "UnaryOp":
            operand_type = self._infer_dict_expression_type(expr["operand"], scope)

            if expr["operator"] in ("+", "-"):
                if operand_type not in ("int", "float", "unknown"):
                    self._add_error(
                        f"Unary '{expr['operator']}' requires a numeric operand",
                        line=expr.get("line", 0)
                    )
                    return "unknown"
                return operand_type

            if expr["operator"] == "not":
                return "bool"

            self._add_error(
                f"Unsupported unary operator '{expr['operator']}'",
                line=expr.get("line", 0)
            )
            return "unknown"

        if expr_type == "BinaryOp":
            left_type = self._infer_dict_expression_type(expr["left"], scope)
            right_type = self._infer_dict_expression_type(expr["right"], scope)
            op = expr["operator"]

            if op == "+":
                if self._is_numeric(left_type) and self._is_numeric(right_type):
                    return self._numeric_result_type(left_type, right_type)

                if left_type == "string" and right_type == "string":
                    return "string"

                if "unknown" not in (left_type, right_type):
                    self._add_error(
                        "Operator '+' requires both operands to be numbers or both to be strings",
                        line=expr.get("line", 0)
                    )
                return "unknown"

            if op in ("-", "*", "/", "%", "//", "**"):
                if self._is_numeric(left_type) and self._is_numeric(right_type):
                    if op == "/":
                        return "float"
                    return self._numeric_result_type(left_type, right_type)

                if "unknown" not in (left_type, right_type):
                    self._add_error(
                        f"Operator '{op}' requires numeric operands",
                        line=expr.get("line", 0)
                    )
                return "unknown"

            self._add_error(
                f"Unsupported binary operator '{op}'",
                line=expr.get("line", 0)
            )
            return "unknown"

        if expr_type == "LogicalOp":
            self._infer_dict_expression_type(expr["left"], scope)
            self._infer_dict_expression_type(expr["right"], scope)
            return "bool"

        if expr_type == "Compare":
            current_left_type = self._infer_dict_expression_type(expr["left"], scope)

            for comp in expr.get("comparisons", []):
                right_type = self._infer_dict_expression_type(comp["right"], scope)

                if comp["operator"] in ("<", "<=", ">", ">="):
                    if not self._comparison_types_compatible(current_left_type, right_type):
                        if "unknown" not in (current_left_type, right_type):
                            self._add_error(
                                f"Operator '{comp['operator']}' used with incompatible operand types",
                                line=comp.get("line", expr.get("line", 0))
                            )

                current_left_type = right_type

            return "bool"

        self._add_error(
            f"Unknown expression type '{expr_type}'",
            line=expr.get("line", 0)
        )
        return "unknown"

    # ==========================================================
    # AST-NODE TREE SUPPORT
    # ==========================================================

    def visit(self, node, scope):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node, scope)

    def generic_visit(self, node, scope):
        self._add_error(f"No visit method for node type '{type(node).__name__}'", line=0)
        return "unknown"

    def visit_Program(self, node, scope):
        for stmt in node.body:
            self.visit(stmt, scope)

    def visit_Assignment(self, node, scope):
        expr_type = self.visit(node.value, scope)
        scope[node.target] = expr_type
        return expr_type

    def visit_Print(self, node, scope):
        self.visit(node.value, scope)

    def visit_If(self, node, scope):
        branch_scopes = []

        for branch in node.branches:
            self.visit(branch.condition, scope)

            local_scope = dict(scope)
            for stmt in branch.body:
                self.visit(stmt, local_scope)
            branch_scopes.append(local_scope)

        if node.else_body is not None:
            else_scope = dict(scope)
            for stmt in node.else_body:
                self.visit(stmt, else_scope)
            branch_scopes.append(else_scope)

            merged_scope = self._merge_branch_scopes(branch_scopes)
            scope.clear()
            scope.update(merged_scope)

    def visit_While(self, node, scope):
        self.visit(node.condition, scope)

        loop_scope = dict(scope)
        for stmt in node.body:
            self.visit(stmt, loop_scope)

    def visit_Literal(self, node, scope):
        return node.literal_type

    def visit_Identifier(self, node, scope):
        if node.name not in scope:
            self._add_error(
                f"Variable '{node.name}' used before assignment",
                line=node.line
            )
            return "unknown"
        return scope[node.name]

    def visit_UnaryOp(self, node, scope):
        operand_type = self.visit(node.operand, scope)

        if node.operator in ("+", "-"):
            if operand_type not in ("int", "float", "unknown"):
                self._add_error(
                    f"Unary '{node.operator}' requires a numeric operand",
                    line=node.line
                )
                return "unknown"
            return operand_type

        if node.operator == "not":
            return "bool"

        self._add_error(
            f"Unsupported unary operator '{node.operator}'",
            line=node.line
        )
        return "unknown"

    def visit_BinaryOp(self, node, scope):
        left_type = self.visit(node.left, scope)
        right_type = self.visit(node.right, scope)

        if node.operator == "+":
            if self._is_numeric(left_type) and self._is_numeric(right_type):
                return self._numeric_result_type(left_type, right_type)

            if left_type == "string" and right_type == "string":
                return "string"

            if "unknown" not in (left_type, right_type):
                self._add_error(
                    "Operator '+' requires both operands to be numbers or both to be strings",
                    line=node.line
                )
            return "unknown"

        if node.operator in ("-", "*", "/", "%", "//", "**"):
            if self._is_numeric(left_type) and self._is_numeric(right_type):
                if node.operator == "/":
                    return "float"
                return self._numeric_result_type(left_type, right_type)

            if "unknown" not in (left_type, right_type):
                self._add_error(
                    f"Operator '{node.operator}' requires numeric operands",
                    line=node.line
                )
            return "unknown"

        self._add_error(
            f"Unsupported binary operator '{node.operator}'",
            line=node.line
        )
        return "unknown"

    def visit_LogicalOp(self, node, scope):
        self.visit(node.left, scope)
        self.visit(node.right, scope)
        return "bool"

    def visit_CompareOp(self, node, scope):
        current_left_type = self.visit(node.left, scope)

        for comp in node.comparisons:
            right_type = self.visit(comp.right, scope)

            if comp.operator in ("<", "<=", ">", ">="):
                if not self._comparison_types_compatible(current_left_type, right_type):
                    if "unknown" not in (current_left_type, right_type):
                        self._add_error(
                            f"Operator '{comp.operator}' used with incompatible operand types",
                            line=comp.line
                        )

            current_left_type = right_type

        return "bool"

    # ==========================================================
    # Helpers
    # ==========================================================

    def _merge_branch_scopes(self, branch_scopes):
        if not branch_scopes:
            return {}

        common_names = set(branch_scopes[0].keys())
        for scope in branch_scopes[1:]:
            common_names &= set(scope.keys())

        merged = {}
        for name in common_names:
            types = {scope[name] for scope in branch_scopes}
            merged[name] = types.pop() if len(types) == 1 else "unknown"

        return merged

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