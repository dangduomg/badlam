"""AST interpreter"""


from dataclasses import dataclass

from lark.tree import Meta

from bl_parser import nodes
from bl_parser.base import ASTVisitor

from . import bl_types
from .bl_types import (
    Result, ExpressionResult, BLError, Value, Call, Env, cast_to_instance,
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
    locals: Env | None = None

    def __init__(self):
        self.calls = []
        self.locals = Env(self)

    def visit(self, node: nodes._Expr) -> Result:
        return self._visit(node)

    def _visit(self, node: nodes._Expr) -> ExpressionResult:
        match node:
            case nodes.Paren(expr=expr):
                return self._visit(expr)
            case nodes.Call(meta=meta, callee=callee, arg=arg):
                arg_visited = self._visit(arg)
                if not isinstance(arg_visited, Value):
                    return arg_visited
                callee = self._visit(callee)
                return callee.call([arg_visited], self, meta)
            case nodes.Var(meta=meta, name=name):
                return self.locals.get_var(name, meta)
            case nodes.Lambda(form_arg=form_arg, body=body):
                env = None if self.locals is None else self.locals.copy()
                return bl_types.BLFunction(form_arg, body, env, str(node))
        return BLError(cast_to_instance(
            NotImplementedException.new([], self, node.meta)
        ), node.meta)
