from .common import *

simd_simple_float_instructions = {
    'add' : '+',
    'sub' : '-',
    'mul' : '*',
    'div' : '/',
}

simd_simple_int_instructions = {
    'add' : '+',
    'sub' : '-',
    'mull': '*',
}

simd_int_types = {
    'b' : 'b',
    'w' : 'w',
    'd' : 'i',
    'q' : 'l',
}

simd_simple_int_bitwise_instructions = {
    'xor' : '(+)',
    'or'  : '|',
    'and' : '&',
}

simd_simple_register_instructions = {
    'movhlps' : '<xmm0>s[0:2] |=| xmm1s[2:4]',
    'movlhps' : '<xmm0>s[2:4] |=| xmm1s[0:2]',
    'unpckhpd': '<xmm0>d |=| <xmm0>d[1], xmm1d[1]',
    'unpcklpd': '<xmm0>d[1] = xmm1d[0]',
}

simd_move_instructions = {
    'movaps' : 'xmm0s |=a| <src>',
    'movups' : 'xmm0s |=u| <src>',
    'movapd' : 'xmm0d |=a| <src>',
    'movupd' : 'xmm0d |=u| <src>',
    'movdqa' : 'xmm0l |=a| <src>',
    'movdqu' : 'xmm0l |=u| <src>',
    'movss'  : 'xmm0s = <src>',
    'movsd'  : 'xmm0d = <src>',
    'movlps' : 'xmm0s[0:2] |=| <src>',
    'movhps' : 'xmm0s[2:4] |=| <src>',
    'movlpd' : 'xmm0d[0] = <src>',
    'movhpd' : 'xmm0d[1] = <src>',
}

simd_cmp_float = {
    'eq' : '==',
    'lt' : '<',
    'le' : '<=',
    'unord' : '',
    'neq' : '!=',
    'nlt' : '!<',
    'nle' : '!<=',
    'ord' : '',
}

def is_simd_reg(operand):
    oplow = operand.lower()
    return oplow[0] in 'xyz' and oplow[1:3] == 'mm' and oplow[3:].isdigit()

def simd_reg_mem(operand: str, ty):
    return operand + ty * is_simd_reg(operand)

def simd_to_symasm(mnem, ops: List[str], token, errors: List[Error] = None):
    if len(mnem) < 3:
        return ''

    def eoc(n): # expected operand count
        if not coc(n, ops, token, errors):
            return False
        if not ops[0].lower().startswith('xmm'):
            if errors is not None:
                errors.append(error_at_token(f'the first operand of the `{token.string}` instruction must be a register', token))
            return False
        return True

    if mnem[-1] in 'sd' and mnem[:-1] == 'xorp':
        if eoc(2):
            if ops[0] == ops[1]:
                return ops[0] + mnem[-1] + ' |=| 0'
            else:
                return ops[0] + mnem[-1] + ' |(+)=| ' + ops[1]

    elif mnem in simd_move_instructions:
        if eoc(2):
            return simd_move_instructions[mnem].replace('xmm0', ops[0]).replace('<src>', ops[1])

    elif mnem in ('movq', 'movd'):
        if coc(2, ops, token, errors):
            if not ops[1].lower().startswith('xmm'):
                if errors is not None:
                    errors.append(error_at_token(f'the second operand of the `{token.string}` instruction must be a xmm register', token))
                return ''
            return ops[0] + ' = ' + ops[1] + ('l' if mnem == 'movq' else 'i')

    elif mnem[-1] in 'sd' and mnem[-2] in 'sp':
        if mnem[:3] in simd_simple_float_instructions:
            if eoc(2):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' ' + p + simd_simple_float_instructions[mnem[:3]] + '=' + p + ' ' + ops[1]
        elif mnem in simd_simple_register_instructions:
            if eoc(2):
                if not ops[1].lower().startswith('xmm'):
                    if errors is not None:
                        errors.append(error_at_token(f'all operands of the `{token.string}` instruction must be registers', token))
                    return ''
                return simd_simple_register_instructions[mnem].replace('xmm1', ops[1]).replace('<xmm0>', ops[0])
        elif mnem[:-1] == 'shufp':
            if eoc(3):
                b = asm_number(ops[2])
                def i(n):
                    return (b >> (n * 2)) & 0b11
                if mnem == 'shufps':
                    if ops[0] == ops[1]:
                        return ops[0] + 's |=| ' + ops[0] + f's[{i(0)},{i(1)},{i(2)},{i(3)}]'
                    else:
                        return ops[0] + 's |=| ' + f'{ops[0]}s[{i(0)},{i(1)}], {ops[1]}s[{i(2)},{i(3)}]'
                else:
                    assert(mnem == 'shufpd')
                    if ops[0] == ops[1]:
                        return ops[0] + 'd |=| ' + ops[0] + f'd[{i(0)},{i(1)}]'
                    else:
                        return ops[0] + 'd |=| ' + f'{ops[0]}d[{i(0)}], {ops[1]}d[{i(1)}]'
        elif mnem.startswith('cmp') and mnem[3:-2] in simd_cmp_float:
            if eoc(2):
                csym = simd_cmp_float[mnem[3:-2]]
                op = '.' * (csym == '') + '='
                if mnem[-2] == 'p':
                    op = '|' + op + '|'
                right = simd_reg_mem(ops[1], mnem[-1])
                right = csym + ' ' + right if csym != '' else mnem[3:-2] + '(' + right + ')'
                return ops[0] + mnem[-1] + ' ' + op + ' ' + right

    elif mnem[0] == 'p':
        if mnem[-1] in simd_int_types and mnem[1:-1] in simd_simple_int_instructions:
            if eoc(2):
                return ops[0] + simd_int_types[mnem[-1]] + ' |' + simd_simple_int_instructions[mnem[1:-1]] + '=| ' + ops[1]
        elif mnem[1:] in simd_simple_int_bitwise_instructions:
            if eoc(2):
                return ops[0] + ' |' + simd_simple_int_bitwise_instructions[mnem[1:]] + '=| ' + ops[1]
        elif mnem == 'pandn':
            if eoc(2):
                return ops[0] + ' |=| ~' + ops[0] + ' & ' + ops[1]
        elif mnem[1:4] in ('add', 'sub') and mnem[-1] in 'bw' and mnem[4:-1] in ('s', 'us'):
            if eoc(2):
                return ops[0] + mnem[-1] + ' |' + mnem[4:-1] + ('+' if mnem[1:4] == 'add' else '-') + '=| ' + ops[1]
        elif mnem.startswith(('pcmpeq', 'pcmpgt')):
            if eoc(2):
                ty = simd_int_types[mnem[-1]]
                return ops[0] + ty + ' |=| ' + ('==' if mnem[4:6] == 'eq' else '>') + ' ' + simd_reg_mem(ops[1], ty)

    return ''
