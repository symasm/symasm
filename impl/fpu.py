from .common import *

fpu_instructions_without_operands = {
    'fldz'    : 'fst.load(0)',
    'fld1'    : 'fst.load(1)',
    'fldpi'   : 'fst.load_pi()',
    'fldl2t'  : 'fst.load_log2(10)',
    'fldl2e'  : 'fst.load_log2(e)',
    'fldlg2'  : 'fst.load_lg(2)',
    'fldln2'  : 'fst.load_ln(2)',
    'fincstp' : 'fst.top++',
    'fdecstp' : 'fst.top--',
    'ftst'    : 'fpu.sw = fst0 <=> 0',
    'fcompp'  : 'fpu.sw = fst.pop() <=> fst1, fst.pop()',
    'fucompp' : 'fpu.sw = fst.pop() uo<=> fst1, fst.pop()',
    'frndint' : 'fst0 = round(fst0)',
    'fsqrt'   : 'fst0 = sqrt(fst0)',
    'fabs'    : 'fst0 = abs(fst0)',
    'fchs'    : 'fst0 = -fst0',
    'fsin'    : 'fst0 = sin(fst0)',
    'fcos'    : 'fst0 = cos(fst0)',
    'fsincos' : 'fst1, fst0 = sincos(fst0)',
    'fpatan'  : 'fst1 = atan2(fst1, fst0), fst.pop()',
    'fptan'   : 'fst0 = tan(fst0), fst.load(1)',
}

fpu_instructions_with_1_operand = {
    'fxch'   : 'fst0 ><',
    'fcom'   : 'fpu.sw = fst0 <=>',
    'fcomp'  : 'fpu.sw = fst.pop() <=>',
    'fucom'  : 'fpu.sw = fst0 uo<=>',
    'fucomp' : 'fpu.sw = fst.pop() uo<=>',
}

fpu_arithmetic_instructions = {
    'add' : '+',
    'sub' : '-',
    'mul' : '*',
    'div' : '/',
}

def fpu_operands(ops: list):
    for i in range(len(ops)):
        op = ops[i].lower()
        if op == 'st':
            ops[i] = 'fst0'
        elif len(op) == 5 and op[3].isdigit() and op.startswith('st(') and op[-1] == ')':
            ops[i] = 'fst' + op[3]

def fpu_to_symasm(mnem, ops: List[str], token, errors: List[Error] = None):
    fpu_operands(ops)

    def eoc(n): # expected operand count
        return coc(n, ops, token, errors)

    if mnem in fpu_instructions_without_operands:
        eoc(0)
        return fpu_instructions_without_operands[mnem]

    elif mnem in fpu_instructions_with_1_operand:
        eoc(1)
        return fpu_instructions_with_1_operand[mnem] + ' ' + ops[0]

    elif mnem[1:] in fpu_arithmetic_instructions:
        if len(ops) == 1:
            return 'fst0 ' + fpu_arithmetic_instructions[mnem[1:]] + '= ' + ops[0]
        eoc(2)
        return ops[0] + ' ' + fpu_arithmetic_instructions[mnem[1:]] + '= ' + ops[1]

    elif mnem[-1] == 'p' and mnem[1:-1] in fpu_arithmetic_instructions:
        eoc(2)
        assert(ops[1] == 'fst0')
        return ops[0] + ' ' + fpu_arithmetic_instructions[mnem[1:-1]] + '= fst.pop()'

    elif mnem[1] == 'i' and mnem[2:] in fpu_arithmetic_instructions:
        eoc(1)
        return 'fst0 ' + fpu_arithmetic_instructions[mnem[2:]] + '= read_int(' + ops[0] + ')'

    elif mnem in ('fsubr', 'fdivr'):
        if len(ops) == 1:
            return 'fst0 = ' + ops[0] + ' ' + ('-' if mnem == 'fsubr' else '/') + ' fst0'
        eoc(2)
        return ops[0] + ' = ' + ops[1] + ' ' + ('-' if mnem == 'fsubr' else '/') + ' ' + ops[0]

    elif mnem in ('fsubrp', 'fdivrp'):
        eoc(2)
        assert(ops[1] == 'fst0')
        return ops[0] + ' = fst.pop() ' + ('-' if mnem == 'fsubrp' else '/') + ' ' + ops[0]

    elif mnem in ('fisubr', 'fidivr'):
        eoc(1)
        return 'fst0 = read_int(' + ops[0] + ') ' + ('-' if mnem == 'fisubr' else '/') + ' fst0'

    elif mnem == 'fld':
        eoc(1)
        return 'fst.load(' + ops[0] + ')'
    elif mnem == 'fild':
        eoc(1)
        return 'fst.load_int(' + ops[0] + ')'
    elif mnem == 'fbld':
        eoc(1)
        return 'fst.load_bcd(' + ops[0] + ')'
    elif mnem == 'fst':
        eoc(1)
        return ops[0] + ' = fst0'
    elif mnem == 'fstp':
        eoc(1)
        if ops[0] == 'fst0':
            return 'fst.pop()'
        else:
            return ops[0] + ' = fst.pop()'
    elif mnem in ('fist', 'fistp', 'fisttp'):
        eoc(1)
        return ops[0] + ' = int(' + {'' : 'round(fst0)', 'p' : 'round(fst.pop())', 'tp' : 'fst.pop()'}[mnem[4:]] + ')'

    elif mnem.startswith('fcmov'):
        eoc(2)
        return ops[0] + ' = ' + ops[1] + ' if ' + {'b':'u<', 'e':'==', 'be':'u<=', 'u':'uo', 'nb':'!u<', 'ne':'!=', 'nbe':'!u<=', 'nu':'!uo'}[mnem[5:]]

    elif mnem in ('fstsw', 'fstcw'):
        eoc(1)
        return f'{ops[0]} = fpu.{mnem[3]}w'
    elif mnem == 'fldcw':
        eoc(1)
        return 'fpu.cw = ' + ops[0]

    return ''
