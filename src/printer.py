"""值类型与打印。"""

from parser import Symbol, Pair


class Proc:
    """过程的基类。"""
    name = '#<procedure>'


class BuiltinProc(Proc):
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn


class Lambda(Proc):
    def __init__(self, params, body, env, name='lambda'):
        self.params = params   # 参数名列表
        self.body = body       # 函数体表达式列表（隐式 begin）
        self.env = env         # 定义处环境（闭包）
        self.name = name


def to_string(value) -> str:
    """值 -> 文本（标准 printed representation）。"""
    if value is True:
        return '#t'
    if value is False:
        return '#f'
    if value is None:
        return ''
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, str):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Pair):
        return _pair_to_string(value)
    if isinstance(value, list):  # 空表 []
        if len(value) == 0:
            return '()'
        return '(' + ' '.join(to_string(v) for v in value) + ')'
    if isinstance(value, Proc):
        return f'#<procedure>'
    return str(value)


def _pair_to_string(p) -> str:
    parts = []
    while isinstance(p, Pair):
        parts.append(to_string(p.car))
        p = p.cdr
    if isinstance(p, list) and len(p) == 0:
        return '(' + ' '.join(parts) + ')'
    return '(' + ' '.join(parts) + ' . ' + to_string(p) + ')'
