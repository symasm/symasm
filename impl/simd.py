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
    'sll' : '<<',
    'srl' : 'u>>',
    'sra' : '>>',
    'adds' : 's+',
    'subs' : 's-',
    'addus' : 'us+',
    'subus' : 'us-',
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

avx_move_from_mem_instructions = {
    'vmovaps' : '<dst>s v|=a| <src>',
    'vmovups' : '<dst>s v|=u| <src>',
    'vmovapd' : '<dst>d v|=a| <src>',
    'vmovupd' : '<dst>d v|=u| <src>',
    'vmovdqa' : '<dst>l v|=a| <src>',
    'vmovdqu' : '<dst>l v|=u| <src>',
}

sse_cmp_float = {
    'eq' : '==',
    'lt' : '<',
    'le' : '<=',
    'unord' : '',
    'neq' : '!=',
    'nlt' : '!<',
    'nle' : '!<=',
    'ord' : '',
}
simd_cmp_float = dict(list(sse_cmp_float.items()) + list({ # starting with Python 3.9, it will be possible to use the merge operator (`|`)
    'eq_uq' : 'uo==',                                      # `simd_cmp_float.update()` doesn't work in transpiler [error C2011: 'symasm::CodeBlock1' : 'struct' type redefinition]
    'nge'   : '!>=',
    'ngt'   : '!>',
    'false' : '',
    'neq_oq': 'o!=',
    'ge'    : '>=',
    'gt'    : '>',
    'true'  : '',
}.items()))

def is_simd_reg(operand):
    oplow = operand.lower()
    return oplow[0] in 'xyz' and oplow[1:3] == 'mm' and oplow[3:].isdigit()

def simd_reg_mem(operand: str, ty):
    return operand + ty * is_simd_reg(operand)

def sse_to_symasm(mnem, ops: List[str], token, errors: List[Error] = None):
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
        if mnem[:-2] in simd_simple_float_instructions:
            if eoc(2):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' ' + p + simd_simple_float_instructions[mnem[:-2]] + '=' + p + ' ' + ops[1]
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
        elif mnem.startswith('cmp') and mnem[3:-2] in sse_cmp_float:
            if eoc(2):
                csym = sse_cmp_float[mnem[3:-2]]
                op = '.' * (csym == '') + '='
                if mnem[-2] == 'p':
                    op = '|' + op + '|'
                right = simd_reg_mem(ops[1], mnem[-1])
                right = csym + ' ' + right if csym != '' else 'cmp' + mnem[3:-2] + '(' + right + ')'
                return ops[0] + mnem[-1] + ' ' + op + ' ' + right

    elif mnem[0] == 'p':
        if mnem[1:-1] in simd_simple_int_instructions and mnem[-1] in simd_int_types:
            if eoc(2):
                return ops[0] + simd_int_types[mnem[-1]] + ' |' + simd_simple_int_instructions[mnem[1:-1]] + '=| ' + ops[1]
        elif mnem[1:] in simd_simple_int_bitwise_instructions:
            if eoc(2):
                return ops[0] + ' |' + simd_simple_int_bitwise_instructions[mnem[1:]] + '=| ' + ops[1]
        elif mnem == 'pandn':
            if eoc(2):
                return ops[0] + ' |=| ~' + ops[0] + ' & ' + ops[1]
        # elif mnem[1:4] in ('add', 'sub') and mnem[-1] in 'bw' and mnem[4:-1] in ('s', 'us'):
        #     if eoc(2):
        #         return ops[0] + mnem[-1] + ' |' + mnem[4:-1] + ('+' if mnem[1:4] == 'add' else '-') + '=| ' + ops[1]
        elif mnem.startswith(('pcmpeq', 'pcmpgt')):
            if eoc(2):
                ty = simd_int_types[mnem[-1]]
                return ops[0] + ty + ' |=| ' + ('==' if mnem[4:6] == 'eq' else '>') + ' ' + simd_reg_mem(ops[1], ty)

    return ''

