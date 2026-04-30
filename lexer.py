# lexer.py

from tokens import Token, TokenType, KEYWORDS, OPERATORS, DELIMITERS
from errors import LexicalError


class LexicalAnalyzer:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tokens = []
        self.errors = []
        self.indent_stack = [0]

        # Longest operators first so == is recognized before =
        self.operator_order = sorted(OPERATORS.keys(), key=len, reverse=True)

    def tokenize(self):
        lines = self.source_code.splitlines()

        for line_number, raw_line in enumerate(lines, start=1):
            self._tokenize_line(raw_line, line_number)

        # Emit remaining DEDENTs at end of file
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(
                Token(TokenType.DEDENT, "<DEDENT>", len(lines) + 1, 1)
            )

        self.tokens.append(Token(TokenType.EOF, "<EOF>", len(lines) + 1, 1))
        return self.tokens, self.errors

    def _tokenize_line(self, raw_line: str, line_number: int):
        # Ignore completely blank lines
        if raw_line.strip() == "":
            return

        # Ignore full-line comments
        stripped = raw_line.lstrip(" \t")
        if stripped.startswith("#"):
            return

        indent_width = self._count_indent(raw_line)
        self._handle_indentation(indent_width, line_number)

        i = len(raw_line) - len(raw_line.lstrip(" \t"))

        while i < len(raw_line):
            ch = raw_line[i]
            column = i + 1

            # Skip spaces/tabs inside the line
            if ch in " \t":
                i += 1
                continue

            # Comment starts: ignore rest of line
            if ch == "#":
                break

            # String literal
            if ch == '"' or ch == "'":
                token, new_index = self._read_string(raw_line, line_number, i)
                if token is not None:
                    self.tokens.append(token)
                i = new_index
                continue

            # Identifier or keyword
            if ch.isalpha() or ch == "_":
                token, new_index = self._read_identifier_or_keyword(raw_line, line_number, i)
                self.tokens.append(token)
                i = new_index
                continue

            # Number literal
            if ch.isdigit():
                token, new_index = self._read_number(raw_line, line_number, i)
                if token is not None:
                    self.tokens.append(token)
                i = new_index
                continue

            # Operators
            matched_operator = self._match_operator(raw_line, i)
            if matched_operator is not None:
                self.tokens.append(
                    Token(
                        OPERATORS[matched_operator],
                        matched_operator,
                        line_number,
                        column
                    )
                )
                i += len(matched_operator)
                continue

            # Delimiters
            if ch in DELIMITERS:
                self.tokens.append(
                    Token(
                        DELIMITERS[ch],
                        ch,
                        line_number,
                        column
                    )
                )
                i += 1
                continue

            # Invalid character
            self._add_error(f"Invalid character '{ch}'", line_number, column)
            i += 1

        # Add NEWLINE token at the end of a meaningful line
        self.tokens.append(
            Token(TokenType.NEWLINE, "<NEWLINE>", line_number, len(raw_line) + 1)
        )

    def _count_indent(self, line: str) -> int:
        count = 0
        for ch in line:
            if ch == " ":
                count += 1
            elif ch == "\t":
                count += 4
            else:
                break
        return count

    def _handle_indentation(self, indent_width: int, line_number: int):
        current_indent = self.indent_stack[-1]

        if indent_width > current_indent:
            self.indent_stack.append(indent_width)
            self.tokens.append(Token(TokenType.INDENT, "<INDENT>", line_number, 1))

        elif indent_width < current_indent:
            while len(self.indent_stack) > 1 and indent_width < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, "<DEDENT>", line_number, 1))

            if self.indent_stack[-1] != indent_width:
                self._add_error("Invalid indentation level", line_number, 1)

    def _read_identifier_or_keyword(self, line: str, line_number: int, start: int):
        i = start
        while i < len(line) and (line[i].isalnum() or line[i] == "_"):
            i += 1

        value = line[start:i]
        token_type = KEYWORDS.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, line_number, start + 1), i

    def _read_number(self, line: str, line_number: int, start: int):
        i = start
        has_dot = False

        while i < len(line):
            if line[i].isdigit():
                i += 1
            elif line[i] == "." and not has_dot:
                has_dot = True
                i += 1
            else:
                break

        value = line[start:i]

        # Reject malformed float like "12."
        if value.endswith("."):
            self._add_error(f"Malformed number '{value}'", line_number, start + 1)
            return None, i

        token_type = TokenType.FLOAT if has_dot else TokenType.INTEGER
        return Token(token_type, value, line_number, start + 1), i

    def _read_string(self, line: str, line_number: int, start: int):
        quote_type = line[start]
        i = start + 1
        value_chars = []

        while i < len(line):
            ch = line[i]

            # Handle escaped characters
            if ch == "\\" and i + 1 < len(line):
                value_chars.append(ch)
                value_chars.append(line[i + 1])
                i += 2
                continue

            if ch == quote_type:
                full_value = quote_type + "".join(value_chars) + quote_type
                return Token(TokenType.STRING, full_value, line_number, start + 1), i + 1

            value_chars.append(ch)
            i += 1

        self._add_error("Unterminated string literal", line_number, start + 1)
        return None, len(line)

    def _match_operator(self, line: str, index: int):
        for op in self.operator_order:
            if line.startswith(op, index):
                return op
        return None

    def _add_error(self, message, line, column):
        self.errors.append(LexicalError(message, line=line, column=column).to_dict())