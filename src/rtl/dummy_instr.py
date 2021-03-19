from pyhcl import *


def dummy_instr(
        # 函数参数
):
    class DUMMY_INSTR(Module):
        #本地参数
        TIMEOUT_CNT_W = U.w(32)(5)
        OP_W = U.w(32)(5)
        LFSR_OUT_W = U.w(32)(17)

        DUMMY_ADD = U.w(2)(0)
        DUMMY_MUL = U.w(2)(1)
        DUMMY_DIV = U.w(2)(2)
        DUMMY_AND = U.w(2)(3)

        io = IO(
            # io端口
            # interface to CSRs
            dummy_instr_en_i=Input(Bool),
            dummy_instr_mask_i=Input(U.w(3)),
            dummy_instr_seed_en_i=Input(Bool),
            dummy_instr_seed_i=Input(U.w(32)),

            # Interface to IF stage
            fetch_valid_i=Input(Bool),
            id_in_ready_i=Input(Bool),
            insert_dummy_instr_o=Output(Bool),
            dummy_instr_data_o=Output(U.w((32)))
        )
        lfsr_data_instr_type = Wire(U.w(2))
        lfsr_data_op_b = Wire(U.w(5))
        lfsr_data_op_a = Wire(U.w(5))
        lfsr_data_cnt = Wire(U.w(5))

        dummy_cnt_incr = Wire(U.w(TIMEOUT_CNT_W))
        dummy_cnt_threshold = Wire(U.w(TIMEOUT_CNT_W))
        dummy_cnt_d = Wire(U.w(TIMEOUT_CNT_W))
        dummy_cnt_q = Wire(U.w(TIMEOUT_CNT_W))
        dummy_cnt_en = Wire(Bool)
        lfsr_en = Wire(Bool)
        lfsr_state = Wire(U.w(LFSR_OUT_W))
        insert_dummy_instr = Wire(Bool)
        dummy_set = Wire(U.w(7))
        dummy_opcode = Wire(U.w(3))
        dummy_instr = Wire(U.w(32))
        dummy_instr_seed_q = Reg(U.w(32))
        dummy_instr_seed_d = Reg(U.w(32))

        # Shift the LFSR every time we insert an instruction
        lfsr_en <<= insert_dummy_instr & io.id_in_ready_i
        dummy_instr_seed_d <<= dummy_instr_seed_q ^ io.dummy_instr_seed_i

        with when(~Module.reset):
            dummy_instr_seed_q <<= 0
        with elsewhen(io.dummy_instr_seed_en_i):
            dummy_instr_seed_q <<= dummy_instr_seed_d

        #     prim_lfsr  # (
        #     .LfsrDw(32),
        #     .StateOutDw(LFSR_OUT_W)
        #
        # ) lfsr_i(
        # .clk_i(clk_i),
        # .rst_ni(rst_ni),
        # .seed_en_i(dummy_instr_seed_en_i),
        # .seed_i(dummy_instr_seed_d),
        # .lfsr_en_i(lfsr_en),
        # .entropy_i('0                    ),
        #            .state_o(lfsr_state)
        #            );

        # // Extract fields from LFSR
        # assign lfsr_data = lfsr_data_t'(lfsr_state);


        # Set count threshold for inserting a new instruction . This is the pseudo-random value from the
        # LFSR with a mask applied (based on CSR cofig) to shorten the period if required

        dummy_cnt_threshold <<= lfsr_data_cnt & CatBits(io.dummy_instr_mask_i,)
















