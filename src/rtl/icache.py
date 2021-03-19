from math import log

from pyhcl import *
from src.include.pkg import *


def icache(
        BranchPredictor = U.w(1)(0),
        BusWidth = U.w(32)(32),
        CacheSizeBytes = U.w(32)(4096),
        IcacheECC = U.w(1)(0),
        LineSize = U.w(32)(64),
        NumWays = U.w(32)(2),
        # only cache branch targets
        BranchCache = U.w(1)(0)
):
    # Local constants
    ADDR_W = U.w(32)(32)
    # Number of fill buffers(must be >= 2)
    NUM_FB = U.w(32)(4)
    # Request throttling threshold
    FB_THRESHOLD = NUM_FB-2
    # Derived parameters
    LINE_SIZE_ECC = Mux(IcacheECC,(LineSize + 8),LineSize)
    LINE_SIZE_BYTES = LineSize/8
    LINE_W = int(log(LINE_SIZE_BYTES,2))
    BUS_BYTES = BusWidth/8
    BUS_W = int(log(BUS_BYTES),2)
    LINE_BEATS = LINE_SIZE_BYTES/BUS_BYTES
    LINE_BEATS_W = int(log(LINE_BEATS,2))
    NUM_LINES = CacheSizeBytes/NumWays/LINE_SIZE_BYTES
    INDEX_W = int(log(NUM_LINES,2))
    INDEX_HI = INDEX_W + LINE_W - 1
    TAG_SIZE = ADDR_W-INDEX_W-LINE_W + 1
    TAG_SIZE_ECC = Mux(IcacheECC,(TAG_SIZE+6),TAG_SIZE)
    OUTPUT_BEATS = (BUS_BYTES / 2)


    class ICACHE(Module):
        io = IO(
            #Signal that the core would like instructions
            req_i = Input(Bool),

            # set the cache`s address counter
            branch_i = Input(Bool),
            branch_spec_i = Input(Bool),
            predicted_branch_i = Input(Bool),
            branch_mispredict_i =Input(Bool),
            addr_i = Input(U.w(32)),

            #if stage interface: Pass fetched instruction to the core
            ready_i = Input(Bool),
            valid_o = Output(Bool),
            rdata_o = Output(U.w(32)),
            addr_o = Output(U.w(32)),
            err_o = Output(Bool),
            err_plus2_o = Output(Bool),

            # Instrucion memory / interconnect interface: Fetch instruction data from memory
            instr_req_o = Output(Bool),
            instr_gnt_i = Input(Bool),
            instr_addr_o = Output(U.w(32)),
            instr_rdata_i = Input(U.w(BusWidth)),
            instr_err_i = Input(Bool),
            instr_pmp_err_i = Input(Bool),
            instr_rvalid_i = Input(Bool),

            # Cache status
            icache_enable_i = Input(Bool),
            icache_inval_i = Input(Bool),
            busy_o = Output(Bool)
        )
        # Prefetch signals
        lookup_addr_aligned = Wire(U.w(ADDR_W))
        branch_mispredict_addr = Wire(U.w(ADDR_W))
        prefetch_addr_d = Wire(U.w(ADDR_W))
        prefetch_addr_q = Wire(U.w(ADDR_W))
        prefetch_addr_en = Wire(Bool)
        branch_or_mispredict = Wire(Bool)

        # Cache pipeline ICO signals
        branch_suppress = Wire(Bool)
        lookup_throttle = Wire(Bool)
        lookup_req_ic0 = Wire(Bool)
        lookup_addr_ic0 = Wire(U.w(ADDR_W))
        lookup_index_ic0 = Wire(U.w(INDEX_W))
        fill_req_ic0 = Wire(Bool)
        fill_index_ic0 = Wire(U.w(INDEX_W))
        fill_tag_ic0 = Wire(U.w(TAG_SIZE))
        fill_wdata_ic0 = Wire(U.w((LineSize)))
        lookup_grant_ic0 = Wire(Bool)
        lookup_actual_ic0 = Wire(Bool)
        fill_grant_ic0 = Wire(Bool)
        tag_req_ic0 = Wire(Bool)
        tag_index_ic0 = Wire(U.w(INDEX_W))
        tag_bank_ic0 = Wire(U.w(NumWays))
        tag_write_ic0 = Wire(Bool)
        tag_wdata_ic0 = Wire(U.w(TAG_SIZE_ECC))
        data_req_ic0 = Wire(Bool)
        data_index_ic0 = Wire(U.w(INDEX_W))
        data_banks_ic0 = Wire(U.w(NumWays))
        data_write_ic0 = Wire(Bool)
        data_wdata_ic0 = Wire(LINE_SIZE_ECC)

        #Cache pipelipe IC1 signals

        #####????????????????????????????????????????????
        tag_rdata_ic1 = Wire(Vec(NumWays,U.w(TAG_SIZE_ECC)))
        data_rdata_ic1 = Wire(Vec(NumWays,U.w(TAG_SIZE_ECC)))
        hit_data_ic1 = Wire(U.w(LINE_SIZE_ECC))
        lookup_valid_ic1 = Wire(Bool)

        #???????????????
        lookup_addr_ic1 = Wire(U.w(ADDR_W))
        tag_match_ic1 = Wire(U.w(NumWays))
        tag_hit_ic1 = Wire(Bool)
        tag_invalid_ic1 = Wire(U.w(NumWays))
        lowest_invalid_way_ic1 = Wire(U.w(NumWays))
        round_robin_way_ic1 = Wire(U.w(NumWays))
        round_robin_way_q = Wire(U.w(NumWays))
        sel_way_ic1 = Wire(U.w(NumWays))
        ecc_err_ic1 = Wire(Bool)
        ecc_write_req = Wire(Bool)
        ecc_write_ways = Wire(U.w(NumWays))
        ecc_write_index = Wire(U.w(INDEX_W))

        #Fill buffer signals
        gnt_or_pmp_err = Wire(Bool)
        gnt_not_pmp_err = Wire(Bool)
        fb_fill_level = Wire(U.w(int(log(NUM_FB,2))))
        fill_cache_new = Wire(Bool)
        fill_new_alloc = Wire(Bool)
        fill_spec_req = Wire(Bool)
        fill_spec_done = Wire(Bool)
        fill_spec_hold = Wire(Bool)
        fill_older_d = Wire(Vec(NUM_FB,U.w(NUM_FB)))
        fill_older_q = Wire(Vec(NUM_FB,U.w(NUM_FB)))

        fill_alloc_sel = Wire(U.w(NUM_FB))
        fill_alloc = Wire(U.w(NUM_FB))
        fill_busy_d = Wire(U.w(NUM_FB))
        fill_busy_q = Wire(U.w(NUM_FB))
        fill_done = Wire(U.w(NUM_FB))
        fill_in_ic1 = Wire(U.w(NUM_FB))
        fill_stale_d = Wire(U.w(NUM_FB))
        fill_stale_q = Wire(U.w(NUM_FB))
        fill_cache_d = Wire(U.w(NUM_FB))
        fill_cache_q = Wire(U.w(NUM_FB))
        fill_hit_ic1 = Wire(U.w(NUM_FB))
        fill_hit_d = Wire(U.w(NUM_FB))
        fill_hit_q = Wire(U.w(NUM_FB))


        fill_ext_cnt_d = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_ext_cnt_q = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_ext_hold_d = Wire(U.w(NUM_FB))
        fill_ext_hold_q = Wire(U.w(NUM_FB))
        fill_ext_done_d = Wire(U.w(NUM_FB))
        fill_ext_done_q = Wire(U.w(NUM_FB))
        fill_rvd_cnt_d = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_rvd_cnt_q = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_rvd_done = Wire(U.w(NUM_FB))
        fill_ram_done_d = Wire(U.w(NUM_FB))
        fill_ram_done_q = Wire(U.w(NUM_FB))
        fill_out_grant = Wire(U.w(NUM_FB))
        fill_out_cnt_d = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_out_cnt_q = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_out_done = Wire(U.w(NUM_FB))
        fill_ext_req = Wire(U.w(NUM_FB))
        fill_rvd_exp = Wire(U.w(NUM_FB))
        fill_ram_req = Wire(U.w(NUM_FB))
        fill_out_req = Wire(U.w(NUM_FB))
        fill_data_sel = Wire(U.w(NUM_FB))
        fill_data_reg = Wire(U.w(NUM_FB))
        fill_data_hit = Wire(U.w(NUM_FB))
        fill_data_rvd = Wire(U.w(NUM_FB))
        fill_ext_off = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_rvd_off = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_ext_beat = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_rvd_beat = Wire(Vec(NUM_FB,U.w(LINE_BEATS_W)))
        fill_ext_arb = Wire(U.w(NUM_FB))
        fill_ram_arb = Wire(U.w(NUM_FB))
        fill_out_arb = Wire(U.w(NUM_FB))
        fill_rvd_arb = Wire(U.w(NUM_FB))
        fill_entry_en = Wire(U.w(NUM_FB))
        fill_addr_en = Wire(U.w(NUM_FB))
        fill_way_en = Wire(U.w(NUM_FB))
        fill_data_en = Wire(Vec(NUM_FB,U.w(LINE_BEATS)))
        fill_err_d = Wire(Vec(NUM_FB,U.w(LINE_BEATS)))
        fill_err_q = Wire(Vec(NUM_FB,U.w(LINE_BEATS)))
        fill_addr_q = Wire(Vec(NUM_FB,U.w(ADDR_W)))
        fill_way_q = Wire(Vec(NUM_FB,U.w(NumWays)))
        fill_data_d = Wire(Vec(NUM_FB,U.w(LineSize)))
        fill_data_q = Wire(Vec(NUM_FB,U.w(LineSize)))
        fill_ext_req_addr = Wire(U.w(ADDR_W))
        fill_ram_req_addr = Wire(U.w(ADDR_W))
        fill_ram_req_way = Wire(U.w(NumWays))
        fill_ram_req_data = Wire(U.w(LineSize))
        fill_out_data = Wire(U.w(LineSize))
        fill_out_err = Wire(U.w(LINE_BEATS))

        #External req signals
        instr_req = Wire(Bool)
        instr_addr = Wire(U.w((ADDR_W)))
        # Data output signals
        skid_complete_instr = Wire(Bool)
        skid_ready = Wire(Bool)
        output_compressed = Wire(Bool)
        skid_valid_d = Wire(Bool)
        skid_valid_q = Wire(Bool)
        skid_en = Wire(Bool)
        skid_data_d = Wire(U.w((16)))
        skid_data_q = Wire(U.w((16)))
        skid_err_q = Wire(Bool)
        output_valid = Wire(Bool)
        addr_incr_two = Wire(Bool)
        output_addr_en = Wire(Bool)
        output_addr_incr = Wire(U.w((ADDR_W)))
        output_addr_d = Wire(U.w((ADDR_W)))
        output_addr_q = Wire(U.w((ADDR_W)))
        output_data_lo = Wire(U.w((16)))
        output_data_hi = Wire(U.w((16)))
        data_valid = Wire(Bool)
        output_ready = Wire(Bool)
        line_data = Wire(U.w((LineSize)))
        line_err = Wire(U.w((LINE_BEATS)))
        line_data_muxed = Wire(U.w((32)))
        line_err_muxed = Wire(Bool)
        output_data = Wire(U.w((32)))
        output_err = Wire(Bool)
        # Invalidations
        start_inval = Wire(Bool)
        inval_done = Wire(Bool)
        reset_inval_q = Wire(Bool)
        inval_prog_d = Wire(Bool)
        inval_prog_q = Wire(Bool)
        inval_index_d = Wire(U.w(INDEX_W))
        inval_index_q = Wire(U.w((INDEX_W)))


















