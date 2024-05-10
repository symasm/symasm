import sys
from enum import IntEnum
from typing import List

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
        DELIMITER = 3
        NUMERIC_LITERAL = 4
        NEWLINE = 5

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
            while i < len(source) and source[i] not in "\n":
                i += 1
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
                    if not (ch.isalpha() or ch in '_.' or '0' <= ch <= '9'):
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

def detect_input_language(source):
    for line in source.split("\n"):
        line = line.split(';', maxsplit = 1)[0].strip(' ')

        if line.endswith(':'): # it is a label - this syntax is valid in all languages
            continue

        errors: List[Error] = []
        tokens = tokenize(line, errors)

        if len(tokens) >= 2 and tokens[-1].category == Token.Category.NAME and tokens[-2].string == ':': # symasm branch instruction (conditional or unconditional)
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

sym_to_cc = {}
for cc, sym in cc_to_sym.items():
    assert(sym not in sym_to_cc)
    sym_to_cc[sym] = cc

cc_to_sym.update({'pe': 'p', 'po': '!p'}) # generated by [helper_scripts/collect_all_condition_codes.py]


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

    lang = detect_input_language(infile_str)
    print(lang)
    errors: List[Error] = []
    for token in tokenize(infile_str, errors):
        print(token)
