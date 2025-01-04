"""AST node and visitor base class"""

from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .nodes import _Expr


# pylint: disable=too-few-public-methods
# pylint: disable=unnecessary-ellipsis


class ASTVisitor(ABC):
    """AST visitor interface"""

    @abstractmethod
    def visit(self, node: "_Expr") -> Any:
        """Visit a node

        Uses pattern matching to determine type of visited node and dispatch
        based on that"""
        ...
