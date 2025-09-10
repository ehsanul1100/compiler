from dataclasses import dataclass

@dataclass
class ParseError:
    message: str
    line: int
    col: int

    def to_dict(self):
        return {"message": self.message, "line": self.line, "col": self.col}