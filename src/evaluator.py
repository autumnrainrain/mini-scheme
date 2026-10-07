"""求值器：evaluate 与 apply 互相递归。"""

from env import Env
from parser import Symbol, Pair, to_data
from printer import BuiltinProc, Lambda


def evaluate(expr, env: Env):
    # 自求值：数字、布尔、字符串字面量
    if isinstance(expr, bool) or isinstance(expr, (int, float)):
        return expr
    if isinstance(expr, str) and not isinstance(expr, Symbol):
        return expr
    if expr is None:
        return None
    # 符号 -> 查环境
    if isinstance(expr, Symbol):
        return env.lookup(str(expr))
    # 空表与点对数据（带点字面量已直接构造为 Pair）
    if isinstance(expr, Pair) or (isinstance(expr, list) and len(expr) == 0):
        return expr
    if not isinstance(expr, list):
        return expr

    head = expr[0]
    if isinstance(head, Symbol):
        name = str(head)
        if name == 'quote':
            return to_data(expr[1])
        if name == 'if':
            _, test, then, *rest = expr
            if _truthy(evaluate(test, env)):
                return evaluate(then, env)
            if rest:
                return evaluate(rest[0], env)
            return None
        if name == 'cond':
            return _eval_cond(expr[1:], env)
        if name == 'and':
            result = True
            for e in expr[1:]:
                result = evaluate(e, env)
                if not _truthy(result):
                    return result
            return result
        if name == 'or':
            for e in expr[1:]:
                result = evaluate(e, env)
                if _truthy(result):
                    return result
            return False
        if name == 'begin':
            return _eval_body(expr[1:], env)
        if name == 'define':
            return _eval_define(expr, env)
        if name == 'lambda':
            params_raw = expr[1]
            if isinstance(params_raw, Symbol):
                params = [str(params_raw)]
            else:
                params = [str(p) for p in params_raw]
            return Lambda(params, expr[2:], env)
        if name == 'let':
            return _eval_let(expr, env)

    # 函数调用：先求值操作符与实参，再 apply
    proc = evaluate(head, env)
    args = [evaluate(a, env) for a in expr[1:]]
    return apply(proc, args)


def apply(proc, args):
    if isinstance(proc, BuiltinProc):
        return proc.fn(*args)
    if isinstance(proc, Lambda):
        if len(args) != len(proc.params):
            raise TypeError(f'{proc.name}: 需要 {len(proc.params)} 个参数，得到 {len(args)} 个')
        new_env = Env(dict(zip(proc.params, args)), parent=proc.env)
        return _eval_body(proc.body, new_env)
    raise TypeError(f'不可调用的对象: {proc!r}')


def _truthy(v) -> bool:
    """只有 #f 为假。"""
    return v is not False


def _eval_cond(clauses, env):
    for clause in clauses:
        items = _pair_items(clause) if isinstance(clause, Pair) else list(clause)
        test_expr, rest = items[0], items[1:]
        if isinstance(test_expr, Symbol) and str(test_expr) == 'else':
            return _eval_body_items(rest, env)
        value = evaluate(test_expr, env)
        if _truthy(value):
            if len(rest) == 0:
                return value
            return _eval_body_items(rest, env)
    return None


def _pair_items(p):
    items = []
    while isinstance(p, Pair):
        items.append(p.car)
        p = p.cdr
    return items


def _eval_body_items(items, env):
    result = None
    for e in items:
        result = evaluate(e, env)
    return result


def _eval_body(exprs, env):
    result = None
    for e in exprs:
        result = evaluate(e, env)
    return result


def _eval_define(expr, env):
    if isinstance(expr[1], list):
        # (define (f x y) body ...)
        name = str(expr[1][0])
        params = [str(p) for p in expr[1][1:]]
        env.define(name, Lambda(params, expr[2:], env, name=name))
        return Symbol(name)
    name = str(expr[1])
    value = evaluate(expr[2], env)
    env.define(name, value)
    return Symbol(name)


def _eval_let(expr, env):
    # 并行绑定：所有右部表达式都先在外层环境求值
    pairs = expr[1]
    new_env = Env({}, parent=env)
    values = []
    names = []
    for binding in pairs:
        if isinstance(binding, Pair):
            items = _pair_items(binding)
        else:
            items = binding
        names.append(str(items[0]))
        values.append(evaluate(items[1], env))
    for n, v in zip(names, values):
        new_env.define(n, v)
    return _eval_body(expr[2:], new_env)