def simd_to_symasm(mnem, ops: List[str], token, errors: List[Error] = None):
    if mnem[0] != 'v':
        s = sse_to_symasm(mnem, ops, token, errors)
        if s != '':
            return s
        return ''

    def eoc(n): # expected operand count
        if not coc(n, ops, token, errors):
            return False
        if n == 3:
            if not is_simd_reg(ops[0]) or not is_simd_reg(ops[1]):
                if errors is not None:
                    errors.append(error_at_token(f'first two operands of the `{token.string}` instruction must be registers', token))
                return False
        elif n == 2:
            if not is_simd_reg(ops[0]):
                if errors is not None:
                    errors.append(error_at_token(f'the first operand of the `{token.string}` instruction must be a register', token))
                return False
        return True

    if mnem in avx_move_from_mem_instructions:
        if eoc(2):
            return avx_move_from_mem_instructions[mnem].replace('<dst>', ops[0]).replace('<src>', ops[1])
    
    elif mnem[1:-1] == 'movntp':
        if coc(2, ops, token, errors):
            return ops[0] + ' v|=nt| ' + ops[1] + mnem[-1]

    elif mnem[1:] in ('movlps', 'movhps'):
        if eoc(3):
            if mnem[1:] == 'movlps':
                if ops[0] == ops[1]:
                    return ops[0] + 's[0:2] v|=| ' + ops[2]
                else:
                    return ops[0] + 's v|=| ' + ops[2] + ', ' + ops[1] + 's[2:4]'
            else:
                if ops[0] == ops[1]:
                    return ops[0] + 's[2:4] v|=| ' + ops[2]
                else:
                    return ops[0] + 's v|=| ' + ops[1] + 's[0:2], ' + ops[2]

    elif mnem[-1] in 'sd' and mnem[-2] in 'sp':
        if mnem[1:-2] in simd_simple_float_instructions:
            if eoc(3):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' v' + p + '=' + p + ' ' + ops[1] + ' ' + simd_simple_float_instructions[mnem[1:-2]] + ' ' + ops[2]
        elif mnem[1:-2] == 'rcp':
            if mnem[-1] != 's':
                if errors is not None:
                    errors.append(error_at_token(f'incorrect instruction: `{token.string}`', token))
                return ''
            if mnem[-2] == 'p':
                if eoc(2):
                    return ops[0] + mnem[-1] + ' v|=| 1 / ' + ops[1]
            else:
                if eoc(3):
                    if ops[0] == ops[1]:
                        return ops[0] + mnem[-1] + ' v= 1 / ' + simd_reg_mem(ops[2], mnem[-1])
                    else:
                        return ops[0] + mnem[-1] + ' v|=| 1 / ' + simd_reg_mem(ops[2], mnem[-1]) + '[0], ' + ops[1] + mnem[-1] + '[1:4]'
        elif mnem[1:-5] == 'fmadd' and mnem[-5:-2].isdigit():
            if eoc(3):
                def o(i):
                    return ops[int(mnem[-5+i]) - 1]
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' v' + p + '=' + p + ' ' + o(0) + ' * ' + o(1) + ' + ' + o(2)
        elif mnem[1:-1] == 'shufp':
            if eoc(4):
                b = asm_number(ops[3])
                def i(n):
                    return (b >> (n * 2)) & 0b11
                if mnem == 'vshufps':
                    if ops[0][0].lower() == 'x':
                        if ops[1] == ops[2]:
                            return ops[0] + 's v|=| ' + ops[1] + f's[{i(0)},{i(1)},{i(2)},{i(3)}]'
                        else:
                            return ops[0] + 's v|=| ' + f'{ops[1]}s[{i(0)},{i(1)}], {ops[2]}s[{i(2)},{i(3)}]'
                    else:
                        assert(ops[0][0].lower() == 'y')
                        if ops[1] == ops[2]:
                            return ops[0] + 's v|=| ' + ops[1] + f's[{i(0)},{i(1)},{i(2)},{i(3)},{i(0)+4},{i(1)+4},{i(2)+4},{i(3)+4}]'
                        else:
                            return ops[0] + 's v|=| ' + f'{ops[1]}s[{i(0)},{i(1)}], {ops[2]}s[{i(2)},{i(3)}], {ops[1]}s[{i(0)+4},{i(1)+4}], {ops[2]}s[{i(2)+4},{i(3)+4}]'
                else:
                    assert(mnem == 'vshufpd')
                    if ops[0][0].lower() == 'x':
                        if ops[1] == ops[2]:
                            return ops[0] + 'd v|=| ' + ops[1] + f'd[{i(0)},{i(1)}]'
                        else:
                            return ops[0] + 'd v|=| ' + f'{ops[1]}d[{i(0)}], {ops[2]}d[{i(1)}]'
                    else:
                        assert(ops[0][0].lower() == 'y')
                        if ops[1] == ops[2]:
                            return ops[0] + 'd v|=| ' + ops[1] + f'd[{i(0)},{i(1)},{i(2)+2},{i(3)+2}]'
                        else:
                            return ops[0] + 'd v|=| ' + f'{ops[1]}d[{i(0)}], {ops[2]}d[{i(1)}], {ops[1]}d[{i(2)+2}], {ops[2]}d[{i(3)+2}]'
        elif mnem.startswith('vcmp') and mnem[4:-2] in simd_cmp_float:
            if eoc(3):
                csym = simd_cmp_float[mnem[4:-2]]
                op = '='
                if mnem[-2] == 'p':
                    op = '|' + op + '|'
                if csym != '':
                    return ops[0] + mnem[-1] + ' v' + op + ' ' + ops[1] + mnem[-1] + ' ' + csym + ' ' + simd_reg_mem(ops[2], mnem[-1])
                else:
                    return ops[0] + mnem[-1] + ' v' + op + ' cmp' + mnem[4:-2] + '(' + ops[1] + ', ' + ops[2] + ')'

    elif mnem[1] == 'p':
        if mnem[2:-1] in simd_simple_int_instructions and mnem[-1] in simd_int_types:
            if eoc(3):
                return ops[0] + simd_int_types[mnem[-1]] + ' v|=| ' + ops[1] + ' ' + simd_simple_int_instructions[mnem[2:-1]] + ' ' + ops[2]
        elif mnem[2:] in simd_simple_int_bitwise_instructions:
            if eoc(3):
                return ops[0] + ' v|=| ' + ops[1] + ' ' + simd_simple_int_bitwise_instructions[mnem[2:]] + ' ' + ops[2]
        elif mnem == 'vpandn':
            if eoc(3):
                return ops[0] + ' v|=| ~' + ops[1] + ' & ' + ops[2]
        elif mnem.startswith(('vpcmpeq', 'vpcmpgt')):
            if eoc(3):
                ty = simd_int_types[mnem[-1]]
                return ops[0] + ty + ' v|=| ' + ops[1] + ty + ' ' + ('==' if mnem[5:7] == 'eq' else '>') + ' ' + simd_reg_mem(ops[2], ty)

    elif mnem in ('vextractf128', 'vextracti128'):
        if coc(3, ops, token, errors):
            assert(ops[2] == '1')
            ty = 'd' if mnem == 'vextractf128' else 'l'
            return simd_reg_mem(ops[0], ty) + ' v|=| ' + ops[1] + ty + '[2:4]'

    return ''
