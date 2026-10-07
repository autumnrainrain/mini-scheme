"""词法分析：程序文本 -> token 列表。"""


def tokenize(text: str) -> list:
    tokens = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == ';':  # 行注释
            while i < n and text[i] != '\n':
                i += 1
        elif ch in '()\'':
            tokens.append(ch)
            i += 1
        elif ch == '"':  # 字符串字面量
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == '\\':
                    j += 1
                j += 1
            if j >= n:
                raise SyntaxError('字符串未闭合')
            tokens.append(text[i:j + 1])
            i = j + 1
        else:  # 数字、符号、#t/#f 等
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()\'";':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens
