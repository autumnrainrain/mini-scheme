"""环境：变量绑定表，front 指向当前层，parent 指向外层（词法作用域）。"""


class Env:
    def __init__(self, bindings=None, parent=None):
        self.bindings = dict(bindings) if bindings else {}
        self.parent = parent

    def lookup(self, name: str):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise NameError(f'未定义的标识符: {name}')

    def define(self, name: str, value):
        self.bindings[name] = value

    def set(self, name: str, value):
        if name in self.bindings:
            self.bindings[name] = value
        elif self.parent is not None:
            self.parent.set(name, value)
        else:
            raise NameError(f'未定义的标识符: {name}')
