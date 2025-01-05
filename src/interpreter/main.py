"""AST interpreter"""


from collections.abc import Callable, Sequence
from typing import Literal

from lark.tree import Meta

from bl_parser import nodes
from bl_parser.base import ASTVisitor

from .bl_types import (
    ExpressionResult, BLError, BLFunction, Call, Env, cast_to_instance,
    NotImplementedException,
)


class ASTInterpreter(ASTVisitor):
    """AST interpreter"""

    calls: list[Call]

    def __init__(self):
        self.calls = []

    def visit(self, node: nodes._Expr) -> ExpressionResult:
        """
        Visits a node in the abstract syntax tree (AST) and processes it.

        This method uses a trampoline to handle recursive calls in a loop to
        avoid Python's recursion limit. It processes the given node and
        returns the result.

        Args:
            node (nodes._Expr): The node to visit in the AST.

        Returns:
            ExpressionResult: The result of processing the node.
        """
        tramp = self._visit(node, None, lambda x: ("done", x))
        while True:
            match tramp:
                case "running", f, args:
                    tramp = f(*args)
                case "done", res:
                    return res

    def _visit(
        self, node: nodes._Expr, env: Env, then: Callable
    ) -> tuple[Literal["running", "done"], Callable, Sequence]:
        """
        Visits a node in the abstract syntax tree (AST) and processes it using
        trampolines.

        Arguments:
            node (nodes._Expr): The AST node to visit.
            env (Env): The environment in which the node is evaluated.
            then (Callable): The continuation function to call after
                             processing the node.
        Returns:
            tuple[Literal["running", "done"], Callable, Sequence]:
                A tuple containing:
                - A status string ("running" or "done").
                - A callable function to continue processing.
                - A sequence of arguments for the next call.
        """
        match node:
            case nodes.Paren(expr=expr):
                return "running", self._visit, (expr, env, then)
            case nodes.Call(meta=meta, callee=callee, arg=arg):
                return "running", self._visit, (
                    callee, env, lambda callee: (
                        self._visit(arg, env, lambda arg: (
                            self.apply(callee, arg, meta, then)
                        ))
                    )
                )
            case nodes.Var(meta=meta, name=name):
                return "running", then, (env.get_var(name, meta),)
            case nodes.Lambda(form_arg=form_arg, body=body):
                return "running", then, (BLFunction(
                    form_arg, body, env, str(node)
                ),)
        return "running", then, (BLError(cast_to_instance(
            NotImplementedException.new([], self, node.meta)
        ), node.meta),)

    def apply(
        self, callee: ExpressionResult, arg: ExpressionResult,
        meta: Meta | None, then: Callable,
    ) -> tuple[Literal["running", "done"], Callable, Sequence]:
        """
        Applies a function or callable to an argument in a
        continuation-passing style (CPS).

        Arguments:
            callee (ExpressionResult): The function or callable to be applied.
            arg (ExpressionResult): The argument to be passed to the function
                                    or callable.
            meta (Meta | None): Optional metadata for the application.
            then (Callable): The continuation function to be called after the
                             application.

        Returns:
            tuple[Literal["running", "done"], Callable, Sequence]:
                A tuple indicating the state of the application ("running" or
                "done"), the next function to be called, and a sequence of
                arguments for the next function.
        """
        match callee:
            case BLFunction(form_arg=form_arg, body=body, env=env):
                return "running", self._visit, (
                    body, env.new_var(form_arg, arg), then
                )
            case _:
                return callee.call_cps([arg], self, meta, then)
