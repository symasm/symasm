import sys
from enum import IntEnum
from typing import List, Dict

primary_operators = ['=', '+=', '-=', '*=', 'u*=', '/=', 'u/=', r'\=', '++', '--', '&=', '|=', '(+)=', '<<=', '>>=', 'u>>=', '(<<)=', '(>>)=', '><', '<=>', '<&>', 'f<=>', 'uo<=>', '.=']
primary_operators += ['|' + op + '|' for op in primary_operators]
primary_operators.sort(key = lambda x: len(x), reverse = True)
first_char_of_primary_operators = set() # Char
for op in primary_operators:
    first_char_of_primary_operators.add(op[0])
inner_binary_operators = {'/', '-'}
inner_unary_operators = {'-', '~'}
inner_operators = inner_binary_operators | inner_unary_operators

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

    def __init__(self, start, end, category, source):
        self.start = start
        self.end = end
        self.category = category
        self.string = source[start:end]

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

def error_at_token(errors: list, message, token):
    errors.append(Error(message, token.start, token.end))

def tokenize(source, errors: list):
    tokens: List[Token] = []

    def is_hexadecimal_digit(ch):
        return '0' <= ch <= '9' or 'A' <= ch <= 'F' or 'a' <= ch <= 'f'

    i = 0
    while i < len(source):
        ch = source[i]
        if ch in " \t":
            i += 1 # just skip whitespace characters
        elif ch == "\n":
            tokens.append(Token(i, i + 1, Token.Category.NEWLINE, source))
            i += 1
        elif ch == ';':
            comment_start = i
            i += 1
            while i < len(source) and source[i] != "\n":
                i += 1
            tokens.append(Token(comment_start, i, Token.Category.COMMENT, source))
            # if comments is not None:
            #     comments.append((comment_start, i))
        else:
            primary_operator = ''
            if ch in first_char_of_primary_operators:
                for op in primary_operators:
                    if source[i:i+len(op)] == op:
                        primary_operator = op
                        break

            lexem_start = i
            i += 1
            category: Token.Category

            if primary_operator != '':
                i = lexem_start + len(primary_operator)
                category = Token.Category.PRIMARY_OPERATOR

            elif ch in inner_operators:
                category = Token.Category.INNER_OPERATOR

            elif ch.isalpha() or ch in '_.': # this is NAME/IDENTIFIER
                while i < len(source):
                    ch = source[i]
                    if not (ch.isalpha() or ch in '_.@' or '0' <= ch <= '9'):
                        break
                    i += 1
                category = Token.Category.NAME

            elif '0' <= ch <= '9' or (ch == '.' and '0' <= source[i:i+1] <= '9'): # this is NUMERIC_LITERAL
                is_hex = False
                while i < len(source) and is_hexadecimal_digit(source[i]):
                    if not ('0' <= source[i] <= '9'):
                        is_hex = True
                    i += 1
                while i < len(source) and ('0' <= source[i] <= '9' or source[i] in "'.eE"):
                    if source[i] in 'eE':
                        if source[i+1:i+2] in '-+':
                            i += 1
                    i += 1
                if source[i:i+1].lower() in ('b', 'h'):
                    i += 1

                tokens.append(Token(lexem_start, i, Token.Category.NUMERIC_LITERAL, source))

                if is_hex and source[i-1].lower() != 'h':
                    error_at_token(errors, 'hexadecimal numbers must end with the `h` suffix', tokens[-1])

                continue

            elif ch in ':,[]()':
                category = Token.Category.DELIMITER

            else:
                errors.append(Error('unexpected character `' + ch + '`', lexem_start, lexem_start))

            tokens.append(Token(lexem_start, i, category, source))

    return tokens

class Lines:
    tokens: List[Token]
    tokeni = 0

    def __init__(self, tokens):
        self.tokens = tokens

    def next_line(self):
        line_start = self.tokeni

        while self.tokeni < len(self.tokens):
            if self.tokens[self.tokeni].category == Token.Category.COMMENT:
                line_end = self.tokeni
                self.tokeni += 1
                if self.tokeni < len(self.tokens) and self.tokens[self.tokeni].category == Token.Category.NEWLINE:
                    self.tokeni += 1
                return self.tokens[line_start:line_end]

            if self.tokens[self.tokeni].category == Token.Category.NEWLINE:
                self.tokeni += 1
                return self.tokens[line_start:self.tokeni-1]

            self.tokeni += 1

        return self.tokens[line_start:self.tokeni]

def detect_input_language(input_tokens):
    lines = Lines(input_tokens)

    while True:
        tokens = lines.next_line()
        if len(tokens) == 0:
            break

        if tokens[-1].string == ':': # it is a label - this syntax is valid in all languages
            continue

        if len(tokens) >= 2 and tokens[-1].category == Token.Category.NAME and tokens[-2].string == ':': # symasm branch instruction (conditional or unconditional)
            if not (len(tokens) > 4 and tokens[-3].string.lower() in ('fs', 'gs') and tokens[-4].string.lower() == 'ptr'): # support thread_local variables
                return 'symasm'

        for token in tokens:
            if token.category == Token.Category.PRIMARY_OPERATOR:
                return 'symasm'

    return 'masm'

