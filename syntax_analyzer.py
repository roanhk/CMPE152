# syntax_analyzer.py

from tokens import TokenType
from errors import SyntaxError as CompilerSyntaxError


class ParseAbort(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.errors = []

    def parse(self):
        """
        Entry point.
        Returns:
            (ast, syntax_errors)
        """
        program = {
            "type": "Program",
            "body": []
        }

        while not self._is_at_end():
            if self._match(TokenType.NEWLINE):
                continue

            try:
                stmt = self._statement()
                if stmt is not None:
                    program["body"].append(stmt)
            except ParseAbort:
                self._synchronize()

        return program, self.errors

    # ------------------------------------------------------------------
    # Core statement parsing
    # ------------------------------------------------------------------

    def _statement(self):
        if self._check(TokenType.IF):
            return self._if_statement()

        if self._check(TokenType.WHILE):
            return self._while_statement()

        if self._check(TokenType.PRINT):
            stmt = self._print_statement()
            self._consume_end_of_statement("Expected end of line after print statement.")
            return stmt

        if self._check(TokenType.IDENTIFIER) and self._check_next(TokenType.ASSIGN):
            stmt = self._assignment_statement()
            self._consume_end_of_statement("Expected end of line after assignment.")
            return stmt

        token = self._peek()
        self._error(token, f"Unexpected token '{token.value}'")

    def _assignment_statement(self):
        identifier = self._consume(TokenType.IDENTIFIER, "Expected identifier.")
        self._consume(TokenType.ASSIGN, "Expected '=' after identifier.")
        expr = self._expression()

        return {
            "type": "Assignment",
            "target": identifier.value,
            "value": expr,
            "line": identifier.line
        }

    def _print_statement(self):
        print_tok = self._consume(TokenType.PRINT, "Expected 'print'.")
        self._consume(TokenType.LPAREN, "Expected '(' after 'print'.")
        expr = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after print expression.")

        return {
            "type": "Print",
            "value": expr,
            "line": print_tok.line
        }

    def _if_statement(self):
        if_tok = self._consume(TokenType.IF, "Expected 'if'.")
        condition = self._expression()
        self._consume(TokenType.COLON, "Expected ':' after if condition.")
        if_body = self._block("Expected an indented block after if statement.")

        branches = [{
            "condition": condition,
            "body": if_body,
            "line": if_tok.line
        }]

        while self._match(TokenType.ELIF):
            elif_tok = self._previous()
            elif_condition = self._expression()
            self._consume(TokenType.COLON, "Expected ':' after elif condition.")
            elif_body = self._block("Expected an indented block after elif statement.")
            branches.append({
                "condition": elif_condition,
                "body": elif_body,
                "line": elif_tok.line
            })

        else_body = None
        else_line = None

        if self._match(TokenType.ELSE):
            else_tok = self._previous()
            self._consume(TokenType.COLON, "Expected ':' after else.")
            else_body = self._block("Expected an indented block after else statement.")
            else_line = else_tok.line

        return {
            "type": "If",
            "branches": branches,
            "else_body": else_body,
            "line": if_tok.line,
            "else_line": else_line
        }

    def _while_statement(self):
        while_tok = self._consume(TokenType.WHILE, "Expected 'while'.")
        condition = self._expression()
        self._consume(TokenType.COLON, "Expected ':' after while condition.")
        body = self._block("Expected an indented block after while statement.")

        return {
            "type": "While",
            "condition": condition,
            "body": body,
            "line": while_tok.line
        }

    def _block(self, error_message):
        """
        Expects:
            NEWLINE
            INDENT
            statement*
            DEDENT
        """
        self._consume(TokenType.NEWLINE, "Expected newline after ':'.")
        self._consume(TokenType.INDENT, error_message)

        statements = []

        while not self._check(TokenType.DEDENT) and not self._is_at_end():
            if self._match(TokenType.NEWLINE):
                continue

            try:
                stmt = self._statement()
                if stmt is not None:
                    statements.append(stmt)
            except ParseAbort:
                self._synchronize(in_block=True)

        self._consume(TokenType.DEDENT, "Expected end of indented block.")
        return statements

    def _consume_end_of_statement(self, message):
        if self._match(TokenType.NEWLINE):
            return

        if self._check(TokenType.EOF):
            return

        self._error(self._peek(), message)

    # ------------------------------------------------------------------
    # Expression parsing with precedence
    # ------------------------------------------------------------------

    def _expression(self):
        return self._or_expression()

    def _or_expression(self):
        expr = self._and_expression()

        while self._match(TokenType.OR):
            op = self._previous()
            right = self._and_expression()
            expr = {
                "type": "LogicalOp",
                "operator": op.value,
                "left": expr,
                "right": right,
                "line": op.line
            }

        return expr

    def _and_expression(self):
        expr = self._not_expression()

        while self._match(TokenType.AND):
            op = self._previous()
            right = self._not_expression()
            expr = {
                "type": "LogicalOp",
                "operator": op.value,
                "left": expr,
                "right": right,
                "line": op.line
            }

        return expr

    def _not_expression(self):
        if self._match(TokenType.NOT):
            op = self._previous()
            operand = self._not_expression()
            return {
                "type": "UnaryOp",
                "operator": op.value,
                "operand": operand,
                "line": op.line
            }

        return self._comparison()

    def _comparison(self):
        expr = self._additive()

        comparisons = []
        while self._match(
            TokenType.EQ,
            TokenType.NE,
            TokenType.LT,
            TokenType.LE,
            TokenType.GT,
            TokenType.GE
        ):
            op = self._previous()
            right = self._additive()
            comparisons.append({
                "operator": op.value,
                "right": right,
                "line": op.line
            })

        if comparisons:
            return {
                "type": "Compare",
                "left": expr,
                "comparisons": comparisons,
                "line": comparisons[0]["line"]
            }

        return expr

    def _additive(self):
        expr = self._multiplicative()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            right = self._multiplicative()
            expr = {
                "type": "BinaryOp",
                "operator": op.value,
                "left": expr,
                "right": right,
                "line": op.line
            }

        return expr

    def _multiplicative(self):
        expr = self._power()

        while self._match(
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.MODULO,
            TokenType.FLOOR_DIVIDE
        ):
            op = self._previous()
            right = self._power()
            expr = {
                "type": "BinaryOp",
                "operator": op.value,
                "left": expr,
                "right": right,
                "line": op.line
            }

        return expr

    def _power(self):
        expr = self._unary_arithmetic()

        if self._match(TokenType.POWER):
            op = self._previous()
            right = self._power()  # right-associative
            expr = {
                "type": "BinaryOp",
                "operator": op.value,
                "left": expr,
                "right": right,
                "line": op.line
            }

        return expr

    def _unary_arithmetic(self):
        if self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            operand = self._unary_arithmetic()
            return {
                "type": "UnaryOp",
                "operator": op.value,
                "operand": operand,
                "line": op.line
            }

        return self._primary()

    def _primary(self):
        if self._match(TokenType.INTEGER):
            tok = self._previous()
            return {
                "type": "Literal",
                "value": int(tok.value),
                "literal_type": "int",
                "line": tok.line
            }

        if self._match(TokenType.FLOAT):
            tok = self._previous()
            return {
                "type": "Literal",
                "value": float(tok.value),
                "literal_type": "float",
                "line": tok.line
            }

        if self._match(TokenType.STRING):
            tok = self._previous()
            return {
                "type": "Literal",
                "value": tok.value,
                "literal_type": "string",
                "line": tok.line
            }

        if self._match(TokenType.TRUE):
            tok = self._previous()
            return {
                "type": "Literal",
                "value": True,
                "literal_type": "bool",
                "line": tok.line
            }

        if self._match(TokenType.FALSE):
            tok = self._previous()
            return {
                "type": "Literal",
                "value": False,
                "literal_type": "bool",
                "line": tok.line
            }

        if self._match(TokenType.NONE):
            tok = self._previous()
            return {
                "type": "Literal",
                "value": None,
                "literal_type": "none",
                "line": tok.line
            }

        if self._match(TokenType.IDENTIFIER):
            tok = self._previous()
            return {
                "type": "Identifier",
                "name": tok.value,
                "line": tok.line
            }

        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        token = self._peek()
        self._error(token, f"Expected expression, found '{token.value}'")

    # ------------------------------------------------------------------
    # Error recovery
    # ------------------------------------------------------------------

    def _synchronize(self, in_block=False):
        while not self._is_at_end():
            if self.current > 0 and self._previous().type == TokenType.NEWLINE:
                return

            if self._check(TokenType.NEWLINE):
                self._advance()
                return

            if in_block and self._check(TokenType.DEDENT):
                return

            self._advance()

    def _error(self, token, message):
        self.errors.append(
            CompilerSyntaxError(
                message,
                line=token.line,
                column=token.column
            ).to_dict()
        )
        raise ParseAbort(message)

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    def _match(self, *types):
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _consume(self, token_type, message):
        if self._check(token_type):
            return self._advance()
        self._error(self._peek(), message)

    def _check(self, token_type):
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().type == token_type

    def _check_next(self, token_type):
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def _advance(self):
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self):
        return self._peek().type == TokenType.EOF

    def _peek(self):
        return self.tokens[self.current]

    def _previous(self):
        return self.tokens[self.current - 1]