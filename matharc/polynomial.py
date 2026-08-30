from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from typing import Any


class PolynomialError(ValueError):
    pass


@dataclass(frozen=True)
class Polynomial:
    coefficients: tuple[Fraction, ...]

    @classmethod
    def constant(cls, value: int | Fraction) -> "Polynomial":
        return cls((Fraction(value),)).trim()

    @classmethod
    def variable(cls) -> "Polynomial":
        return cls((Fraction(0), Fraction(1)))

    def trim(self) -> "Polynomial":
        values = list(self.coefficients)
        while len(values) > 1 and values[-1] == 0:
            values.pop()
        return Polynomial(tuple(values))

    def __add__(self, other: "Polynomial") -> "Polynomial":
        size = max(len(self.coefficients), len(other.coefficients))
        values = [Fraction(0)] * size
        for index in range(size):
            left = self.coefficients[index] if index < len(self.coefficients) else Fraction(0)
            right = other.coefficients[index] if index < len(other.coefficients) else Fraction(0)
            values[index] = left + right
        return Polynomial(tuple(values)).trim()

    def __neg__(self) -> "Polynomial":
        return Polynomial(tuple(-value for value in self.coefficients)).trim()

    def __sub__(self, other: "Polynomial") -> "Polynomial":
        return self + (-other)

    def __mul__(self, other: "Polynomial") -> "Polynomial":
        values = [Fraction(0)] * (len(self.coefficients) + len(other.coefficients) - 1)
        for left_index, left in enumerate(self.coefficients):
            for right_index, right in enumerate(other.coefficients):
                values[left_index + right_index] += left * right
        return Polynomial(tuple(values)).trim()

    def __pow__(self, exponent: int) -> "Polynomial":
        if exponent < 0 or exponent > 16:
            raise PolynomialError("exponent must be an integer in [0, 16]")
        result = Polynomial.constant(1)
        base = self
        power = exponent
        while power:
            if power & 1:
                result = result * base
            base = base * base
            power //= 2
        return result

    def evaluate(self, value: int) -> Fraction:
        result = Fraction(0)
        for coefficient in reversed(self.coefficients):
            result = result * value + coefficient
        return result

    def to_list(self) -> list[int | str]:
        result: list[int | str] = []
        for coefficient in self.coefficients:
            if coefficient.denominator == 1:
                result.append(coefficient.numerator)
            else:
                result.append(str(coefficient))
        return result


def parse_polynomial(expression: str, variable: str = "n") -> Polynomial:
    tree = ast.parse(expression, mode="eval")

    def convert(node: ast.AST) -> Polynomial:
        if isinstance(node, ast.Expression):
            return convert(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return Polynomial.constant(node.value)
        if isinstance(node, ast.Name) and node.id == variable:
            return Polynomial.variable()
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -convert(node.operand)
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Add):
                return convert(node.left) + convert(node.right)
            if isinstance(node.op, ast.Sub):
                return convert(node.left) - convert(node.right)
            if isinstance(node.op, ast.Mult):
                return convert(node.left) * convert(node.right)
            if isinstance(node.op, ast.Pow):
                if not isinstance(node.right, ast.Constant) or not isinstance(node.right.value, int):
                    raise PolynomialError("polynomial exponent must be an integer literal")
                return convert(node.left) ** node.right.value
        raise PolynomialError(f"unsupported polynomial syntax: {ast.dump(node)}")

    return convert(tree).trim()


def identity_certificate(lhs: str, rhs: str, variable: str = "n") -> dict[str, Any]:
    left = parse_polynomial(lhs, variable)
    right = parse_polynomial(rhs, variable)
    difference = (left - right).trim()
    return {
        "variable": variable,
        "lhs": lhs,
        "rhs": rhs,
        "lhs_coefficients": left.to_list(),
        "rhs_coefficients": right.to_list(),
        "difference_coefficients": difference.to_list(),
        "valid": all(value == 0 for value in difference.coefficients),
    }