cc_to_sym = {'a': 'u>', 'ae': 'u>=', 'b': 'u<', 'be': 'u<=', 'c': 'c',
'cxz': 'cx == 0', 'e': '==', 'ecxz': 'ecx == 0', 'g': '>', 'ge': '>=',
'l': '<', 'le': '<=', 'na': '!u>', 'nae': '!u>=', 'nb': '!u<', 'nbe':
'!u<=', 'nc': '!c', 'ne': '!=', 'ng': '!>', 'nge': '!>=', 'nl': '!<',
'nle': '!<=', 'no': '!o', 'np': '!p', 'ns': '!s', 'nz': '!z', 'o':
'o', 'p': 'p', 'rcxz': 'rcx == 0', 's': 's', 'z': 'z'} # generated by [helper_scripts/collect_all_condition_codes.py]

sym_to_cc: Dict[str, str] = {}
for cc, sym in cc_to_sym.items():
    assert(sym not in sym_to_cc)
    sym_to_cc[sym] = cc

cc_to_sym.update({'pe': 'p', 'po': '!p'}) # generated by [helper_scripts/collect_all_condition_codes.py]

def translate_masm_to_symasm(tokens, source):
    lines = Lines(tokens)
    next_line = lines.next_line()

    def op_str(toks):
        return source[toks[0].start : toks[-1].end]
    res: List[Tuple[List[Token], str]] = []

    while True:
        line = next_line
        if len(line) == 0:
            break
        next_line = lines.next_line()

        if line[-1].string == ':': # this is a label
            res.append((line, ''))
            continue

        mnem = line[0].string.lower()

        operands: List[List[Token]] = []
        last_operand: List[Token] = []
        for token in line[1:]:
            if token.string == ',':
                operands.append(last_operand)
                last_operand = []
            else:
                last_operand.append(token)
        operands.append(last_operand)

        if mnem == 'mov':
            assert(len(operands) == 2)
            res.append((line, op_str(operands[0]) + ' = ' + op_str(operands[1])))

        elif mnem == 'xor':
            assert(len(operands) == 2)
            op1 = op_str(operands[0])
            op2 = op_str(operands[1])
            if op1 == op2:
                res.append((line, op1 + ' = 0'))
            else:
                res.append((line, op1 + ' (+)= ' + op2))

        elif mnem == 'cmp':
            assert(len(operands) == 2)

            if len(next_line) > 0:
                next_mnem = next_line[0].string.lower()
                if next_mnem.startswith('j') and next_mnem[1:] in cc_to_sym:
                    res.append((line, op_str(operands[0]) + ' ' + cc_to_sym[next_mnem[1:]] + ' ' + op_str(operands[1]) + ' : ' + op_str(next_line[1:])))
                    res.append((next_line, '-'))
                    next_line = lines.next_line()
                    continue

            res.append((line, op_str(operands[0]) + ' <=> ' + op_str(operands[1])))

        elif mnem.startswith('set') and mnem[3:] in cc_to_sym:
            assert(len(operands) == 1)
            res.append((line, op_str(operands[0]) + ' = 1 if ' + cc_to_sym[mnem[3:]] + ' else 0'))

        elif mnem.startswith('cmov') and mnem[4:] in cc_to_sym:
            assert(len(operands) == 2)
            res.append((line, op_str(operands[0]) + ' = ' + op_str(operands[1]) + ' if ' + cc_to_sym[mnem[4:]]))

        elif mnem.startswith('j') and mnem[1:] in cc_to_sym:
            assert(len(operands) == 1)
            res.append((line, cc_to_sym[mnem[1:]] + ' : ' + op_str(operands[0])))

        else:
            res.append((line, ''))

    return res

if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print(
R'''Symbolic code assembly language translator

Usage: symasm [options] [INPUT_FILE]

Positional arguments:
  INPUT_FILE            input file (STDIN is assumed if no INPUT_FILE is given)

Options:
  -h, --help            show this help message and exit
  -f OUTPUT_FILE, --file OUTPUT_FILE
                        write output to OUTPUT_FILE (defaults to STDOUT)''')
        sys.exit(0)

    args_infile = sys.stdin
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] in ('-f', '--file'):
            i += 2
            continue
        if not sys.argv[i].startswith('-'):
            try:
                args_infile = open(sys.argv[i], 'r', encoding = 'utf-8-sig')
            except:
                sys.exit("Can't open file '" + sys.argv[i] + "'")
            break
        i += 1
    args_outfile = sys.stdout
    outfile_name: str
    try:
        if '-f' in sys.argv:
            outfile_name = sys.argv[sys.argv.index('-f')     + 1]
            args_outfile = open(outfile_name, 'w', encoding = 'utf-8', newline = "\n")
        elif '--file' in sys.argv:
            outfile_name = sys.argv[sys.argv.index('--file') + 1]
            args_outfile = open(outfile_name, 'w', encoding = 'utf-8', newline = "\n")
    except:
        sys.exit("Can't open file '" + outfile_name + "' for writing")

    infile_str: str
    try:
        infile_str = args_infile.read()
    except UnicodeDecodeError:
        sys.exit('Input is not a valid UTF-8!')

    mode = 'annotate'

    errors: List[Error] = []
    tokens = tokenize(infile_str, errors)

    lang = detect_input_language(tokens)

    if mode == 'translate':
        assert(lang == 'masm')
        for src_line, line in translate_masm_to_symasm(tokens, infile_str):
            if line != '-':
                print(line if line != '' else infile_str[src_line[0].start : src_line[-1].end])
    elif mode == 'annotate':
        assert(lang == 'masm')
        translation = translate_masm_to_symasm(tokens, infile_str)
        longest_src_line_len = max(len(infile_str[src_line[0].start : src_line[-1].end]) for src_line, line in translation)
        for src_line, line in translation:
            print(infile_str[src_line[0].start : src_line[-1].end].ljust(longest_src_line_len) + (' ; ' + line if line != '' else ''))
    else:
        sys.exit('Wrong mode: ' + mode)
