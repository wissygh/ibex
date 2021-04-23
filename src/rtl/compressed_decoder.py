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
        mul_buffer = Wire(U.w(16))
        for i in range(16):
            mul_buffer[i] <<= io.instr_i[12]
        with elsewhen(io.instr_i[1:0] == U.w(2)(1)):
            with when(io.instr_i[15:13] == U.w(3)(0)):
                # c.addi -> addi rd, rd, nzimm
                # c.nop
                io.instr_o <<= CatBits(mul_buffer[5:0], io.instr_i[12], io.instr_i[6:2],
                                     io.instr_i[11:7], U.w(3)(0), io.instr_i[11:7], OPCODE_OP_IMM)
            with elsewhen(io.instr_i[15:13] == U.w(3)(1) | io.instr_i[15:13] == U.w(3)(5)):
                # // 001: c.jal -> jal x1, imm
                # // 101: c.j   -> jal x0, imm
                io.instr_o <<= CatBits(io.instr_i[12],io.instr_i[8], io.instr_i[10:9], io.instr_i[6],
                                     io.instr_i[7], io.instr_i[2], io.instr_i[11], io.instr_i[5:3],
                                     mul_buffer[8:0], U.w(4)(0), ~io.instr_i[15], OPCODE_JAL)
            with elsewhen(io.instr_i[15:13] == U.w(3)(2)):
                # // c.li -> addi rd, x0, nzimm
                # // (c.li hints are translated into an addi hint)
                io.instr_o <<= CatBits(mul_buffer[5:0], io.instr_i[12], io.instr_i[6:2], U.w(5)(0),
                                     U.w(3)(0), io.instr_i[11:7], OPCODE_OP_IMM )
            with elsewhen(io.instr_i[15:13] == U.w(3)(3)):
                # // c.lui -> lui  rd, imm
                # // (c.lui hints are translated into a lui hint)
                io.instr_o <<= CatBits(mul_buffer[14:0], io.instr_i[6:2], io.instr_i[11:7], OPCODE_LUI)
                if( io.instr_i[11:7] == U.w(5(0x02))):
                    # // c.addi16sp -> addi x2, x2, nzimm
                    io.instr_o <<= CatBits(mul_buffer[2:0], io.instr_i[4:3], io.instr_i[5], io.instr_i[2],
                                         io.instr_i[6], U.w(4)(0), U.w(5)(0x02), U.w(3)(0), U.w(5)(0x02),
                                         OPCODE_OP_IMM)
                if(  CatBits(io.instr_i[12], io.instr_i[6:2]) == U.w(6)(0) ):
                    io.illegal_instr_o <<= U.w(1)(1)
            with elsewhen(io.instr_i[15:13] == U.w(3)(4)):
                with when(io.instr_i[11:10] == U.w(2)(0) | io.instr_i[11:10] == U.w(2)(1)):
                    # // 00: c.srli -> srli  rd, rd, shamt
                    # // 01: c.srai -> srai rd, rd, shamt
                    # // (c.srli / c.srai hints are translated into a srli / srai hint)
                    io.instr_o <<= CatBits(U.w(1)(0), io.instr_i[10], U.w(5)(0), io.instr_i[6:2], U.w(2)(1)
                                           ,io.instr_i[9:7], U.w(3)(5), U.w(2)(1), io.instr_i[9:7],
                                           OPCODE_OP_IMM)
                    if(io.instr_i[12] == U.w(1)(1)):
                        io.illegal_instr_o <<= U.w(1)(1)

                with elsewhen(io.instr_i[11:10] == U.w(2)(2)):
                    # // c.andi -> andi   rd, rd, imm
                    io.instr_o <<= CatBits(mul_buffer[5:0], io.instr_i[12],  io.instr_i[6:2], U.w(2)(1)
                                           , io.instr_i[9:7], U.w(3)(7), U.w(2)(1), io.instr_i[9:7],
                                           OPCODE_OP_IMM)
                with elsewhen(io.instr_i[11:10] == U.w(2)(3)):
                    with when(CatBits(io.instr_i[12], io.instr_i[6:5]) == U.w(3)(0)):
                        # // c.sub -> sub rd ', rd', rs2 '
                        io.instr_o <<= CatBits(U.w(2)(0), U.w(5)(0), io.instr_i[4:2], U.w(2)(1), io.instr_i[9:7],
                                               U.w(3)(0), U.w(2)(1).io.instr_i[9:7], OPCODE_OP)
                    with when(CatBits(io.instr_i[12], io.instr_i[6:5]) == U.w(3)(1)):
                        # // c.xor -> xor  rd ', rd', rs2'
                        io.instr_o <<= CatBits(U.w(7)(0), U.w(2)(1), io.instr_i[4:2], U.w(2)(1), io.instr_i[9:7],
                                               U.w(3)(4), U.w(2)(1), io.instr_i[9:7], OPCODE_OP)
                    with elsewhen(CatBits(io.instr_i[12], io.instr_i[6:5]) == U.w(3)(2)):
                        # / c. or  -> or rd ', rd', rs2 '
                        io.instr_o <<= CatBits(U.w(7)(0), U.w(2)(1), io.instr_i[4:2], U.w(2)(1), io.instr_i[9:7],
                                               U.w(3)(6), U.w(2)(1), io.instr_i[9:7], OPCODE_OP)
                    with elsewhen(CatBits(io.instr_i[12], io.instr_i[6:5]) == U.w(3)(3)):
                        # // c. and -> and rd  ', rd', rs2'
                        io.instr_o <<= CatBits(U.w(7)(0), U.w(2)(1), io.instr_i[4:2], U.w(2)(1), io.instr_i[9:7],
                                               U.w(3)(7), U.w(2)(1), io.instr_i[9:7], OPCODE_OP)
                    with otherwise:
                        # // 100: c.subw
                        # // 101: c.addw
                        io.illegal_instr_o <<= U.w(1)(1)


            with elsewhen(io.instr_i[15:13] == U.w(3)(6) | io.instr_i[15:13] == U.w(3)(7)):
                # // 0: c.beqz -> beq rs1   ', x0, imm
                # // 1: c.bnez -> bne rs1   ', x0, imm
                io.instr_o <<= CatBits(mul_buffer[3:0], io.instr_i[6:5], io.instr_i[2],
                                       U.w(5)(0), U.w(2)(1), io.instr_i[9:7], U.w(2)(0),
                                       io.instr_i[13], io.instr_i[11:10], io.instr_i[4:3],
                                       io.instr_i[12], OPCODE_BRANCH)
            with otherwise:
                io.illegal_instr_o <<= U.w(1)(1)




        # C2
        with elsewhen(io.instr_i[1:0] == U.w(2)(2)):

            with when(io.instr_i[15:13] == U.w(3)(0)):
                # // c.slli -> slli  rd, rd, shamt
                # // (c.ssli hints are translated into a slli hint)
                io.instr_o <<= CatBits(U.w(7)(0), io.instr_i[6:2], io.instr_i[11:7],
                                       U.w(3)(1), io.instr_i[11:7],OPCODE_OP_IMM)
                if(io.instr_i[12] == U.w(1)(1)):
                    io.illegal_instr_o = U.w(1)(1)
            with elsewhen(io.instr_i[15:13] == U.w(3)(2)):
                # // c.lwsp -> lw rd, imm(x2)
                io.instr_o <<= CatBits(U.w(4)(0), io.instr_i[3:2], io.instr_i[12], io.instr_i[6:4],
                                       U.w(2)(0), U.w(5)(0x02), U.w(3)(2), io.instr_i[11:7], OPCODE_LOAD)
                if(io.instr_i[11:7] == U.w(5)(0)):
                    io.illegal_instr_o <<= U.w(1)(1)
            with elsewhen(io.instr_i[15:13] == U.w(3)(4)):
                if(io.instr_i[12] == U.w(1)(0)):
                    if(io.instr_i[6:2] != U.w(5)(0)):
                        # // c.mv -> add   rd / rs1, x0, rs2
                        # // (c.mv hints are translated into an add hint)
                        io.instr_o <<= CatBits(U.w(7)(0), io.instr_i[6:2], U.w(5)(0), U.w(3)(0),
                                               io.instr_i[11:7], OPCODE_OP)
                    else:
                        # // c.jr -> jalr  x0, rd / rs1, 0
                        io.instr_o <<= CatBits(U.w(12)(0), io.instr_i[11:7], U.w(3)(0), U.w(5)(0), OPCODE_JALR)
                        if(io.instr_i[11:7] == U.w(5)(0)):
                            io.illegal_instr_o <<= U.w(1)(1)
                else:
                    if(io.instr_i[6:2] != U.w(5)(0)):
                        # // c.add -> add    rd, rd, rs2
                        # // (c.add hints are translated into an add hint)
                        io.instr_o <<= CatBits(U.w(7)(0), io.instr_i[6:2], io.instr_i[11:7],
                                               U.w(3)(0),io.instr_i[11:7], OPCODE_OP)
                    else:
                        if(io.instr_i[11:7] == U.w(5)(0)):
                            # // c.ebreak -> ebreak
                            io.instr_o <<= U.w(32)(0x00100073)
                        else:
                            # // c.jalr -> jalr  x1, rs1, 0
                            io.instr_o <<= CatBits(U.w(12)(0), io.instr_i[11:7], U.w(3)(0),
                                                   U.w(5)(1), OPCODE_JALR)

            with elsewhen(io.instr_i[15:13] == U.w(3)(6)):
                # // c.swsp -> sw  rs2, imm(x2)
                io.instr_o <<= CatBits(U.w(4)(0), io.instr_i[8:7], io.instr_i[12], io.instr_i[6:2],
                                       U.w(5)(0x02), U.w(3)(2), io.instr_i[11:9], U.w(2)(0), OPCODE_STORE)

            with otherwise:
                io.illegal_instr_o <<= U.w(1)(1)

        # // Incoming instruction is not compressed.
        with elsewhen(io.instr_i[1:0] == U.w(2)(3)):
            pass

        with otherwise:
            io.illegal_instr_o <<= U.w(1)(1)

        io.is_compressed_o <<= (io.instr_i[1:0] != U.w(2)(3))

    return COMPRESSED_DECODER()

