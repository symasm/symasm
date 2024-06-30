from .common import *
from .simd import *

# >[https://stackoverflow.com/questions/37056387/converting-from-intel-assembly-to-gas-att <- google:‘site:stackoverflow.com translate intel to at t syntax’]:‘
# The ‘GAS manual’[https://sourceware.org/binutils/docs/as/i386_002dMemory.html#i386_002dMemory] has a pretty good explanation of how to write memory references in AT&T syntax.’

# [http://staffwww.fullcoll.edu/aclifton/courses/cs241/syntax.html <- google:‘at&t syntax samples’]

# >[https://stackoverflow.com/questions/3902460/a-reference-for-att-syntax-assembly-floating-point-arithmetic <- google:‘at&t syntax fpu’]:‘The main things to note are:’

# >[https://stackoverflow.com/questions/34377711/which-2s-complement-integer-operations-can-be-used-without-zeroing-high-bits-in <- https://stackoverflow.com/questions/38303333/the-advantages-of-using-32bit-registers-instructions-in-x86-64]:‘
# ; int intfunc(int a, int b) { return a + b*4 + 3; }’

def fix_reg(reg):
    if reg.startswith(('r', 'R')) and \
       reg.endswith  (('d', 'D')) and reg[1:-1].isdigit():
        return reg[:-1] + trans_char_keep_case(reg[-1], 'd', 'i')
    else:
        return reg

def is_att_number(s):
    return s.startswith(('0x', '0X')) or s.isdigit()

def fix_number(imm):
    if imm.startswith(('0x', '0X')):
        return '0'*(not imm[2].isdigit()) + imm[2:] + 'h'
    return imm

att_suffixes = {'b':1, 'w':2, 'l':4, 'q':8, 't':10, 'o':16}

def translate_att_to_masm(mnem, source, operands, ops: list, token, errors: List[Error] = None):
    reg_size = 0
    mem_size = 0

    for toks in reversed(operands):
        r = ''

        if toks[0].string[0] == '$': # immediate/‘numeric constant’
            if len(toks) == 1:
                assert(is_att_number(toks[0].string[1:]))
                r = fix_number(toks[0].string[1:])
            else:
                assert(len(toks) == 3 and len(toks[0].string) == 1 and toks[1].string == '-' and is_att_number(toks[2].string))
                r = '-' + fix_number(toks[2].string)

        elif toks[0].string[0] == '%': # register
            assert(is_reg(toks[0].string[1:]) and len(toks) == 1)
            r = fix_reg(toks[0].string[1:])
            if is_cpu_gp_reg(r):
                sz = cpu_gp_reg_size(r)
                if reg_size == 0:
                    reg_size = sz
                else:
                    if reg_size != sz and not mnem.startswith(('movs', 'movz')):
                        if errors is not None:
                            errors.append(error_at_token(f'register size mismatch ({sz}, expected {reg_size})', toks[0]))
# (
        elif toks[-1].string == ')': # indirect
            for i, tok in enumerate(toks):
                if tok.string == '(': # )
                    disp = toks[:i]

                    i += 1
                    if toks[i].string == ',': # no base
                        assert(toks[i+1].string[0] == '%' and
                               toks[i+2].string == ',' and
                               toks[i+3].category == Token.Category.NUMERIC_LITERAL and
                                    i+4 == len(toks)-1)
                        r = fix_reg(toks[i+1].string[1:]) + '*' + fix_number(toks[i+3].string)
                    else:
                        base = toks[i].string
                        assert(base[0] == '%')
                        r = fix_reg(base[1:])
                        i += 1
                        if toks[i].string == ',':
                            i += 1
                            index = toks[i].string
                            assert(index[0] == '%')
                            r += '+' + fix_reg(index[1:])
                            i += 1
                            if toks[i].string == ',':
                                i += 1
                                scale = toks[i].string
                                assert(scale[0].isdigit())
                                r += '*' + scale
                                i += 1
                        assert(i + 1 == len(toks))

                    if len(disp) != 0:
                        if len(disp) == 1 and disp[0].category == Token.Category.NUMERIC_LITERAL:
                            if r != '':
                                r += '+'
                            r += fix_number(disp[0].string)
                        elif len(disp) == 2 and disp[1].category == Token.Category.NUMERIC_LITERAL and disp[0].string == '-':
                            r += '-' + fix_number(disp[1].string)
                        else:
                            r = source[disp[0].start:disp[-1].end] + '+' + r

                    assert(mem_size == 0)
                    mem_size = att_suffixes[mnem[-2] if mnem.startswith(('movs', 'movz')) else mnem[-1]]
                    r = size_keyword(mem_size) + '[' + r + ']'
                    break
            else:
                if errors is not None:
                    errors.append(Error('open paren is not found', toks[0].start, toks[-1].end))

        else:
            if errors is not None:
                errors.append(Error('unrecognized operand type', toks[0].start, toks[-1].end))

        ops.append(r)

    if mnem.startswith(('set', 'cmov')):
        if mnem.startswith('cmov') and mnem[-1] == 'l' and len(mnem) > 5:
            return mnem[:-1]
        return mnem

    if reg_size != 0:
        if mnem[-1] != {1:'b', 2:'w', 4:'l', 8:'q', 10:'t', 16:'o'}[reg_size]:
            if errors is not None:
                errors.append(Error('wrong instruction suffix', token.end - 1, token.end))
            return mnem
        if mnem.startswith(('movs', 'movz')):
            return mnem[:-2] + 'x'
        return mnem[:-1]

    if mem_size != 0:
        return mnem[:-1]

    return mnem
