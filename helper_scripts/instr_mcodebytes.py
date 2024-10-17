import os, json, subprocess, re

if not os.path.isfile('instr_mcodebytes.json'):
    open('instr_mcodebytes.json', 'w').write(json.dumps({'fasm_path':'-', 'nasm_path':'-', 'gas_path':'', 'uasm_path':'-'}, indent=0))
config = json.load(open('instr_mcodebytes.json', encoding='utf-8-sig'))
fasm_path = config['fasm_path']
nasm_path = config['nasm_path']
gas_path  = config[ 'gas_path']
uasm_path = config['uasm_path']

if os.name == 'nt':
    # Get path to ml64.exe (MASM)
    if not os.path.isfile('masm_pathname.txt'):
        was_break = False
        for version in ['2022', '2019', '2017', '2015', '2013']:
            for edition in ['BuildTools', 'Community', 'Enterprise', 'Professional']:
                for x86 in [0, 1]:
                    vcvarsall = 'C:\\Program Files' + ' (x86)'*x86 + '\\Microsoft Visual Studio\\' + version + '\\' + edition + R'\VC\Auxiliary\Build\vcvarsall.bat'
                    if os.path.isfile(vcvarsall):
                        was_break = True
                        #print('Using ' + version + '\\' + edition)
                        break
                if was_break:
                    break
            if was_break:
                break
        if was_break:
            masm_pathname = subprocess.check_output('"' + vcvarsall + '" x64 > nul && where ml64', encoding = 'ascii').rstrip()
            open('masm_pathname.txt', 'w').write(masm_pathname)
        else:
            print('''Unable to find vcvarsall.bat!
If you do not have Visual Studio 2013, 2015, 2017, 2019 or 2022 installed please install it or Build Tools for Visual Studio from here[https://visualstudio.microsoft.com/downloads/].''')
            masm_pathname = '-'
    else:
        masm_pathname = open('masm_pathname.txt').read()
else:
    masm_pathname = '-'

def bytes_to_hex(b):
    #return b.hex(' ').upper() # for Python 3.8+
#   return ' '.join(hex(i)[2:].zfill(2).upper() for i in b)
    return ' '.join('%02X' % i for i in b)

while True:
    instruction = input('>>>   ')

    # MASM
    if masm_pathname != '-':
        open('input.masm', 'w').write(".CODE\n" + instruction + "\nEND")
        r = subprocess.run([masm_pathname, '/nologo', 'input.masm', '/c'], text=True, stdout=subprocess.PIPE)
        if r.returncode == 0:
            b = open('input.obj', 'rb').read()
            masm_code = bytes_to_hex(b[0x8C : 0x8C+int.from_bytes(b[0x24:0x28], 'little')])
            os.remove('input.obj')
        else:
            print(r.stdout)
            masm_code = 'ERROR'
        os.remove('input.masm')
    else:
        # UASM >[https://stackoverflow.com/questions/304555/masm-under-linux <- google:‘masm linux’]:‘UASM is a free MASM-compatible assembler based on JWasm.’
        if uasm_path != '-':
            open('input.uasm', 'w').write(".X64\n.MODEL FLAT\n.CODE\n" + instruction + "\nEND")
            subprocess.run([os.path.join(uasm_path, 'uasm'), '-bin', 'input.uasm'], stdout=subprocess.DEVNULL)
            masm_code = bytes_to_hex(open('input.BIN', 'rb').read())
            os.remove('input.uasm')
            os.remove('input.BIN')
        else:
            masm_code = '-'

    # FASM
    if fasm_path != '-':
        open('input.asm', 'w').write("use64\n" + instruction)
        subprocess.run([os.path.join(fasm_path, 'fasm'), 'input.asm', 'output.bin'], stdout=subprocess.DEVNULL)
        fasm_code = bytes_to_hex(open('output.bin', 'rb').read())
        os.remove('output.bin')
    else:
        fasm_code = '-'

    # NASM
    if nasm_path != '-':
        subprocess.run([os.path.join(nasm_path, 'nasm'), 'input.asm', '-o', 'output_nasm.bin'], stdout=subprocess.DEVNULL)
        nasm_code = bytes_to_hex(open('output_nasm.bin', 'rb').read())
        os.remove('output_nasm.bin')
        os.remove('input.asm')
    else:
        nasm_code = '-'

    # GAS
    if gas_path != '-':
        instructiong = re.sub(r'\b(\d[\da-fA-F]*)[hH]\b', r'0x\1', instruction) # >[https://stackoverflow.com/questions/46746145/x86-intel-syntax-ambigious-size-for-mov-junk-h-after-expression <- google:‘Error: junk `h' after expression’]:‘GNU's assembler (even in Intel syntax mode) doesn't support constants with the base specified as a suffix.’
        subprocess.run([os.path.join(gas_path, 'as'), '-msyntax=intel', '-mnaked-reg'], input=instructiong+"\n", universal_newlines=True, stdout=subprocess.DEVNULL) # -'‘universal_newlines’'+'‘text’' for Python 3.7
        b = open('a.out', 'rb').read()
        gas_code = bytes_to_hex(b[0x8C : 0x8C+int.from_bytes(b[0xD2:0xD6], 'little')] if os.name == 'nt' else b[0x40 : 0x40+int.from_bytes(b[0x138:0x13C], 'little')])
        os.remove('a.out')
    else:
        gas_code = '-'

    if masm_code == fasm_code == nasm_code == gas_code:
        print('     ', masm_code)
    else:
        print('MASM:' if masm_pathname != '-' else 'UASM:', masm_code)
        print('FASM:', fasm_code)
        print('NASM:', nasm_code)
        print(' GAS:',  gas_code)
    print()
