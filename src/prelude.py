"""Builtin library loaded into the initial environment."""

import math
import operator

from env import Env
from parser import Symbol, Pair
from printer import BuiltinProc, Proc, to_string


def _trunc_div(a, b):
    """整数商，商向零截断（-7 / 2 = -3）。"""
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def _div(a, b):
    if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool) and not isinstance(b, bool):
        return _trunc_div(a, b)
    return a / b


def _arith(op, args, identity=None, unary=None):
    if len(args) == 0:
        if identity is None:
            raise TypeError('参数个数不足')
        return identity
    if len(args) == 1 and unary is not None:
        return unary(args[0])
    result = args[0]
    for a in args[1:]:
        result = op(result, a)
    return result


def _cmp(op, args):
    if len(args) < 2:
        raise TypeError('至少需要两个参数')
    return all(op(args[i], args[i + 1]) for i in range(len(args) - 1))


def _num_or_sym(a):
    """用于 = 等比较：支持数字与符号。"""
    return a


def _cmp_val(op, a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        # 布尔只与布尔比较
        if isinstance(a, bool) and isinstance(b, bool):
            return a == b
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return op(a, b)
    if isinstance(a, Symbol) and isinstance(b, Symbol):
        return op(str(a), str(b))
    return False


def _datum_equal(a, b) -> bool:
    """equal?：结构相等。"""
    # 避免 True == 1、'a == "a" 之类的意外
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, Symbol) or isinstance(b, Symbol):
        return isinstance(a, Symbol) and isinstance(b, Symbol) and str(a) == str(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, Pair) and isinstance(b, Pair):
        return _datum_equal(a.car, b.car) and _datum_equal(a.cdr, b.cdr)
    if isinstance(a, list) and isinstance(b, list):
        return a == b == []
    return False


def _datum_eq(a, b) -> bool:
    """eq?：符号/数字/布尔按值比较，复合数据按同一性。"""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return a == b
    if isinstance(a, Symbol) and isinstance(b, Symbol):
        return str(a) == str(b)
    if isinstance(a, list) and isinstance(b, list):  # 空表
        return a == [] and b == []
    if isinstance(a, Pair) or isinstance(b, Pair):
        return a is b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    return False


def truthy(v) -> bool:
    return v is not False


def build_list(xs):
    result = []
    for x in reversed(list(xs)):
        result = Pair(x, result)
    return result


def standard_env() -> Env:
    env = Env()

    def b(name, fn):
        env.define(name, BuiltinProc(name, fn))

    b('+', lambda *a: _arith(operator.add, a, identity=0))
    b('-', lambda *a: _arith(operator.sub, a, unary=lambda x: -x))
    b('*', lambda *a: _arith(operator.mul, a, identity=1))
    b('/', lambda *a: _arith(_div, a, unary=lambda x: 1.0 / x))
    b('modulo', lambda a, b: a % b)
    b('quotient', lambda a, b: _trunc_div(a, b))
    b('expt', lambda a, b: a ** b)
    b('abs', lambda a: abs(a))
    b('=', lambda *a: _cmp(lambda x, y: _cmp_val(operator.eq, x, y), a))
    b('<', lambda *a: _cmp(lambda x, y: _cmp_val(operator.lt, x, y), a))
    b('>', lambda *a: _cmp(lambda x, y: _cmp_val(operator.gt, x, y), a))
    b('<=', lambda *a: _cmp(lambda x, y: _cmp_val(operator.le, x, y), a))
    b('>=', lambda *a: _cmp(lambda x, y: _cmp_val(operator.ge, x, y), a))
    b('not', lambda a: not truthy(a))
    b('boolean?', lambda a: isinstance(a, bool))
    b('number?', lambda a: isinstance(a, (int, float)) and not isinstance(a, bool))
    b('string?', lambda a: isinstance(a, str) and not isinstance(a, Symbol))
    b('symbol?', lambda a: isinstance(a, Symbol))
    b('list?', lambda a: _is_proper_list(a))
    b('null?', lambda a: isinstance(a, list) and len(a) == 0)
    b('pair?', lambda a: isinstance(a, Pair))
    b('procedure?', lambda a: isinstance(a, Proc))
    b('zero?', lambda a: a == 0 and not isinstance(a, bool))
    b('even?', lambda a: isinstance(a, int) and not isinstance(a, bool) and a % 2 == 0)
    b('odd?', lambda a: isinstance(a, int) and not isinstance(a, bool) and a % 2 == 1)
    b('eq?', lambda a, b: _datum_eq(a, b))
    b('equal?', lambda a, b: _datum_equal(a, b))
    b('cons', lambda a, b: Pair(a, b))
    b('car', lambda a: a.car)
    b('cdr', lambda a: a.cdr)
    b('list', lambda *a: build_list(a))
    b('length', lambda a: _length(a))
    b('append', lambda *a: _append(a))
    b('display', lambda a: _display(a))
    b('newline', lambda: _newline())
    return env


def _is_proper_list(a) -> bool:
    x = a
    while isinstance(x, Pair):
        x = x.cdr
    return isinstance(x, list) and len(x) == 0


def _length(a) -> int:
    n = 0
    while isinstance(a, Pair):
        n += 1
        a = a.cdr
    return n


def _append(lists):
    result = []
    for lst in reversed(lists):
        # 把 lst 的元素依次 consd 到 result 前
        items = []
        x = lst
        while isinstance(x, Pair):
            items.append(x.car)
            x = x.cdr
        out = result
        for item in reversed(items):
            out = Pair(item, out)
        result = out
    return result


def _display(v):
    if isinstance(v, str) and not isinstance(v, Symbol):
        print(v, end='')
    else:
        print(to_string(v), end='')
    return None


def _newline():
    print()
    return None
