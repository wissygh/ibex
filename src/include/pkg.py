from pyhcl import *
from enum import Enum








###############
##if stage
###############

# pc mux selection
PC_BOOT =   U.w(3)(0)
PC_JUMP =   U.w(3)(1)
PC_EXC  =   U.w(3)(2)
PC_ERET =   U.w(3)(3)
PC_DRET =   U.w(3)(4)
PC_BP   =   U.w(3)(5)

# Exception PC mux selection

EXC_PC_EXC =   U.w(2)(0)
EXC_PC_IRQ =   U.w(2)(1)
EXC_PC_DBD =   U.w(2)(2)
EXC_PC_DBG_EXC =   U.w(2)(3)  #Exception while in debug mode

# Exception cause
EXC_CAUSE_IRQ_SOFTWARE_M     = CatBits(U.w(1)(1),U.w(5)(3))
EXC_CAUSE_IRQ_TIMER_M        = CatBits(U.w(1)(1),U.w(5)(7))
EXC_CAUSE_IRQ_EXTERNAL_M     = CatBits(U.w(1)(1),U.w(5)(11))
# EXC_CAUSE_IRQ_FAST_0      = CatBits(U.w(1)(1),U.w(5)(16)),
# EXC_CAUSE_IRQ_FAST_14     = CatBits(U.w(1)(1),U.w(5)(30))
EXC_CAUSE_IRQ_NM             = CatBits(U.w(1)(1),U.w(5)(31)) # == EXC_CAUSE_IRQ_FAST_15
EXC_CAUSE_INSN_ADDR_MISA     = CatBits(U.w(1)(0),U.w(5)(0)),
EXC_CAUSE_INSTR_ACCESS_FAULT = CatBits(U.w(1)(0),U.w(5)(1)),
EXC_CAUSE_ILLEGAL_INSN       = CatBits(U.w(1)(0),U.w(5)(2)),
EXC_CAUSE_BREAKPOINT         = CatBits(U.w(1)(0),U.w(5)(3))
EXC_CAUSE_LOAD_ACCESS_FAULT  = CatBits(U.w(1)(0),U.w(5)(5))
EXC_CAUSE_STORE_ACCESS_FAULT = CatBits(U.w(1)(0),U.w(5)(7))
EXC_CAUSE_ECALL_UMODE        = CatBits(U.w(1)(0),U.w(5)(8))
EXC_CAUSE_ECALL_MMODE        = CatBits(U.w(1)(0),U.w(5)(11))