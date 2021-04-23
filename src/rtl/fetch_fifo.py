# /**
#  * Fetch Fifo for 32 bit memory interface
#  *
#  * input port: send address and data to the FIFO
#  * clear_i clears the FIFO for the following cycle, including any new request
#  */

from pyhcl import *


def fetch_fifo(
        # 函数参数
        NUM_REQS = U.w(32)(2)

):
    class FETCH_FIFO(Module):
        # 本地参数
        DEPTH = NUM_REQS +1

        io = IO(
            # io端口

            # control signals
            clear_i = Input(Bool),
            busy_o = Output(U.w(NUM_REQS)),

            # input port
            in_valid_i = Input(Bool),
            in_addr_i = Input(U.w(32)),
            in_rdata_i = Input(U.w(32)),
            in_err_i = Input(Bool),

            # ouput port
            out_valid_o = Output(Bool),
            out_ready_i = Input(Bool),
            out_addr_o = Output(U.w(32)),
            out_addr_next_o = Output(U.w(32)),
            out_rdata_o = Output(U.w(32)),
            out_err_o = Output(Bool),
            out_err_plus2_o = Output(Bool)
        )
        # index 0 is used for output
        rdata_d = Wire(Vec(DEPTH,U.w(32)))
        rdata_q = Wire(Vec(DEPTH,U.w(32)))
        err_d = Wire(U.w(DEPTH))
        err_q = Wire(U.w(DEPTH))
        valid_d = Wire(U.w(DEPTH))
        valid_q = Wire(U.w(DEPTH))
        lowest_free_entry = Wire(U.w(DEPTH))
        valid_pushed = Wire(U.w(DEPTH))
        valid_poped = Wire(U.w(DEPTH))
        entry_en = Wire(U.w(DEPTH))

        pop_fifo = Wire(Bool)
        rdata = Wire(U.w(32))
        rdata_unaligned = Wire(U.w(32))
        err = Wire(Bool)
        err_unaligned = Wire(Bool)
        err_plus2 = Wire(Bool)
        valid = Wire(Bool)
        valid_unaligned = Wire(Bool)

        aligned_is_compressed = Wire(Bool)
        unaligned_is_compressed = Wire(Bool)

        addr_incr_two = Wire(Bool)
        instr_addr_next = Wire(U.w(32))
        instr_addr_d = Wire(U.w(32))
        instr_addr_q = Wire(U.w(32))
        instr_addr_en = Wire(Bool)
        unused_addr_in = Wire(Bool)

        # // // // // // // // // /
        # // Output         port //
        # // // // // // // // // /

        rdata <<= Mux(valid_q[0], rdata_q[0], io.in_rdata_i)
        err   <<= Mux(valid[0], err_q[0], io.in_err_i)
        valid <<= valid_q[0] | io.in_valid_i

        # the FIFO contains word aligned memory fetches, but the instructions contained in each entry
        # might be half-word aligned(due to compressed instructions)
        # e.g.
        # .............| 31...........16|15.............0|
        # FIFO entry 0 | Instr 1 [15:0] | Instr 0 [15:0] |
        # FIFO entry 0 | Instr 1 [15:0] | Instr 0 [15:0] |

        # The FIFO also has a direct bypass path, so a complete instruction might be made up of data
        # from the FIFO and new incoming data

        # construct the output data for an unaligned instruction
        rdata_unaligned <<= Mux(valid_q[1], CatBits((rdata_q[1][15:0],rdata[31:16])),
                                CatBits(io.in_rdata_i[15:0], rdata[31:16]))

        # If entry[1] is valid, an error can come from entry[0] or entry[1], unless the
        # instruction in entry[0] is compressed (entry[1] is a new instruction)
        # If entry[1] is not valid, and entry[0] is, an error can come from entry[0] or the incoming
        # data, unless the instruction in entry[0] is compressed
        # If entry[0] is not valid, the error must come from the incoming data
        err_unaligned <<= Mux(valid_q[1], (err_q[1] & ~unaligned_is_compressed) | err_q[0] ,
                              (valid_q[0] & err_q[0]) |
                              (io.in_err_i & (~valid_q[0] | ~unaligned_is_compressed)))

        # Record when an error is caused by the second half of an unaligned 32bit instruction
        # Only needs to be correct when unaligned and if err_unaligned is set
        err_plus2 <<= Mux(valid_q[1], err_q[1] & ~err_q[0],
                                      io.in_err_i & valid_q[0] & ~err_q[0])

        # An uncomoressed unaligned instruction is only valid if both parts are available
        valid_unaligned<<= Mux(valid_q[1], U.w(1)(1), valid_q[0] & io.in_valid_i)

        # If there is an error , rdata is unknown
        unaligned_is_compressed <<= (rdata[17:16] != U.w(2)(3)) & ~err
        aligned_is_compressed <<= (rdata[1:0] != U.w(2)(3)) & ~err

        # // // // // // // // // // // // // // // // // // // // //
        # // Instruction    aligner( if unaligned) //
        # // // // // // // // // // // // // // // // // // // // //


    return FETCH_FIFO()
