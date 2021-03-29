# /**
#  * Branch Predictor
#  *
#  * This implements static branch prediction. It takes an instruction and its PC and determines if
#  * it's a branch or a jump and calculates its target. For jumps it will always predict taken. For
#  * branches it will predict taken if the PC offset is negative.
#  *
#  * This handles both compressed and uncompressed instructions. Compressed instructions must be in
#  * the lower 16-bits of instr.
#  *
#  * The predictor is entirely combinational but takes clk/rst_n signals for use by assertions.
#  */

from pyhcl import *
from src.include.pkg import *


def branch_predict(
        # 函数参数
):
    class BRANCH_PREDICT(Module):
        # 本地参数

        io = IO(
            # Instruction from fetch stage
            fetch_rdata_i = Input(U.w(32)),
            fetch_pc_i = Input(U.w(32)),
            fetch_valid_i = Input(Bool),

            # Prediction for supplied instruction
            predict_branch_taken_o = Output(Bool),
            predict_branch_pc_o = Output(Bool)
        )

        imm_j_type = Wire(U.w(32))
        imm_b_type = Wire(U.w(32))
        imm_cj_type = Wire(U.w(32))
        imm_cb_type = Wire(U.w(32))

        branch_imm = Wire(U.w(32))

        instr = Wire(U.w(32))

        instr_j = Wire(Bool)
        instr_b = Wire(Bool)
        instr_cj = Wire(Bool)
        instr_cb = Wire(Bool)

        instr_b_taken = Wire(Bool)

        # provide short internal name for fetch_rdata_i due to reduce wrapping
        instr <<= io.fetch_rdata_i

        # Extract and sign-extend to 32-bit the various immediates that may be used to calculate the target
        instr_buf = Wire(U.w(32))    #用于 i{instr[j]}  ,例如 12{instr[5]}

        # Uncompressed immediates
        for i in range(12):
            instr_buf[i] <<= instr[31]
        imm_j_type <<= CatBits(instr_buf[11:0],instr[19:12],instr[20],instr[30:21],U.w(1)(0))
        for i in range(19):
            instr_buf[i] <<= instr[31]
        imm_b_type <<= CatBits(instr_buf[18:0],instr[31],instr[7],instr[30:25],instr[11:8],U.w(1)(0))

        # Compressed immediates
        for i in range(20):
            instr_buf[i] <<= instr[12]
        imm_cj_type <<= CatBits(instr_buf[19:0], instr[12], instr[8], instr[10:9], instr[6], instr[7],
                                instr[2],instr[11], instr[5:3],U.w(1)(0) )
        for i in range(23):
            instr_buf[i] <<= instr[12]
        imm_cb_type <<= CatBits(instr_buf[22:0],instr[12],instr[6:5],instr[2],instr[11:10],
                                instr[4:3],U.w(1)(0))

        # Determine if the instruction is a branch or a jump

        # Uncompressed branch/jump
        instr_b = instr[6:0] == OPCODE_BRANCH;
        instr_j = instr[6:0] == OPCODE_JAL;

        # Compressed branch/jump
        instr_cb <<= (instr[1:0] == U.w(2)(1)) & ((instr[15:13] == U.w(3)(6)) | (instr[15:13] == U.w(3)(7)))
        instr_cj <<= (instr[1:0] == U.w(2)(1)) & ((instr[15:13] == U.w(3)(5)) | (instr[15:13] == U.w(3)(1)))

        # Select out the branch offset for target calculation based upon the instruction type
        branch_imm <<= imm_b_type

        branch_imm <<= Mux(instr_j,branch_imm,imm_j_type)
        branch_imm <<= Mux(instr_b, branch_imm, imm_b_type)
        branch_imm <<= Mux(instr_cj, branch_imm, imm_cj_type)
        branch_imm <<= Mux(instr_cb, branch_imm, imm_cb_type)

        # `ASSERT_IF(BranchInsTypeOneHot, $onehot0({instr_j, instr_b, instr_cj, instr_cb}), fetch_valid_i)?

        # Determine branch prediction , taken if offset is negetive
        instr_b_taken <<= (instr_b & imm_b_type[31]) | (instr_cb & imm_cb_type[31])

        # Always predict jumps taken otherwise take prediction from 'instr_b_taken'
        predict_branch_taken_o = io.fetch_valid_i & (instr_j | instr_cj | instr_b_taken)
        # Calculate target
        io.predict_branch_pc_o <<= io.fetch_pc_i + branch_imm

        pass



