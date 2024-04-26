import sys


cc_to_sym = # generated by [helper_scripts/collect_all_condition_codes.py]

sym_to_cc = {}
for cc, sym in cc_to_sym:
    assert(sym not in sym_to_cc)
    sym_to_cc[sym] = cc

cc_to_sym.update() # generated by [helper_scripts/collect_all_condition_codes.py]


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
