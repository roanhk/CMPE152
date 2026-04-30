# errors.py

class CompilerError(Exception):
    def __init__(self, message, line=None, column=None, error_type="Compiler Error"):
        self.message = message
        self.line = line
        self.column = column
        self.error_type = error_type
        super().__init__(self.__str__())

    def __str__(self):
        location = ""

        if self.line is not None and self.column is not None:
            location = f"Line {self.line}, Column {self.column}: "
        elif self.line is not None:
            location = f"Line {self.line}: "

        return f"{location}{self.error_type}: {self.message}"

    def to_dict(self):
        return {
            "line": self.line,
            "column": self.column,
            "type": self.error_type,
            "message": self.message
        }


class LexicalError(CompilerError):
    def __init__(self, message, line=None, column=None):
        super().__init__(message, line, column, error_type="Lexical Error")


class SyntaxError(CompilerError):
    def __init__(self, message, line=None, column=None):
        super().__init__(message, line, column, error_type="Syntax Error")


class SemanticError(CompilerError):
    def __init__(self, message, line=None, column=None):
        super().__init__(message, line, column, error_type="Semantic Error")


class RuntimeExecutionError(CompilerError):
    def __init__(self, message, line=None, column=None):
        super().__init__(message, line, column, error_type="Runtime Error")


def format_error(error):
    """
    Accepts either:
    - a CompilerError object
    - a dictionary like:
      {"line": 2, "column": 5, "message": "..."}
    """
    if isinstance(error, CompilerError):
        return str(error)

    if isinstance(error, dict):
        line = error.get("line")
        column = error.get("column")
        message = error.get("message", "Unknown error")
        error_type = error.get("type", "Error")

        if line is not None and column is not None:
            return f"Line {line}, Column {column}: {error_type}: {message}"
        if line is not None:
            return f"Line {line}: {error_type}: {message}"
        return f"{error_type}: {message}"

    return str(error)


def format_error_list(errors):
    return [format_error(error) for error in errors]