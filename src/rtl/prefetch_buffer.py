# /**
#  * Prefetcher Buffer for 32 bit memory interface
#  *
#  * Prefetch Buffer that caches instructions. This cuts overly long critical
#  * paths to the instruction cache.
#  */

from pyhcl import *
from src.include.pkg import *

def prefetch_buffer(
        BranchPredictor = U.w(1)(0)
):
    NUM_REQS = U.w(32)(2)
    class PREFETCH_BUFFER(Module):
        io = IO(
            req_i = Input(Bool),

            branch_i = Input(Bool),
            branch_spec_i = Input(Bool),
            predicted_branch_i = Input(Bool),
            branch_mispredict_i = Input(Bool),
            addr_i = Input(U.w(32)),

            ready_i = Input(Bool),
            valid_o = Output(Bool),
            rdata_o = Output(U.w(32)),
            addr_o = Output(U.w(32)),
            err_o = Output(Bool),
            err_plus2_o = Output(Bool),

            # gose to instruction memory/instruction cache
            instr_req_o = Output(Bool),
            instr_gnt_i = Input(Bool),
            instr_addr_o = Output(U.w(32)),
            instr_rdata_i = Input(U.w(32)),
            instr_err_i = Input(Bool),
            instr_pmp_err_i = Input(Bool),
            instr_rvalid_i = Input(Bool),

            #Prefetch Buffer Status
            busy_o = Output(Bool)

        )

        branch_suppress = Wire(Bool)
        valid_new_req = Wire(Bool)
        valid_req = Wire(Bool)
        valid_req_d = Wire(Bool)
        valid_req_q= Wire(Bool)
        discard_req_d = Wire(Bool)
        discard_req_q = Wire(Bool)
        gnt_or_pmp_err = Wire(Bool)
        rvalid_or_pmp_err = Wire(Bool)

        rdata_outstanding_n = Wire(U.w(NUM_REQS))
        rdata_outstanding_s = Wire(U.w(NUM_REQS))
        rdata_outstanding_q = Wire(U.w(NUM_REQS))
        branch_discard_n = Wire(U.w(NUM_REQS))
        branch_discard_s = Wire(U.w(NUM_REQS))
        branch_discard_q = Wire(U.w(NUM_REQS))
        rdata_pmp_err_n = Wire(U.w(NUM_REQS))
        rdata_pmp_err_s = Wire(U.w(NUM_REQS))
        rdata_pmp_err_q = Wire(U.w(NUM_REQS))
        rdata_outstanding_rev = Wire(U.w(NUM_REQS))

        stored_addr_d = Wire(U.w(32))
        stored_addr_q = Wire(U.w(32))
        stored_addr_en = Wire(Bool)
        fetch_addr_d = Wire(U.w(32))
        fetch_addr_q = Wire(U.w(32))
        fetch_addr_en = Wire(Bool)
        branch_mispredict_addr = Wire(U.w(32))
        instr_addr = Wire(U.w(32))
        instr_addr_w_aligned = Wire(U.w(32))
        instr_or_pmp_err = Wire(Bool)

        fifo_valid = Wire(Bool)
        fifo_addr = Wire(U.w(32))
        fifo_ready = Wire(Bool)
        fifo_clear = Wire(Bool)
        fifo_busy = Wire(U.w(NUM_REQS))
        valid_raw = Wire(Bool)
        addr_next = Wire(U.w(32))
        branch_or_mispredict = Wire(Bool)

        #############################
        ## Prefetch buffer status
        #############################

