"""AST parser"""

from pathlib import Path

from lark import Lark, ast_utils

from . import nodes


grammar_path = Path(__file__).parent.parent / "grammar.lark"
common_opts = {
    "grammar_filename": grammar_path,
    "parser": "lalr",
    "propagate_positions": True,
}
parser = Lark.open(**common_opts)


_to_ast = ast_utils.create_transformer(nodes)


def parse_to_ast(src: str) -> nodes._Expr:
    """Parse baba-lang expression to AST"""
    return _to_ast.transform(parser.parse(src))
