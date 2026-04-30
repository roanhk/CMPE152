# ast_nodes.py

class ASTNode:
    pass


class Program(ASTNode):
    def __init__(self, body):
        self.body = body


# -----------------------------
# Statement Nodes
# -----------------------------

class Assignment(ASTNode):
    def __init__(self, target, value, line):
        self.target = target
        self.value = value
        self.line = line


class Print(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line


class If(ASTNode):
    def __init__(self, branches, else_body, line, else_line=None):
        self.branches = branches          # list of IfBranch
        self.else_body = else_body        # list of statements or None
        self.line = line
        self.else_line = else_line


class IfBranch(ASTNode):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line


class While(ASTNode):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line


# -----------------------------
# Expression Nodes
# -----------------------------

class Literal(ASTNode):
    def __init__(self, value, literal_type, line):
        self.value = value
        self.literal_type = literal_type
        self.line = line


class Identifier(ASTNode):
    def __init__(self, name, line):
        self.name = name
        self.line = line


class UnaryOp(ASTNode):
    def __init__(self, operator, operand, line):
        self.operator = operator
        self.operand = operand
        self.line = line


class BinaryOp(ASTNode):
    def __init__(self, operator, left, right, line):
        self.operator = operator
        self.left = left
        self.right = right
        self.line = line


class LogicalOp(ASTNode):
    def __init__(self, operator, left, right, line):
        self.operator = operator
        self.left = left
        self.right = right
        self.line = line


class CompareOp(ASTNode):
    def __init__(self, left, comparisons, line):
        self.left = left
        self.comparisons = comparisons    # list of ComparisonPart
        self.line = line


class ComparisonPart(ASTNode):
    def __init__(self, operator, right, line):
        self.operator = operator
        self.right = right
        self.line = line