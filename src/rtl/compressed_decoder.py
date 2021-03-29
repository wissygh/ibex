# /**
#  * Compressed instruction decoder
#  *
#  * Decodes RISC-V compressed instructions into their RV32 equivalent.
#  * This module is fully combinatorial, clock and reset are used for
#  * assertions only.
#  */

from pyhcl import *
from src.include.pkg import *

def compressed_decoder():
    class COMPRESSED_DECODER(Module):
        io = IO(
            valid_i = Input(Bool),
            instr_i = Input(U.w(32)),
            instr_o = Output(U.w(32)),
            is_compressed_o =  Output(Bool),
            illegal_instr_o = Output(Bool)
         )

        # valid_i indicates if instr_i is valid and is used for assertions only.
        # The following signal is used to avoid possible lint errors.
        unused_valid = Wire(Bool)
        unused_valid <<=  io.valid_i

        #########################
        ### Compressed  decoder
        #########################
        io.instr_o <<= io.instr_i
        io.illegal_instr_o <<= U.w(1)(0)
        # Check if incoming instructon is cpompressed.
        # C0
        with when(io.instr_i[1:0]==U.w(2)(0)):
            with when(io.instr_i[15:13]==U.w(3)(0)):
                # c.addi4spn -> addi rd', x2, imm
                io.instr_o <<= CatBits(U.w(2)(0),io.instr_i[10:7],io.str_i[12:11],io.instr_i[5],
                                       io.instr_i[6],U.w(2)(0),U.w(5)(0x02),U.w(3)(0),U.w(2)(1),io.instr_i[4:2],OPCODE_OP_IMM)
                with when(io.instr_i[12:5]==U.w(8)(0)):
                    io.illegal_instr_o <<= U.w(1)(1)

            with elsewhen(io.instr_i[15:13] == U.w(3)(2)):
                # c.lw -> lw rd', imm(rs1`)
                io.instr_o <<= CatBits(U.w(5)(0),io.instr_i[5],io.str_i[12:10],io.instr_i[6],
                                       U.w(2)(0),U.w(2)(1),io.instr_i[9:7],U.w(3)(2),U.w(2)(1),io.instr_i[4:2],OPCODE_LOAD)

            with elsewhen(io.instr_i[15:13]==U.w(3)(6)):
                io.instr_o <<= CatBits(U.w(5)(0),io.instr_i[5],io.str_i[12],U.w(2)(1),io.instr_i[4:2],
                                       U.w(2)(1),io.instr_i[9:7],U.w(3)(2),io.instr_i[11:10],io.instr_i[6],
                                       U.w(2)(0),OPCODE_STORE)

            with otherwise:
                io.illegal_instr_o <<= U.w(1)(1)

        #C1
        with elsewhen(io.instr_i[1:0] == U.w(2)(1)):
            with when(io.instr_i[15:13] == U.w(3)(0)):
                # c.addi -> addi rd, rd, nzimm
                # c.nop
                io.instr_o = CatBits()
            with elsewhen(io.instr_i[15:13] == U.w(3)(2) | io.instr_i[15:13] == U.w(3)(5)):
            with elsewhen(io.instr_i[15:13] == U.w(3)(3)):
            with elsewhen(io.instr_i[15:13] == U.w(3)(4)):
            with elsewhen(io.instr_i[15:13] == U.w(3)(6) | io.instr_i[15:13] == U.w(3)(7)):
            with otherwise:




        # C2
        with elsewhen(io.instr_i[1:0] == U.w(2)(2)):

        with otherwise:
            io.illegal_instr_o <<= U.w(1)(1)


    return compressed_decoder()

