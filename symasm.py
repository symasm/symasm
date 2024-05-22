import sys, re
from enum import IntEnum
from typing import List, Dict, Callable, NamedTuple

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
            if len(tokens) == 0 or tokens[-1].category == Token.Category.NEWLINE:
                tokens.append(Token(i, i, Token.Category.DELIMITER, source, len(tokens)))

            tokens.append(Token(i, i + 1, Token.Category.NEWLINE, source, len(tokens)))
            i += 1
        elif ch == ';':
            comment_start = i
            i += 1
            while i < len(source) and source[i] != "\n":
                i += 1

            if len(tokens) == 0 or tokens[-1].category == Token.Category.NEWLINE:
                tokens.append(Token(i, i, Token.Category.DELIMITER, source, len(tokens)))

            tokens.append(Token(comment_start, i, Token.Category.COMMENT, source, len(tokens)))
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

                tokens.append(Token(lexem_start, i, Token.Category.NUMERIC_LITERAL, source, len(tokens)))

                if is_hex and source[i-1].lower() != 'h':
                    error_at_token(errors, 'hexadecimal numbers must end with the `h` suffix', tokens[-1])

                continue

            elif ch in ':,[]()':
                category = Token.Category.DELIMITER

            else:
                errors.append(Error('unexpected character `' + ch + '`', lexem_start, lexem_start))

            tokens.append(Token(lexem_start, i, category, source, len(tokens)))

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

instructions_without_operands = {
    'cdq' : 'edx:eax = sx(eax)',
    'cqo' : 'rdx:rax = sx(rax)',
}

simple_instructions_with_2_operands = {
    'add' : '+',
    'sub' : '-',
    'and' : '&',
    'or'  : '|',
    'sal' : '<<',
    'shl' : '<<',
    'sar' : '>>',
    'shr' : 'u>>',
    'rol' : '(<<)',
    'ror' : '(>>)',
    'xchg': '><',
}

