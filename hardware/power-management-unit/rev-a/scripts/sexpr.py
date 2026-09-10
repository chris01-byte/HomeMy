"""Small lossless-enough KiCad s-expression reader used by the CAD build.

No dependency on an installed KiCad library is needed to inspect source files.
Quoted atoms retain their quoted form so that symbols can be embedded unchanged.
"""
import re


TOKEN = re.compile(r'\s+|;[^\n]*|\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


def parse(text):
    stack = [[]]
    for m in TOKEN.finditer(text):
        token = m.group()
        if token.isspace() or token.startswith(';'):
            continue
        if token == '(':
            item = []
            stack[-1].append(item)
            stack.append(item)
        elif token == ')':
            if len(stack) == 1:
                raise ValueError('Unbalanced closing parenthesis')
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError('Not one balanced s-expression')
    return stack[0][0]


def dump(value):
    if isinstance(value, list):
        return '(' + ' '.join(dump(v) for v in value) + ')'
    return str(value)


def children(item, name):
    return [v for v in item if isinstance(v, list) and v and v[0] == name]


def child(item, name):
    return next(iter(children(item, name)), None)


def unquote(atom):
    import json
    return json.loads(atom) if atom.startswith('"') else atom
