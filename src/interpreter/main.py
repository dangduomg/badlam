"""AST interpreter"""


from collections.abc import Callable, Sequence
from typing import Literal

from lark.tree import Meta

from bl_parser import nodes
from bl_parser.base import ASTVisitor

from . import bl_types
from .bl_types import (
    ExpressionResult, BLError, Call, Env, cast_to_instance,
    NotImplementedException,
)


class ASTInterpreter(ASTVisitor):
    """AST interpreter"""

    # pylint: disable=too-few-public-methods

    calls: list[Call]
    locals: Env

    def __init__(self):
        self.calls = []
        self.locals = Env(self)

    def visit(self, node: nodes._Expr) -> ExpressionResult:
        tramp = self._visit(node, self.locals, lambda x: ("done", x))
        while True:
            match tramp:
                case "running", f, args:
                    tramp = f(*args)
                case "done", res:
                    return res

    def _visit(
        self, node: nodes._Expr, env: Env, then: Callable
    ) -> tuple[Literal["running", "done"], Callable, Sequence]:
        """Uses trampolines"""
        match node:
            case nodes.Paren(expr=expr):
                return "running", self._visit, (expr, env, then)
            case nodes.Call(meta=meta, callee=callee, arg=arg):
                return "running", self._visit, (callee, env, lambda callee: (
                    self._visit(
                        arg,
                        env,
                        lambda arg: (
                            self.apply(callee, arg, meta, then)
                        )
                    )
                ))
            case nodes.Var(meta=meta, name=name):
                return "running", then, (env.get_var(name, meta),)
            case nodes.Lambda(form_arg=form_arg, body=body):
                return "running", then, (bl_types.BLFunction(
                    form_arg, body, env, str(node)
                ),)
        return "running", then, (BLError(cast_to_instance(
            NotImplementedException.new([], self, node.meta)
        ), node.meta),)

    def apply(
        self, callee: ExpressionResult, arg: ExpressionResult,
        meta: Meta | None, then: Callable,
    ) -> ExpressionResult:
        """Apply a function"""
        match callee:
            case bl_types.BLFunction(form_arg=form_arg, body=body, env=env):
                return "running", self._visit, (
                    body, env.new_var(form_arg, arg), then
                )
            case _:
                return callee.call_cps([arg], self, meta, then)
