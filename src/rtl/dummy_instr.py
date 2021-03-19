from pyhcl import *


def dummy_instr(
        # 函数参数
):
    class DUMMY_INSTR(Module):
        #本地参数
        TIMEOUT_CNT_W = U.w(32)(5)
        OP_W = U.w(32)(5)

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
