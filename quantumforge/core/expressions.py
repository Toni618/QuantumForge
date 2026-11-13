"""Restricted mathematical expression parser; never evaluates Python code."""
from __future__ import annotations
import ast
import math
import sympy as sp

_ALLOWED_BINARY = {ast.Add: lambda a,b: a+b, ast.Sub: lambda a,b: a-b,
                   ast.Mult: lambda a,b: a*b, ast.Div: lambda a,b: a/b,
                   ast.Pow: lambda a,b: a**b}
_ALLOWED_UNARY = {ast.UAdd: lambda a: a, ast.USub: lambda a: -a}
_FUNCTIONS = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp,
              "log": sp.log, "sqrt": sp.sqrt, "sinh": sp.sinh, "cosh": sp.cosh,
              "abs": sp.Abs}
_CONSTANTS = {"pi": sp.pi, "E": sp.E}

class ExpressionError(ValueError):
    pass

def parse_expression(source: str, variables: tuple[str, ...] = ()) -> sp.Expr:
    if not isinstance(source, str) or not source.strip() or len(source) > 2000:
        raise ExpressionError("Expression must be a non-empty string of at most 2000 characters")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Invalid expression syntax: {exc.msg}") from exc
    if sum(1 for _ in ast.walk(tree)) > 128:
        raise ExpressionError("Expression is too complex (maximum 128 syntax nodes)")
    allowed_names = set(variables) | set(_CONSTANTS) | set(_FUNCTIONS)
    def visit(node):
        if isinstance(node, ast.Expression): return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if isinstance(node.value, float) and not math.isfinite(node.value):
                raise ExpressionError("Non-finite numeric literals are not allowed")
            return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)
        if isinstance(node, ast.Name):
            if node.id not in allowed_names: raise ExpressionError(f"Unknown symbol: {node.id}")
            if node.id in _CONSTANTS: return _CONSTANTS[node.id]
            if node.id in _FUNCTIONS: raise ExpressionError(f"Function {node.id} must be called")
            return sp.Symbol(node.id, real=True)
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY:
            return _ALLOWED_BINARY[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](visit(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and len(node.args) == 1 and not node.keywords:
            return _FUNCTIONS[node.func.id](visit(node.args[0]))
        raise ExpressionError(f"Unsupported expression construct: {type(node).__name__}")
    result = visit(tree)
    if result.free_symbols - {sp.Symbol(v, real=True) for v in variables}:
        raise ExpressionError("Expression contains undeclared variables")
    return result
