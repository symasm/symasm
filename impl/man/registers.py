# [Based on 325462-sdm-vol-1-2abcd-3abcd-4.pdf]

registers_info = {
'EFLAGS' : '''\

The 32-bit EFLAGS register contains a group of status flags, a control flag,
and a group of system flags.

The next figure shows the most commonly used flags of EFLAGS.

                      11 10 7 6 2 0
┌─────────────────────┬──┬─┬─┬─┬─┬─┐
│                     │O │D│S│Z│P│C│
│                     │F │F│F│F│F│F│
└─────────────────────┴┬─┴┬┴┬┴┬┴┬┴┬┘
                       │  │ │ │ │ │
S Overflow Flag (OF)───┘  │ │ │ │ │
C Direction Flag (DF)─────┘ │ │ │ │
S Sign Flag (SF)────────────┘ │ │ │
S Zero Flag (ZF)──────────────┘ │ │
S Parity Flag (PF)──────────────┘ │
S Carry Flag (CF)─────────────────┘

S Indicates a Status Flag
C Indicates a Control Flag

Show all flags?<EXTRA />
                         21 20  19  18 17 16  14 13 12 11 10 9 8 7 6  4  2  0
┌───────────────────────┬──┬───┬───┬──┬──┬──┬┬──┬─────┬──┬──┬─┬─┬─┬─┬┬─┬┬─┬┬─┐
│                       │ID│VIP│VIF│AC│VM│RF││NT│IOPL │OF│DF│I│T│S│Z││A││P││C│
│                       │  │   │   │  │  │  ││  │     │  │  │F│F│F│F││F││F││F│
└───────────────────────┴┬─┴─┬─┴─┬─┴┬─┴┬─┴┬─┴┴┬─┴──┬──┴┬─┴┬─┴┬┴┬┴┬┴┬┴┴┬┴┴┬┴┴┬┘
                         │   │   │  │  │  │   │    │   │  │  │ │ │ │  │  │  │
X ID Flag────────────────┘   │   │  │  │  │   │    │   │  │  │ │ │ │  │  │  │
X Virtual Interrupt Pending──┘   │  │  │  │   │    │   │  │  │ │ │ │  │  │  │
X Virtual Interrupt Flag─────────┘  │  │  │   │    │   │  │  │ │ │ │  │  │  │
X Alignment Check / Access Control──┘  │  │   │    │   │  │  │ │ │ │  │  │  │
X Virtual-8086 Mode (VM)───────────────┘  │   │    │   │  │  │ │ │ │  │  │  │
X Resume Flag (RF)────────────────────────┘   │    │   │  │  │ │ │ │  │  │  │
X Nested Task (NT)────────────────────────────┘    │   │  │  │ │ │ │  │  │  │
X I/O Privilege Level (IOPL)───────────────────────┘   │  │  │ │ │ │  │  │  │
S Overflow Flag (OF)───────────────────────────────────┘  │  │ │ │ │  │  │  │
C Direction Flag (DF)─────────────────────────────────────┘  │ │ │ │  │  │  │
X Interrupt Enable Flag (IF)─────────────────────────────────┘ │ │ │  │  │  │
X Trap Flag (TF)───────────────────────────────────────────────┘ │ │  │  │  │
S Sign Flag (SF)─────────────────────────────────────────────────┘ │  │  │  │
S Zero Flag (ZF)───────────────────────────────────────────────────┘  │  │  │
S Auxiliary Carry Flag (AF)───────────────────────────────────────────┘  │  │
S Parity Flag (PF)───────────────────────────────────────────────────────┘  │
S Carry Flag (CF)───────────────────────────────────────────────────────────┘

S Indicates a Status Flag
C Indicates a Control Flag
X Indicates a System Flag''',

'OF' : '''\
Overflow flag (bit 11 of the EFLAGS register) — Set if the integer result
is too large a positive number or too small a negative number (excluding
the sign-bit) to fit in the destination operand; cleared otherwise. This
flag indicates an overflow condition for signed-integer (two's complement)
arithmetic.''',

'EAX' : '''\
EAX is a lower 32-bit part of the RAX register, an accumulator for operands and results data.

This register is used to store the result of a function in all calling conventions.[[[well-known fact]]]

It is [implicitly] used in the following instructions:[[[https://www.cs.tufts.edu/comp/40-2011f/readings/amd-implicit-regs.pdf <- google:‘ecx register implicitly used instructions’][-1]]]
• Operand for decimal arithmetic, multiply, divide, string, compare-and-exchange, table-translation,
  and I/O instructions (MUL, IMUL, DIV, IDIV, CMPXCHG, CMPXCHG8B, CMPXCHG16B, IN*, OUT*, [-...-]).
• Special sign extension instructions (CWD, CDQ, CQO, CBW, CWDE, CDQE).
...
• CPUID.''',

'ECX' : '''\
ECX is a lower 32-bit part of the RCX register, a counter for string and loop operations.

It is [implicitly] used in the following instructions:[[[-1]]]
• Bit index for shift and rotate instructions (SAL/SHL, SAR, SHR, SHLD, SHRD).
• Iteration count for loop (LOOP, LOOPE, LOOPNE).
• Repeated string instructions (REP, REPE/REPZ, REPNE/REPNZ).
• Jump conditional if zero (JRCXZ, JECXZ, JCXZ).
• CPUID.

According to the Intel ABI, Microsoft x64, and System V AMD64 ABI, the ECX/RCX is a caller-saved (volatile) register.[[[https://en.wikipedia.org/wiki/X86_calling_conventions]]]
In Microsoft x64, RCX denotes the first [integer] argument of the called function.
In the System V AMD64 ABI, RCX denotes the fourth [integer] argument of the called function.''',
}
