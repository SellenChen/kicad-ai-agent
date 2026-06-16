from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


TOKEN_RE = re.compile(r'''\s*(?:(;[^\n\r]*)|([()])|("(?:(?:\\.)|[^"\\])*")|([^\s()";]+))''')


@dataclass
class Atom:
    value: str
    quoted: bool = False


Node = list["Node | Atom"]


def tokenize(text: str) -> list[Atom | str]:
    tokens: list[Atom | str] = []
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        match = TOKEN_RE.match(text, pos)
        if not match:
            raise ValueError(f"Unexpected character at offset {pos}")
        pos = match.end()
        comment, paren, quoted, bare = match.groups()
        if comment:
            continue
        if paren:
            tokens.append(paren)
        elif quoted is not None:
            tokens.append(Atom(bytes(quoted[1:-1], "utf-8").decode("unicode_escape"), True))
        elif bare is not None:
            tokens.append(Atom(bare, False))
    return tokens


def parse(text: str) -> Node:
    stack: list[Node] = []
    root: Node | None = None
    for token in tokenize(text):
        if token == "(":
            node: Node = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
            if root is None:
                root = node
        elif token == ")":
            if not stack:
                raise ValueError("Unexpected closing parenthesis")
            stack.pop()
        else:
            if not stack:
                raise ValueError("Atom outside list")
            stack[-1].append(token)
    if stack:
        raise ValueError("Unclosed parenthesis")
    if root is None:
        raise ValueError("Empty S-expression")
    return root


def atom_text(item: Node | Atom) -> str | None:
    return item.value if isinstance(item, Atom) else None


def head(node: Node) -> str | None:
    return atom_text(node[0]) if node else None


def walk(node: Node) -> Iterator[Node]:
    yield node
    for item in node:
        if isinstance(item, list):
            yield from walk(item)


def properties(symbol: Node) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in symbol:
        if isinstance(item, list) and head(item) == "property" and len(item) >= 3:
            name = atom_text(item[1])
            value = atom_text(item[2])
            if name is not None and value is not None:
                result[name] = value
    return result
