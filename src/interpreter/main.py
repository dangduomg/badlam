"""AST interpreter"""


from dataclasses import dataclass
from collections.abc import Callable

from lark.tree import Meta

from bl_parser import nodes
from bl_parser.base import ASTVisitor

from . import bl_types
from .bl_types import (
    ExpressionResult, BLError, Call, Env, cast_to_instance,
    NotImplementedException,
)


@dataclass(frozen=True)
class ASTContinuation:
    """AST continuation"""
    node: nodes._Expr
    env: Env
    meta: Meta


class ASTInterpreter(ASTVisitor):
    """AST interpreter"""

    # pylint: disable=too-few-public-methods

    calls: list[Call]
    locals: Env

    def __init__(self):
        self.calls = []
        self.locals = Env(self)

    def visit(self, node: nodes._Expr) -> ExpressionResult:
        res = self._visit(node, lambda x: x)
        while callable(res):
            res = res()
        return res

    def _visit(
        self, node: nodes._Expr, then: Callable
    ) -> ExpressionResult:
        match node:
            case nodes.Paren(expr=expr):
                return lambda: self._visit(expr, then)
            case nodes.Call(meta=meta, callee=callee, arg=arg):
                return lambda: self._visit(
                    callee,
                    lambda callee: (
                        self._visit(
                            arg,
                            lambda arg: callee.call1_cps(arg, self, meta, then)
                        )
                    )
                )
            case nodes.Var(meta=meta, name=name):
                return lambda: then(self.locals.get_var(name, meta))
            case nodes.Lambda(form_arg=form_arg, body=body):
                env = self.locals.copy()
                return lambda: then(
                    bl_types.BLFunction(form_arg, body, env, str(node))
                )
        return lambda: then(BLError(cast_to_instance(
            NotImplementedException.new([], self, node.meta)
        ), node.meta))
