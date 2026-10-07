"""语法分析：token 列表 -> 嵌套的表达式数据结构。

代码层面的表用 Python list 表示；带点语法的列表直接构造 Pair。
quote 求值时再把数据子树转成 Pair 链（见 evaluator.to_data）。
"""

from lexer import tokenize


class Symbol(str):
    """符号：继承 str 便于做字典键，但类型上与字符串字面量区分。"""


class Pair:
    """点对：列表的实际存储结构，(car . cdr)。"""

    __slots__ = ('car', 'cdr')

    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def __eq__(self, other):
        # 结构相等（equal? 使用）
        if isinstance(other, Pair):
            from prelude import _datum_equal
            return _datum_equal(self.car, other.car) and _datum_equal(self.cdr, other.cdr)
        return NotImplemented

    def __repr__(self):
        return f'Pair({self.car!r}, {self.cdr!r})'


def parse(text: str) -> list:
    """解析整个程序，返回顶层表达式列表。"""
    tokens = tokenize(text)
    pos = [0]
    exprs = []
    while pos[0] < len(tokens):
        exprs.append(_parse_one(tokens, pos))
    return exprs


def parse_expr(text: str):
    tokens = tokenize(text)
    return _parse_one(tokens, [0])


def _parse_one(tokens, pos):
    tok = tokens[pos[0]]
    if tok == "'":
        pos[0] += 1
        return [Symbol('quote'), _parse_one(tokens, pos)]
    if tok == '(':
        pos[0] += 1
        items = []
        cdr = _MISSING
        while pos[0] < len(tokens) and tokens[pos[0]] != ')':
            if tokens[pos[0]] == '.':
                pos[0] += 1
                cdr = _parse_one(tokens, pos)
            else:
                items.append(_parse_one(tokens, pos))
        if pos[0] >= len(tokens):
            raise SyntaxError('括号未闭合')
        pos[0] += 1
        if cdr is not _MISSING:  # 带点语法 -> 直接构造 Pair 链
            result = cdr
            for item in reversed(items):
                result = Pair(item, result)
            return result
        return items
    pos[0] += 1
    return _atom(tok)


_MISSING = object()


def _atom(tok: str):
    if tok == '#t':
        return True
    if tok == '#f':
        return False
    if tok.startswith('"'):
        return _decode_string(tok[1:-1])
    try:
        if '.' in tok or 'e' in tok.lower():
            return float(tok)
        return int(tok)
    except ValueError:
        return Symbol(tok)


def _decode_string(s: str) -> str:
    return (s.replace('\\n', '\n')
             .replace('\\t', '\t')
             .replace('\\"', '"')
             .replace('\\\\', '\\'))


def to_data(tree):
    """把解析出的 Python list 树转成 Pair 链（quote 求值时调用）。"""
    if isinstance(tree, Pair):
        tree.car = to_data(tree.car)
        tree.cdr = to_data(tree.cdr)
        return tree
    if isinstance(tree, list):
        result = []
        for item in reversed(tree):
            result = Pair(to_data(item), result)
        return result
    return tree
