"""入口：读 .scm 文件（可多个，共享环境）或标准输入，逐个求值并打印结果。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import parse
from evaluator import evaluate
from prelude import standard_env
from printer import to_string


def run_text(text: str, env, out):
    for expr in parse(text):
        value = evaluate(expr, env)
        if value is not None:  # None 表示无值（如 display/newline/if 的假分支缺省）
            out.write(to_string(value) + '\n')


def main():
    env = standard_env()
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            with open(path, 'r', encoding='utf-8') as f:
                run_text(f.read(), env, sys.stdout)
    else:
        run_text(sys.stdin.read(), env, sys.stdout)


if __name__ == '__main__':
    main()
