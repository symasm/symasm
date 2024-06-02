from enum import IntEnum
from typing import List

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

class Error:
    message: str
    pos: int
    end: int

    def __init__(self, message, start, end):
        self.message = message
        self.pos = start
        self.end = end

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
