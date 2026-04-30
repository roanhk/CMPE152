# semantic_analyzer.py

from errors import SemanticError
from ast_nodes import (
    Program, Assignment, Print, If, IfBranch, While,
    Literal, Identifier, UnaryOp, BinaryOp, LogicalOp,
    CompareOp, ComparisonPart
)


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.symbol_table = {}

    def analyze(self, tree):
        self.errors = []
        self.symbol_table = {}

        if not isinstance(tree, Program):
            self._add_error("Invalid AST root. Expected Program.", line=0)
            return self.errors

        self.visit(tree, self.symbol_table)
        return self.errors

    # ---------------------------------
    # Generic visitor
    # ---------------------------------

    def visit(self, node, scope):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node, scope)

    def generic_visit(self, node, scope):
        self._add_error(f"No visit method for node type '{type(node).__name__}'", line=0)
        return "unknown"

    # ---------------------------------
    # Program / Statements
    # ---------------------------------

    def visit_Program(self, node, scope):
        for stmt in node.body:
            self.visit(stmt, scope)

    def visit_Assignment(self, node, scope):
        expr_type = self.visit(node.value, scope)
        scope[node.target] = expr_type
        return expr_type

    def visit_Print(self, node, scope):
        self.visit(node.value, scope)
        return None

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

        return None

    def visit_IfBranch(self, node, scope):
        self.visit(node.condition, scope)
        for stmt in node.body:
            self.visit(stmt, scope)
        return None

    def visit_While(self, node, scope):
        self.visit(node.condition, scope)

        loop_scope = dict(scope)
        for stmt in node.body:
            self.visit(stmt, loop_scope)

        # Do not promote loop-defined vars outside
        return None

    # ---------------------------------
    # Expressions
    # ---------------------------------

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

            elif comp.operator in ("==", "!="):
                pass
            else:
                self._add_error(
                    f"Unsupported comparison operator '{comp.operator}'",
                    line=comp.line
                )

            current_left_type = right_type

        return "bool"

    # ---------------------------------
    # Helpers
    # ---------------------------------

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