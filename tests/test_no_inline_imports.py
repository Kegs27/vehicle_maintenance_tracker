import ast
import pathlib


def _has_inline_from_import(path: pathlib.Path, module: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                if isinstance(stmt, ast.ImportFrom) and stmt.module == module:
                    return True, node.name
    return False, None


def test_no_inline_data_ops_imports():
    path = pathlib.Path("main.py")
    hit, func_name = _has_inline_from_import(path, "data_operations")
    assert not hit, f"Inline 'from data_operations import' inside function {func_name}"