def translate_masm_to_symasm(tokens, source, errors: List[Error] = None):
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

        if len(line) == 1 and line[0].category == Token.Category.DELIMITER and line[0].string == '': # this is an empty line
            res.append((line, ''))
            continue

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
        if len(last_operand) > 0:
            operands.append(last_operand)

        def eoc(n): # expected operand count
            if len(operands) != n:
                if errors is not None:
                    error_at_token(errors, f'`{mnem}` instruction must have {n} operand(s)', line[0])

        def eoc_range(fr, thru):
            if len(operands) not in range(fr, thru + 1):
                if errors is not None:
                    error_at_token(errors, f'`{mnem}` instruction must have {fr} through {thru} operands', line[0])

        if mnem == 'mov':
            eoc(2)
            op2 = op_str(operands[1])
            res.append((line, op_str(operands[0]) + ' = ' + ('(0)' if op2 == '0' else op2)))

        elif mnem == 'xor':
            eoc(2)
            op1 = op_str(operands[0])
            op2 = op_str(operands[1])
            if op1 == op2:
                res.append((line, op1 + ' = 0'))
            else:
                res.append((line, op1 + ' (+)= ' + op2))

        elif mnem in simple_instructions_with_2_operands:
            eoc(2)
            res.append((line, op_str(operands[0]) + ' ' + simple_instructions_with_2_operands[mnem] + '= ' + op_str(operands[1])))

        elif mnem == 'jmp':
            eoc(1)
            res.append((line, ':' + op_str(operands[0])))

        elif mnem in ('inc', 'dec'):
            eoc(1)

            # >‘Do not use the INC or DEC instructions in x86 or x64 CodeGen’[https://github.com/dotnet/runtime/issues/7697 <- google:‘why compilers prefer sub over "dec"’]:‘
            # The partial flags stall only happens on older CPUs (P4) and Atom, for new Intel CPUs are able to rename each flag bit separately.’
            if mnem == 'dec' and len(next_line) > 0:
                next_mnem = next_line[0].string.lower()
                if next_mnem.startswith('j') and next_mnem[1:] in ('z', 'nz', 'e', 'ne'):
                    res.append((line, '--' + op_str(operands[0]) + (' !=' if next_mnem[1] == 'n' else ' ==') + ' 0 : ' + op_str(next_line[1:])))
                    res.append((next_line, '-'))
                    next_line = lines.next_line()
                    continue

            res.append((line, op_str(operands[0]) + ('++' if mnem == 'inc' else '--')))

        elif mnem == 'cmp':
            eoc(2)

            if len(next_line) > 0:
                next_mnem = next_line[0].string.lower()
                if next_mnem.startswith('j') and next_mnem[1:] in cc_to_sym:
                    res.append((line, op_str(operands[0]) + ' ' + cc_to_sym[next_mnem[1:]] + ' ' + op_str(operands[1]) + ' : ' + op_str(next_line[1:])))
                    res.append((next_line, '-'))
                    next_line = lines.next_line()
                    continue

            res.append((line, op_str(operands[0]) + ' <=> ' + op_str(operands[1])))

        elif mnem == 'test':
            eoc(2)
            op1 = op_str(operands[0])
            op2 = op_str(operands[1])

            if op1 == op2 and len(next_line) > 0:
                next_mnem = next_line[0].string.lower()
                if next_mnem.startswith('j') and next_mnem[1:] in ('z', 'nz', 'e', 'ne'):
                    res.append((line, op1 + (' !=' if next_mnem[1] == 'n' else ' ==') + ' 0 : ' + op_str(next_line[1:])))
                    res.append((next_line, '-'))
                    next_line = lines.next_line()
                    continue

            res.append((line, op1 + ' <&> ' + op2))

        elif mnem.startswith('set') and mnem[3:] in cc_to_sym:
            eoc(1)
            res.append((line, op_str(operands[0]) + ' = 1 if ' + cc_to_sym[mnem[3:]] + ' else 0'))

        elif mnem.startswith('cmov') and mnem[4:] in cc_to_sym:
            eoc(2)
            res.append((line, op_str(operands[0]) + ' = ' + op_str(operands[1]) + ' if ' + cc_to_sym[mnem[4:]]))

        elif mnem.startswith('j') and mnem[1:] in cc_to_sym:
            eoc(1)
            res.append((line, cc_to_sym[mnem[1:]] + ' : ' + op_str(operands[0])))

        elif mnem in instructions_without_operands:
            eoc(0)
            res.append((line, instructions_without_operands[mnem]))

        elif mnem in ('neg', 'not'):
            eoc(1)
            res.append((line, op_str(operands[0]) + ' = ' + ('-' if mnem == 'neg' else '~') + op_str(operands[0])))

        elif mnem == 'imul' and len(operands) > 1:
            eoc_range(1, 3)
            if len(operands) == 2:
                res.append((line, op_str(operands[0]) + ' *= ' + op_str(operands[1])))
            else:
                res.append((line, op_str(operands[0]) + ' = ' + op_str(operands[1]) + ' * ' + op_str(operands[2])))

        elif mnem in ('mul', 'imul', 'div', 'idiv'):
            eoc(1)
            op = op_str(operands[0])
            regp = op[0]
            u = 'u' * (mnem[0] != 'i')
            o = '*' if mnem.endswith('mul') else '/'
            res.append((line, f'{regp}dx:{regp}ax {u}{o}= {op}'))

        elif mnem in ('adc', 'sbb'):
            eoc(2)
            res.append((line, op_str(operands[0]) + ' ' + ('+' if mnem == 'adc' else '-') + '= ' + op_str(operands[1]) + ' + cf'))

        elif mnem in ('rcl', 'rcr'):
            eoc(2)
            res.append((line, 'cf:' + op_str(operands[0]) + ' (' + ('<<' if mnem == 'rcl' else '>>') + ')= ' + op_str(operands[1])))

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
                        write output to OUTPUT_FILE (defaults to STDOUT)
  --annotate            force operating mode to annotate
  --translate           force operating mode to translate''')
        sys.exit(0)

    # Options
    class Option(NamedTuple):
        name: str
        default_value: str
        description: str

    options_list = [
        Option('input_language', 'auto', 'Input language (masm, att, symasm)'),
        Option('mode',   'auto', 'Operating mode (annotate, translate)'),
        Option('indent', 'keep', 'Indent (tab, space, 4 spaces, 2 tabs, etc.)'),
        Option('case',   'keep', 'Case (upper, lower)'),
    ]
    options: Dict[str, str] = {}
    for option in options_list:
        options[option.name] = option.default_value

    # Read config
    config = ''
    try:
        config = open('symasm_config.txt', encoding = 'utf-8-sig').read()
    except:
        pass
    for line in config.split("\n"):
        line = line.strip()
        if line.startswith('//') or line == '':
            continue
        name, value = line.split('=', maxsplit = 1)
        name = name.strip()
        if not name in options:
            sys.exit('Unknown option: ' + name)
        options[name] = value.strip()

    # Update config
    new_config = ''
    for option in options_list:
        new_config += '// ' + option.description + "\n"
        new_config += '// Default value: ' + option.default_value + "\n"
        new_config += option.name + ' = ' + options[option.name] + "\n"
        if option is not options_list[-1]:
            new_config += "\n"
    if new_config != config:
        open('symasm_config.txt', 'w', encoding = 'utf-8').write(new_config)

    # Parse command line arguments
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
            #break
        if sys.argv[i] == '--annotate':
            options['mode'] = 'annotate'
        if sys.argv[i] == '--translate':
            options['mode'] = 'translate'
        i += 1
    out = sys.stdout
    outfile_name: str
    try:
        if '-f' in sys.argv:
            outfile_name = sys.argv[sys.argv.index('-f')     + 1]
            out = open(outfile_name, 'w', encoding = 'utf-8', newline = "\n")
        elif '--file' in sys.argv:
            outfile_name = sys.argv[sys.argv.index('--file') + 1]
            out = open(outfile_name, 'w', encoding = 'utf-8', newline = "\n")
    except:
        sys.exit("Can't open file '" + outfile_name + "' for writing")

    # Read and process input
    infile_str: str
    try:
        infile_str = args_infile.read()
    except UnicodeDecodeError:
        sys.exit('Input is not a valid UTF-8!')

    mode   = options['mode']
    indent = options['indent']

    indent_f: Callable[[List[Token]], str]
    if indent == 'keep':
        def indent_keep(line):
            i = line[0].start
            while i >= 0 and infile_str[i] != "\n":
                i -= 1
            return infile_str[i+1 : line[0].start]
        indent_f = indent_keep
    else:
        def indent_fixed(line):
            if line[-1].string == ':': # labels are not indented
                return ''
            return indent
        indent_f = indent_fixed

        if indent == 'none':
            indent = ''
        elif indent == 'tab':
            indent = "\t"
        elif indent == 'space':
            indent = ' '
        elif indent.endswith(' tabs'):
            indent = "\t" * int(indent.split(' ')[0])
        elif indent.endswith(' spaces'):
            indent = ' ' * int(indent.split(' ')[0])
        else:
            sys.exit('Wrong indent: ' + indent)

    errors: List[Error] = []
    tokens = tokenize(infile_str, errors)

    def check_errors():
        if len(errors) > 0:
            for e in errors:
                next_line_pos = infile_str.find("\n", e.pos)
                if next_line_pos == -1:
                    next_line_pos = len(infile_str)
                prev_line_pos = infile_str.rfind("\n", 0, e.pos) + 1
                sys.stderr.write('Error: ' + e.message + "\n in line " + str(infile_str[:e.pos].count("\n") + 1) + "\n"
                                + infile_str[prev_line_pos:next_line_pos] + "\n"
                                + re.sub(r'[^\t]', ' ', infile_str[prev_line_pos:e.pos]) + '^'*max(1, e.end - e.pos) + "\n")
            sys.exit(len(errors))

    lang = options['input_language']
    if lang == 'auto':
        lang = detect_input_language(tokens)
    if mode == 'auto':
        mode = 'annotate' if lang != 'symasm' else 'translate'

    def line_str(src_line):
        line_start = tokens[src_line[ 0].index - 1].end if src_line[ 0].index > 0 else 0
        line_end   = tokens[src_line[-1].index + 1].end if src_line[-1].index + 1 < len(tokens) and tokens[src_line[-1].index + 1].category == Token.Category.COMMENT else src_line[-1].end
        return infile_str[line_start : line_end]

    def get_comment(src_line):
        return ' ' + tokens[src_line[-1].index + 1].string if src_line[-1].index + 1 < len(tokens) and tokens[src_line[-1].index + 1].category == Token.Category.COMMENT else ''

    if mode == 'translate':
        assert(lang == 'masm')
        translation = translate_masm_to_symasm(tokens, infile_str, errors)
        check_errors()
        for i in range(len(translation)):
            src_line, line = translation[i]
            if line == '-':
                continue

            if (src_line[-1].string == ':'
                    or (len(src_line) == 1 and src_line[0].category == Token.Category.DELIMITER and src_line[0].string == '')):
                out.write(line_str(src_line) + "\n")
                continue

            comment:str = get_comment(src_line)
            if i + 1 < len(translation) and translation[i + 1][1] == '-':
                comment += get_comment(translation[i + 1][0])
            out.write(indent_f(src_line) + (line if line != '' else infile_str[src_line[0].start : src_line[-1].end]) + comment + "\n")

    elif mode == 'annotate':
        assert(lang == 'masm')
        translation = translate_masm_to_symasm(tokens, infile_str, errors)
        check_errors()
        longest_src_line_len = max((src_line[-1].end - src_line[0].start for src_line, line in translation if src_line[-1].string != ':'), default = 0)
        for src_line, line in translation:
            if (src_line[-1].string == ':' # labels do not need to be justified (this is for labels with comments)
                    or (len(src_line) == 1 and src_line[0].category == Token.Category.DELIMITER and src_line[0].string == '')):
                out.write(line_str(src_line) + "\n")
                continue
            comment = get_comment(src_line)
            out.write(indent_f(src_line) + (infile_str[src_line[0].start : src_line[-1].end].ljust(longest_src_line_len) + (' ; ' + line + comment if line != '' else '  ' + comment if comment != '' else '')).rstrip(' ') + "\n")

    else:
        sys.exit('Wrong mode: ' + mode)
