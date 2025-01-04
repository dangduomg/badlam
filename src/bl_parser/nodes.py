"""AST node classes"""


from abc import ABC
from dataclasses import dataclass

from lark import Token
from lark.tree import Meta
from lark.ast_utils import Ast, WithMeta


# pylint: disable=too-few-public-methods


class _Expr(Ast, WithMeta, ABC):
    """Expression base class"""
    meta: Meta


@dataclass(frozen=True)
class Paren(_Expr):
    """Parenthesized expression"""
    meta: Meta
    expr: _Expr

    def __str__(self) -> str:
        return f"({self.expr})"


@dataclass(frozen=True)
class Call(_Expr):
    """Function call operation"""
    meta: Meta
    callee: _Expr
    arg: _Expr

    def __str__(self) -> str:
        return f"{self.callee} {self.arg}"


@dataclass(frozen=True)
class Var(_Expr):
    """Variable reference"""
    meta: Meta
    name: Token

    def __str__(self) -> str:
        return self.name.value


@dataclass(frozen=True)
class Lambda(_Expr):
    """Function literal"""
    meta: Meta
    form_arg: Token
    body: _Expr

    def __str__(self) -> str:
        return f"λ{self.form_arg}.{self.body}"
