from enum import IntEnum
from typing import List, NamedTuple

class Token:
    class Category(IntEnum): # why ‘Category’: >[https://docs.python.org/3/reference/lexical_analysis.html#other-tokens]:‘the following categories of tokens exist’
        NAME = 0 # or IDENTIFIER
        PRIMARY_OPERATOR = 1
        INNER_OPERATOR = 2
        CONDITIONAL_OPERATOR = 3
        DELIMITER = 4
        NUMERIC_LITERAL = 5
        NEWLINE = 6
        COMMENT = 7

    start: int
    end: int
    category: Category
    string: str
    index: int

    def __init__(self, start, end, category, source, index):
        self.start = start
        self.end = end
        self.category = category
        self.string = source[start:end]
        self.index = index

    def __str__(self):
        return 'Token(' + str(self.category) + ', "' + self.string + '")'

class Error(NamedTuple):
    message: str
    pos: int
    end: int

    def __ne__(self, other):
        return not (self.message == other.message and self.pos == other.pos and self.end == other.end)

    def __str__(self):
        return f"Error: {self.message}\nPos: {self.pos}\nEnd: {self.end}"

def error_at_token(message, token):
    return Error(message, token.start, token.end)

def coc(n, ops, token, errors: List[Error] = None): # check operand count
    if len(ops) != n:
        if errors is not None:
            errors.append(error_at_token(f'`{token.string}` instruction must have {n} operand(s)', token))
        return False
    return True

def asm_number(num):
    num = num.lower()
    if num[-1] == 'h':
        return int(num[:-1], 16)
    if num[-1] == 'b':
        return int(num[:-1], 2)
    return int(num)

cpu_gp_regs_1b = {'al', 'bl', 'cl', 'dl', 'ah', 'bh', 'ch', 'dh'}
cpu_gp_regs_2b = {'ax', 'bx', 'cx', 'dx', 'si', 'di', 'sp', 'bp'}
cpu_gp_regs_suffixes = {'b' : 1, 'w' : 2, 'i' : 4}

def cpu_gp_reg_size(reg):
    reg = reg.lower()

    if len(reg) == 2:
        if reg in cpu_gp_regs_1b:
            return 1
        if reg in cpu_gp_regs_2b:
            return 2
        if reg[0] == 'r' and reg[1].isdigit():
            return 8
        return 0

    if len(reg) == 3:
        if reg[0] == 'e':
            return 4 if reg[1:] in cpu_gp_regs_2b else 0
        if reg[-1] == 'l':
            return 1 if reg[:-1] in ('si', 'di', 'sp', 'bp') else 0

    if reg[0] == 'r':
        if reg[1:] in cpu_gp_regs_2b:
            return 8
        if reg[-1].isalpha():
            if not reg[1:-1].isdigit():
                return 0
            return cpu_gp_regs_suffixes.get(reg[-1], 0)
        return 8 if reg[1:].isdigit() else 0

    return 0

Char = str
def trans_char_keep_case(ch, fr: Char, to: Char) -> Char:
    return chr(ord(ch) + (ord(to) - ord(fr)))

def cpu_gp_reg_4b_to_2b(reg):
    if reg[0] in 'eE':
        assert(len(reg) == 3)
        return reg[1:]

    assert(reg[0] in 'rR' and reg[-1] in 'iI' and reg[1:-1].isdigit())
    return reg[:-1] + trans_char_keep_case(reg[-1], 'i', 'w')

def cpu_gp_reg_4b_to_1b(reg):
    if reg[0] in 'eE':
        assert(len(reg) == 3)
        return (reg[1] if reg[2] in 'xX' else reg[1:3]) + trans_char_keep_case(reg[0], 'e', 'l')

    assert(reg[0] in 'rR' and reg[-1] in 'iI' and reg[1:-1].isdigit())
    return reg[:-1] + trans_char_keep_case(reg[-1], 'i', 'b')

def is_cpu_gp_reg(reg):
    return cpu_gp_reg_size(reg) != 0

def size_keyword(bytes):
    assert(bytes >= 1)
    return 'byte' if bytes == 1 else f'{bytes}bytes'
