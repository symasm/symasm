from .common import *

simd_simple_float_instructions = {
    'add' : '+',
    'sub' : '-',
    'mul' : '*',
    'div' : '/',
    'and' : '&',
    'or'  : '|',
}

simd_complex_float_instructions = {
    'andn' : '~<op1> & <op2>',
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

simd_int_type_shifts = {
    'b' : 0,
    'w' : 1,
    'd' : 2,
    'q' : 3,
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
    'movaps' : ('|=a|', 's'),
    'movups' : ('|=u|', 's'),
    'movapd' : ('|=a|', 'd'),
    'movupd' : ('|=u|', 'd'),
    'movdqa' : ('|=a|', 'l'),
    'movdqu' : ('|=u|', 'l'),
    'movss'  : ('=', 's'),
    'movsd'  : ('=', 'd'),
}

sse_move_instructions = {
    'movlps' : ('s[0:2]', '|=|'),
    'movhps' : ('s[2:4]', '|=|'),
    'movlpd' : ('d[0]', '='),
    'movhpd' : ('d[1]', '='),
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

simd_float_intrinsics_with_1_operand = {
    'sqrt',
    'rsqrt',
}

simd_float_intrinsics_with_2_operands = {
    'hadd',
    'min',
    'max',
}

simd_int_intrinsics_with_2_operands = {
    'hadd',
    'mins',
    'minu',
    'maxs',
    'maxu',
    'avg',
}

simd_special_intrinsics_with_2_operands = {
    'punpcklbw' : ('unpacklo', 'b'),
    'punpcklwd' : ('unpacklo', 'w'),
    'punpckldq' : ('unpacklo', 'i'),
    'punpcklqdq': ('unpacklo', 'l'),
    'punpckhbw' : ('unpackhi', 'b'),
    'punpckhwd' : ('unpackhi', 'w'),
    'punpckhdq' : ('unpackhi', 'i'),
    'punpckhqdq': ('unpackhi', 'l'),

    'unpcklps'  : ('unpacklo', 's'),
    'unpcklpd'  : ('unpacklo', 'd'),
    'unpckhps'  : ('unpackhi', 's'),
    'unpckhpd'  : ('unpackhi', 'd'),

    'pslldq'    : ('bshl',     ''),
    'psrldq'    : ('bshr',     ''),
    'pmuldq'    : ('muli',     'l'),
    'pmuludq'   : ('mului',    'ul'),

    'pshufb'    : ('shuffle',  'b'),
}

simd_packs_intrinsics = {
    'packuswb' : ('packus', 'w', 'b'),
    'packusdw' : ('packus', 'i', 'w'),
    'packsswb' : ('packss', 'w', 'b'),
    'packssdw' : ('packss', 'i', 'w'),
}

def is_simd_reg(operand):
    oplow = operand.lower()
    return oplow[0] in 'xyz' and oplow[1:3] == 'mm' and oplow[3:].isdigit()

def simd_reg_mem(operand: str, ty):
    return operand + ty * is_simd_reg(operand)

def simd_movq_movd(mnem, ops, token, errors: List[Error] = None):
    if coc(2, ops, token, errors):
        v = 'v' * (mnem[0] == 'v')
        if ops[1].lower().startswith('xmm'):
            return ops[0] + ' ' + v + '= ' + ops[1] + ('l' if mnem[-1] == 'q' else 'i')
        elif ops[0].lower().startswith('xmm'):
            return ops[0] + ('l' if mnem[-1] == 'q' else 'i') + ' ' + v + '= ' + ops[1]
        else:
            if errors is not None:
                errors.append(error_at_token(f'one of the operands of the `{token.string}` instruction must be a xmm register', token))
    return ''

def simd_cvt(mnem: str, op1, op2, a = ''):
    assert not 'pi' in mnem, 'MMX instructions are not supported'
    mnem = mnem.replace('dq', 'pi')
    assert mnem[-5] == mnem[-2] and mnem[-2] in 'ps' and mnem[-3] == '2'

    v = 'v' * (mnem[0] == 'v')
    p = '|' * (mnem[-2] == 'p')
    end = ''

    if not mnem.endswith('si'):
        op1 += mnem[-1]
    if mnem[-2] == 'p' and \
       mnem[-4] == 'd' and op1.lower().startswith('xmm') \
                       and op2.lower().startswith('xmm'):
        assert(mnem[-1] != 'd')
        end = ', ' + op1 + '[2:4] |=| 0'
        op1 += '[0:2]'

    if mnem[-2] == 'p' and \
       mnem[-1] == 'd' and op1.lower().startswith('xmm') \
                       and op2.lower().startswith('xmm'):
        assert(mnem[-4] != 'd')
        a = '[0:2]'

    if mnem[-1] in 'sd' and mnem[-4] in 'sd':
        op2 = 'convert(' + op2 + mnem[-4] + a + ')'
    elif mnem[-4] == 'i':
        op2 = 'float(' + op2 + 'i'*len(p) + a + ')'
    elif mnem.startswith(('cvtt', 'vcvtt')):
        op2 = 'int(' + op2 + mnem[-4] + ')'
    else:
        op2 = 'int(round(' + op2 + mnem[-4] + '))'

    return op1 + ' ' + v + p + '=' + p + ' ' + op2 + end

def is_simd_sxzx(mnem):
    return mnem[:-2] in ('pmovsx', 'pmovzx') and mnem[-2:] in ('bw', 'bd', 'bq', 'wd', 'wq', 'dq')

def simd_sxzx_slice(mnem, ops) -> str:
    #ratio = {'bw':2, 'bd':4, 'bq':8, 'wd':2, 'wq':4, 'dq':2}[mnem[-2:]]
    dst_sz = 16 << (ord(ops[0][0].lower()) - ord('x')) >> simd_int_type_shifts[mnem[-1]]
    src_sz = 16 << (ord(ops[1][0].lower()) - ord('x')) >> simd_int_type_shifts[mnem[-2]]
    assert(src_sz >= dst_sz)
    return f'[0:{dst_sz}]' if src_sz != dst_sz else ''

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
        if coc(2, ops, token, errors):
            op, ty = simd_move_instructions[mnem]
            if is_simd_reg(ops[0]):
                return ops[0] + ty + ' ' + op + ' ' + ops[1]
            else:
                assert(is_simd_reg(ops[1]))
                return ops[0] + ' ' + op + ' ' + ops[1] + ty

    elif mnem in sse_move_instructions:
        if coc(2, ops, token, errors):
            regc, op = sse_move_instructions[mnem]
            if is_simd_reg(ops[0]):
                return ops[0] + regc + ' ' + op + ' ' + ops[1]
            else:
                return ops[0] + ' ' + op + ' ' + ops[1] + regc

    elif mnem in ('movq', 'movd'):
        return simd_movq_movd(mnem, ops, token, errors)

    elif mnem in ('movmskps', 'movmskpd'):
        if coc(2, ops, token, errors):
            return ops[0] + ' |=| ' + 'mask' + '(' + ops[1] + mnem[-1] + ')'

    elif mnem in simd_special_intrinsics_with_2_operands and not mnem in simd_simple_register_instructions:
        if eoc(2):
            iname, ty = simd_special_intrinsics_with_2_operands[mnem]
            return ops[0] + ty + ' |.=| ' + iname + '(' + ops[1] + ')'

    elif mnem in simd_packs_intrinsics:
        if eoc(2):
            iname, ty_src, ty_dst = simd_packs_intrinsics[mnem]
            return ops[0] + ty_dst + ' |=| ' + iname + '(' + ops[0] + ty_src + ', ' + ops[1] + ty_src + ')'

    elif mnem[:-5] in ('cvt', 'cvtt'):
        if coc(2, ops, token, errors):
            return simd_cvt(mnem, ops[0], ops[1])

    elif is_simd_sxzx(mnem):
        if eoc(2):
            return ops[0] + simd_int_types[mnem[-1]] + ' |=| ' + mnem[4] + 'x(' + simd_reg_mem(ops[1], simd_int_types[mnem[-2]] + simd_sxzx_slice(mnem, ops)) + ')'

    elif mnem[0] == 'p':
        if mnem[1:-1] in simd_simple_int_instructions and mnem[-1] in simd_int_types:
            if eoc(2):
                return ops[0] + simd_int_types[mnem[-1]] + ' |' + simd_simple_int_instructions[mnem[1:-1]] + '=| ' + ops[1]
        elif mnem[1:-1] in simd_int_intrinsics_with_2_operands and mnem[-1] in simd_int_types:
            if eoc(2):
                return ops[0] + simd_int_types[mnem[-1]] + ' |.=| ' + mnem[1:-1] + '(' + ops[1] + ')'
        elif mnem == 'pmovmskb':
            if coc(2, ops, token, errors):
                return ops[0] + ' |=| ' + 'mask' + '(' + ops[1] + simd_int_types[mnem[-1]] + ')'
        elif mnem[1:] in simd_simple_int_bitwise_instructions:
            if eoc(2):
                if mnem == 'pxor' and ops[0] == ops[1]:
                    return ops[0] + ' |=| 0'
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
        elif mnem[:-1] == 'pinsr':
            if eoc(3):
                if mnem[-1] in 'bw':
                    sz = cpu_gp_reg_size(ops[1])
                    if sz != 0:
                        assert(sz == 4)
                        ops[1] = cpu_gp_reg_4b_to_1b(ops[1]) if mnem[-1] == 'b' else cpu_gp_reg_4b_to_2b(ops[1])
                return ops[0] + simd_int_types[mnem[-1]] + '[' + ops[2] + '] = ' + ops[1]
        elif mnem[:-1] == 'pextr':
            if coc(3, ops, token, errors):
                return ops[0] + ' = ' + ops[1] + simd_int_types[mnem[-1]] + '[' + ops[2] + ']'

    elif mnem[-1] in 'sd' and mnem[-2] in 'sp':
        if mnem[:-2] in simd_simple_float_instructions:
            if eoc(2):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' ' + p + simd_simple_float_instructions[mnem[:-2]] + '=' + p + ' ' + ops[1]
        elif mnem[:-2] in simd_complex_float_instructions:
            if eoc(2):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' ' + p + '=' + p + ' ' + simd_complex_float_instructions[mnem[:-2]].replace('<op1>', ops[0]).replace('<op2>', ops[1])
        elif mnem in simd_simple_register_instructions:
            if eoc(2):
                if not ops[1].lower().startswith('xmm'):
                    if errors is not None:
                        errors.append(error_at_token(f'all operands of the `{token.string}` instruction must be registers', token))
                    return ''
                return simd_simple_register_instructions[mnem].replace('xmm1', ops[1]).replace('<xmm0>', ops[0])
        elif mnem[:-2] in simd_float_intrinsics_with_1_operand \
          or mnem[:-2] in simd_float_intrinsics_with_2_operands:
            if eoc(2):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' ' + p + '.'*(mnem[:-2] in simd_float_intrinsics_with_2_operands) + '=' + p + ' ' + mnem[:-2] + '(' + ops[1] + ')'
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

    if mnem[1:] in simd_move_instructions:
        if coc(2, ops, token, errors):
            op, ty = simd_move_instructions[mnem[1:]]
            if is_simd_reg(ops[0]):
                return ops[0] + ty + ' v' + op + ' ' + ops[1]
            else:
                assert(is_simd_reg(ops[1]))
                return ops[0] + ' v' + op + ' ' + ops[1] + ty

    if mnem[-1] in 'sd' and mnem[:-1] == 'vxorp':
        if eoc(3):
            if ops[1] == ops[2]:
                return ops[0] + mnem[-1] + ' v|=| 0'
            else:
                return ops[0] + mnem[-1] + ' v|=| ' + ops[1] + ' (+) ' + ops[2]

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

    elif mnem in ('vmovq', 'vmovd'):
        return simd_movq_movd(mnem, ops, token, errors)

    elif mnem[1:] in simd_special_intrinsics_with_2_operands:
        if eoc(3):
            iname, ty = simd_special_intrinsics_with_2_operands[mnem[1:]]
            return ops[0] + ty + ' v|=| ' + iname + '(' + ops[1] + ', ' + ops[2] + ')'

    elif mnem[1:] in simd_packs_intrinsics:
        if eoc(3):
            iname, ty_src, ty_dst = simd_packs_intrinsics[mnem[1:]]
            return ops[0] + ty_dst + ' v|=| ' + iname + '(' + ops[1] + ty_src + ', ' + ops[2] + ty_src + ')'

    elif mnem[:-5] in ('vcvt', 'vcvtt'):
        if mnem.endswith(('ss', 'sd')):
            if eoc(3):
                if ops[0] == ops[1]:
                    return simd_cvt(mnem, ops[0], ops[2])
                else:
                    return simd_cvt(mnem, ops[0], ops[2], '[0]'*(mnem[-4] != 'i')) + ', ' + ops[1] + ('s[1:4]' if mnem[-1] == 's' else 'd[1]')
        else:
            if coc(2, ops, token, errors):
                return simd_cvt(mnem, ops[0], ops[1])

    elif is_simd_sxzx(mnem[1:]):
        if eoc(2):
            return ops[0] + simd_int_types[mnem[-1]] + ' v|=| ' + mnem[5] + 'x(' + simd_reg_mem(ops[1], simd_int_types[mnem[-2]] + simd_sxzx_slice(mnem, ops)) + ')'

    elif mnem in ('vbroadcastss', 'vbroadcastsd'):
        if eoc(2):
            return ops[0] + mnem[-1] + ' v|=| broadcast(' + ops[1] + ')'

    elif mnem[1] == 'p':
        if mnem[2:-1] in simd_simple_int_instructions and mnem[-1] in simd_int_types:
            if eoc(3):
                return ops[0] + simd_int_types[mnem[-1]] + ' v|=| ' + ops[1] + ' ' + simd_simple_int_instructions[mnem[2:-1]] + ' ' + ops[2]
        elif mnem[2:-1] in simd_int_intrinsics_with_2_operands and mnem[-1] in simd_int_types:
            if eoc(3):
                return ops[0] + simd_int_types[mnem[-1]] + ' v|=| ' + mnem[2:-1] + '(' + ops[1] + ', ' + ops[2] + ')'
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
        elif mnem[:-1] == 'vpinsr':
            if eoc(4):
                assert(ops[0] == ops[1])
                if mnem[-1] in 'bw':
                    sz = cpu_gp_reg_size(ops[2])
                    if sz != 0:
                        assert(sz == 4)
                        ops[2] = cpu_gp_reg_4b_to_1b(ops[2]) if mnem[-1] == 'b' else cpu_gp_reg_4b_to_2b(ops[2])
                return ops[0] + simd_int_types[mnem[-1]] + '[' + ops[3] + '] v= ' + ops[2]
        elif mnem[:-1] == 'vpextr':
            if coc(3, ops, token, errors):
                return ops[0] + ' v= ' + ops[1] + simd_int_types[mnem[-1]] + '[' + ops[2] + ']'

    elif mnem[-1] in 'sd' and mnem[-2] in 'sp':
        if mnem[1:-2] in simd_simple_float_instructions:
            if eoc(3):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' v' + p + '=' + p + ' ' + ops[1] + ' ' + simd_simple_float_instructions[mnem[1:-2]] + ' ' + ops[2]
        elif mnem[1:-2] in simd_complex_float_instructions:
            if eoc(3):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' v' + p + '=' + p + ' ' + simd_complex_float_instructions[mnem[1:-2]].replace('<op1>', ops[1]).replace('<op2>', ops[2])
        elif mnem[1:-2] in simd_float_intrinsics_with_1_operand:
            ty = mnem[-1]
            if mnem[-2] == 'p':
                if eoc(2):
                    return ops[0] + ty + ' v|=| ' + mnem[1:-2] + '(' + ops[1] + ')'
            else:
                if eoc(3):
                    if ops[0] == ops[1]:
                        return ops[0] + ty + ' v= ' + mnem[1:-2] + '(' + ops[2] + ')'
                    else:
                        return ops[0] + ty + ' v= ' + mnem[1:-2] + '(' + ops[2] + ty + '[0]' + '), ' + ops[1] + ('s[1:4]' if ty == 's' else 'd[1]')
        elif mnem[1:-2] in simd_float_intrinsics_with_2_operands:
            if eoc(3):
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' v' + p + '=' + p + ' ' + mnem[1:-2] + '(' + ops[1] + ', ' + ops[2] + ')'
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
        elif mnem[1:-5] in ('fmadd', 'fmsub') and mnem[-5:-2].isdigit():
            if eoc(3):
                def o(i):
                    return ops[int(mnem[-5+i]) - 1]
                p = '|' * (mnem[-2] == 'p')
                return ops[0] + mnem[-1] + ' v' + p + '=' + p + ' ' + o(0) + ' * ' + o(1) + (' + ' if mnem[1:-5] == 'fmadd' else ' - ') + o(2)
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

    elif mnem in ('vextractf128', 'vextracti128'):
        if coc(3, ops, token, errors):
            assert(ops[2] == '1')
            ty = 'd' if mnem == 'vextractf128' else 'l'
            return simd_reg_mem(ops[0], ty) + ' v|=| ' + ops[1] + ty + '[2:4]'

    elif mnem in ('vinsertf128', 'vinserti128'):
        if eoc(4):
            assert(ops[3] == '1' and ops[0] == ops[1])
            ty = 'd' if mnem == 'vinsertf128' else 'l'
            return ops[0] + ty + '[2:4] v|=| ' + ops[2] + ty

    return ''

def is_reg(reg):
    return is_cpu_gp_reg(reg) or is_simd_reg(reg)
