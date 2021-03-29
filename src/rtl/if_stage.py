
# Instruction Fetch Stage
#
# Instruction fetch unit: Selection of the next PC, and buffering (sampling) of
# the read instruction.


from pyhcl import *
from src.include.pkg import *
from src.rtl.branch_predict import *
from src.rtl.compressed_decoder import *
from src.rtl.dummy_instr import *
from src.rtl.icache import *
from src.rtl.prefetch_buffer import *


def if_stage(DmHaltAddr = U.w(32)(0x1A110800),
             DmExceptionAddr = U.w(32)(0x1A110800),
             DummyInstructions = U.w(1)(0),
             ICache = U.w(1)(0),
             ICacheECC = U.w(1)(0),
             PCIncrCheck = U.w(1)(0),
             BranchPredictor = U.w(1)(0)
             ):
    class IF_STAGE(Module):
        io = IO(
            # also used for mtvec
            boot_addr_i = input(U.w(32)),

            # instruction request control
            req_i = input(Bool),

            # instruction cache interface
            instr_req_o = Output(Bool),
            instr_addr_o = Output(Bool),
            instr_gnt_i = Input(Bool),
            instr_rvalid_i = Input(Bool),
            instr_rdata_i = Input(U.w(32)),
            instr_err_i = Input(Bool),
            instr_pmp_err_i = Input(Bool),

            # output of ID stage
            instr_valid_id_o = Output(Bool),
            instr_new_id_o = Output(Bool),
            instr_rdata_id_o = Output(U.w(32)),
            instr_rdata_alu_id_o = Output(U.w(32)),

            instr_rdata_c_id_o = Output(U.w(16)),
            instr_is_compressed_id_o = Output(Bool),
            instr_bp_taken_o = Output(Bool),
            instr_fetch_err_o = Output(Bool),
            instr_fetch_err_plus2_o = Output(Bool),
            illegal_c_insn_id_o = Output(Bool),
            dummy_instr_id_o = Output(Bool),
            pc_if_o = Output(U.w(32)),
            pc_id_o =Output(U.w(32)),

            # control signals
            instr_valid_clear_i = Input(Bool),
            pc_set_i = Input(Bool),
            pc_set_spec_i = Input(Bool),
            pc_mux_i = Input(U.w(3)),
            nt_branch_mispredict_i = Input(Bool),

            exc_pc_mux_i = Input(U.w(2)),
            exc_cause = Input(U.w(6)),

            dummy_instr_en_i = Input(Bool),
            dummy_instr_mask_i = Input(U.w(2)),
            dummy_instr_seed_en_i =Input(Bool),
            dummy_instr_seed_i = Input(U.w(32)),
            icache_enable_i = Input(Bool),
            icache_inval_i = Input(Bool),

            #jump and branch target
            branch_target_ex_i = Input(U.w(32)),

            #CSRs
            csr_mepc_i = Input(U.w(32)),

            csr_depc = Input(U.w(32)),
            csr_mtvec_i = Input(U.w(32)),
            csr_mtvec_init_o = Output(Bool),

            #pipeline stall
            id_in_ready_i = Input(Bool),

            #misc signals
            pc_mismatch_alert_o = Output(Bool),
            if_busy_o = Output(Bool)
        ) #type: IO

        instr_valid_id_d = Reg(Bool)
        instr_valid_id_q = Reg(Bool)
        instr_new_id_d = Reg(Bool)
        instr_new_id_q = Reg(Bool)

        # prefetch buffer related signals
        prefetch_busy = Wire(Bool)
        branch_req = Wire(Bool)
        branch_spec = Wire(Bool)
        predicted_branch = Wire(Bool)
        fetch_addr_n = Wire(U.w(32))
        unused_fetch_addr_n0 = Wire(Bool)

        fetch_valid = Wire(Bool)
        fetch_ready = Wire(Bool)
        fetch_rdata = Wire(U.w(32))
        fetch_addr = Wire(U.w(32))
        fetch_err = Wire(Bool)
        fetch_err_plus2 = Wire(Bool)

        if_instr_valid = Wire(Bool)
        if_instr_rdata = Wire(U.w(32))
        if_instr_addr = Wire(U.w(32))
        if_instr_err = Wire(Bool)

        exc_pc = Wire(U.w(32))

        irq_id = Wire(U.w(6))
        unused_irq_bit = Wire(Bool)
        # if-id pipeline reg write enable
        if_id_pipe_reg_we = Wire(Bool)

        # Dummy instruction signals
        stall_dummy_instr = Wire(Bool)
        instr_out = Wire(U.w(32))
        instr_is_compressed_out = Wire(Bool)
        illegal_c_instr_out = Wire(Bool)
        instr_err_out = Wire(Bool)

        predict_branch_taken = Wire(Bool)
        predict_branch_pc = Wire(U.w(32))

        pc_mux_internal = Wire(U.w(3))

        unused_boot_addr = Wire(U.w(8))
        unused_csr_mtvec = Wire(U.w(8))

        unused_boot_addr <<= io.boot_addr_i[7:0]
        unused_csr_mtvec <<= io.csr_mtvec_i[7:0]

        # extract interrupt id from exception cause
        irq_id <<= io.exc_cause
        unused_irq_bit <<= io.irq_id[5] #MSB distinguishes interrupts from exceptions

        #exception PC selection mux
        with when(io.exc_pc_mux_i == EXC_PC_EXC):
            exc_pc <<= CatBits(io.csr_mtvec_i[31:8],U.w(8)(0x00))
        with elsewhen(io.exc_pc_mux_i == EXC_PC_IRQ):
            exc_pc <<= CatBits(io.csr_mtvec_i[31:8], U.w(1)(0),irq_id[4:0],U.w(2)(0))
        with elsewhen(io.exc_pc_mux_i == EXC_PC_DBD):
            exc_pc <<= DmHaltAddr
        with elsewhen(io.exc_pc_mux_i == EXC_PC_DBG_EXC):
            exc_pc <<= DmExceptionAddr
        with otherwise:
            exc_pc <<= CatBits(io.csr_mtvec_i[31:8],U.w(8)(0x00))

        #The Branch predictor can provide a new PCwhich is internal to if_stage.Only override the mux
        #select to choose this if the core isn't already trying to set a PC.
        pc_mux_internal <<=((BranchPredictor & predicted_branch_taken & ~io.pc_set_i),PC_BP,io.pc_mux_i)

        #fetch address selection mux
        with when(pc_mux_internal == PC_BOOT):
            fetch_addr_n <<= CatBits(io.boot_addr_i[31:8],U.w(8)(0x80))
        with when(pc_mux_internal == PC_JUMP):
            fetch_addr_n <<= io.branch_target_ex_i
        with when(pc_mux_internal == PC_EXC):
            fetch_addr_n <<= exc_pc
        with when(pc_mux_internal == PC_ERET):
            fetch_addr_n <<= io.csr_mepc_i
        with when(pc_mux_internal == PC_DRET):
            fetch_addr_n <<= io.csr_depc_i
        with when(pc_mux_internal == PC_BP):
            fetch_addr_n <<= Mux(BranchPredictor,predict_branch_pc,CatBits(io.boot_addr_i[31:8],U.w(8)(0x80)))
        with otherwise:
            fetch_addr_n <<= CatBits(io.boot_addr_i[31:8],U.w(8)(0x80))

        #tell CS register file to initialize mtvec on boot
        io.csr_mtvec_init_o <<= (io.pc_mux_i == PC_BOOT) & io.pc_set_i

        if(ICache):
            # Full I-Cache option
            icache_i = icache(BranchPredictor=BranchPredictor,IcacheECC=ICacheECC).io
            icache_i.req_i <<= io.req_i
            icache_i.branch_i <<= branch_req
            icache_i.branch_spec_i <<= branch_spec
            icache_i.predicted_branch_i <<= io.nt_branch_mispredict_i
            icache_i.addr_i <<= CatBits(fetch_addr_n[31:1],U.w(1)(0))

            icache_i.ready_i <<= fetch_ready
            fetch_valid <<= icache_i.valid_o
            fetch_rdata <<= icache_i.rdata_o
            fetch_addr <<= icache_i.addr_o
            fetch_err <<= icache_i.err_o
            fetch_err_plus2 <<= icache_i.err_plus2_o

            io.instr_req_o <<= icache_i.instr_req_o
            io.instr_addr_o <<= icache_i.instr_addr_o
            icache_i.instr_gnt_i <<= io.instr_gnt_i
            icache_i.instr_rvalid_i <<= io.instr_rvalid_i
            icache_i.instr_rdata_i <<= io.instr_rdata_i
            icache_i.instr_err_i <<= io.instr_err_i
            icache_i.instr_pmp_err_i <<= io.instr_pmp_err_i

            icache_i.instr_enable_i <<= io.icache_enable_i
            icache_i.inval_i <<= io.icache_inval_i
            icache_i.busy_o <<= prefetch_busy

        else:
            # prefetch buffer, Cache a fixed number of instructions
            prefetch_buffer_i = prefetch_buffer(BranchPredictor=BranchPredictor).io
            prefetch_buffer_i.req_i <<= io.req_i
            prefetch_buffer_i.branch_i <<= branch_req
            prefetch_buffer_i.branch_spec_i <<= branch_spec
            prefetch_buffer_i.predicted_branch_i <<= io.nt_branch_mispredict_i
            prefetch_buffer_i.addr_i <<= CatBits(fetch_addr_n[31:1],U.w(1)(0))

            prefetch_buffer_i.ready_i <<= fetch_ready
            fetch_valid <<= prefetch_buffer_i.valid_o
            fetch_rdata <<= prefetch_buffer_i.rdata_o
            fetch_addr <<= prefetch_buffer_i.addr_o
            fetch_err <<= prefetch_buffer_i.err_o
            fetch_err_plus2 <<= prefetch_buffer_i.err_plus2_o

            io.instr_req_o <<= prefetch_buffer_i.instr_req_o
            io.instr_addr_o <<= prefetch_buffer_i.instr_addr_o
            prefetch_buffer_i.instr_gnt_i <<= io.instr_gnt_i
            prefetch_buffer_i.instr_rvalid_i <<= io.instr_rvalid_i
            prefetch_buffer_i.instr_rdata_i <<= io.instr_rdata_i
            prefetch_buffer_i.instr_err_i <<= io.instr_err_i
            prefetch_buffer_i.instr_pmp_err_i <<= io.instr_pmp_err_i

            prefetch_buffer_i.busy_o <<= prefetch_busy

            #ICache tieoffs
            unused_icen = Wire(Bool)
            unused_icinv = Wire(Bool)
            unused_icen <<= io.icache_enable_i
            unused_icinv <<= io.icache_inval_i

        unused_fetch_addr_n0 <<= fetch_addr_n[0]

        branch_req <<= io.pc_set_i | predict_branch_taken
        branch_req <<= io.pc_set_spec_i | predict_branch_taken
        io.pc_if_o <<= if_instr_addr
        io.if_busy_o <<= prefetch_busy

        #compressed instruction decoding ,or more precisely compressed instruction
        #expander
        #
        #since it dose not matter where we deompress instrductions, we do it here
        #to ease timig closure

        instr_decompressed = Wire(U.w(32))
        illegal_c_insn = Wire(Bool)
        instr_is_compressed = Wire(Bool)

        compressed_decoder_i = compressed_decoder().io
        compressed_decoder_i.valid_i <<= fetch_valid & (~fetch_err)
        compressed_decoder_i.instr_i <<= if_instr_rdata
        instr_decompressed <<= compressed_decoder_i.instr_o
        instr_is_compressed <<= compressed_decoder_i.is_compresed_o
        illegal_c_insn <<= compressed_decoder_i.illegal_instr_o

        # Dummy instruction insertion
        if(DummyInstructions):
            insert_dummy_instr = Reg(Bool)
            dummy_instr_data = Wire(U.w(32))

            dummy_instr_i = dummy_instr().io
            dummy_instr_i.dummy_instr_en_i <<= io.dummy_instr_en_i
            dummy_instr_i.dummy_instr_mask_i <<= io.dummy_instr_mask_i
            dummy_instr_i.dummy_instr_seed_en_i <<= io.dummy_instr_seed_en_i
            dummy_instr_i.dummy_instr_seed_i <<= io.dummy_instr_seed_i
            dummy_instr_i.fetch_valid_i <<= fetch_valid
            dummy_instr_i.id_in_ready_i <<= io.id_in_ready_i
            insert_dummy_instr <<= dummy_instr_i.insert_dummy_instr_o
            dummy_instr_data <<= dummy_instr_i.dummy_instr_data_o

            #Mux between actual instructions and dummy instructions
            instr_out <<= Mux(insert_dummy_instr, dummy_instr_data,instr_decompressed)
            instr_is_compressed_out <<= Mux(insert_dummy_instr,U.w(1)(0),instr_is_compressed)
            illegal_c_instr_out <<= Mux(insert_dummy_instr,U.w(1)(0),illegal_c_insn)
            instr_err_out <<= Mux(insert_dummy_instr , U.w(1)(0),if_instr_err)

            # Stall the IF stage if we insert a dummy insert instruction . the dummy will execute between whatever
            # is currently in the ID stage and whatever is valid from the prefetch buffer this cycle .
            # the pc of the dummy instruction will match whatever is next from prefetch buffer

            stall_dummy_instr <<= insert_dummy_instr

            # Register the dummy instruction indication into the ID stage
            with when(Module.reset):
                io.dummy_instr_id_o <<= U.w(1)(0)
            with elsewhen(if_id_pipe_reg_we):
                io.dummy_instr_id_o <<= insert_dummy_instr
        else:
            unused_dummy_en = Wire(Bool)
            unused_dummy_mask = Wire(U.w(2))
            unused_dummy_seed_en = Wire(Bool)
            unused_dummy_seed = Wire(U.w(32))

            unused_dummy_en <<= io.dummy_instr_en_i
            unused_dummy_mask <<= io.dummy_instr_mask_i
            unused_dummy_seed_en <<= io.dummy_instr_seed_en_i
            unused_dummy_seed <<= io.dummy_instr_seed_i
            instr_out <<= instr_decompressed
            instr_is_compressed_out <<= instr_is_compressed
            illegal_c_instr_out <<= illegal_c_insn
            instr_err_out <<= if_instr_err
            stall_dummy_instr << U.w(1)(0)
            io.dummy_instr_id_o <<= U.w(1)(0)

        # The Id stage becomes valid as soon as any instruction is registered in the ID stage flops.
        # Note that the current instruction is aquahed by the incoming pc_set_i signal.
        # Valid is help until it is explicitly cleared (due to an instruction completing or an exception)

        instr_valid_id_d <<= (if_instr_valid & io.id_in_ready_i & ~io.pc_set_i) | (instr_valid_id_q & ~io.instr_valid_clear_i)
        instr_new_id_d <<= if_instr_valid & io.id_in_ready_i

        with when(Module.reset):
            instr_valid_id_q <<= U.w(1)(0)
            instr_new_id_d <<= U.w(1)(0)
        with otherwise:
            instr_valid_id_q <<= instr_new_id_d
            instr_new_id_q <<= instr_new_id_d

        io.instr_new_id_o <<= instr_valid_id_q

        #Signal when a new instruction enters the ID stage(only used for RVFI signalling)
        io.instr_new_id_o <<= instr_new_id_q

        #if-id pipeline registers ,frozen when the Id stage is stalled
        if_id_pipe_reg_we <<= instr_new_id_d

        with when(if_id_pipe_reg_we):
            io.instr_rdata_alu_id_o <<= instr_out

            # To reduce fan-out and help timing from the instr_rdata_id flops they are replicated
            io.instr_rdata_alu_id_o <<= instr_out
            io.instr_fetch_err_o <<= instr_err_out
            io.instr_fetch_err_plus2_o <<= fetch_err_plus2
            io.rdata_c_id_o <<= if_instr_rdata[15:0]
            io.instr_is_compressed_id_o <<= instr_is_compressed_out
            io.illegal_c_insn_id_o <<= illegal_c_instr_out
            io.pc_id_o <<= io.pc_if_o

        # check for expected increments of the pc when security hardening enabled
        if(PCIncrCheck):
            prev_instr_addr_incr = Wire(U.w(32))
            prev_instr_seq_q = Reg(Bool)
            prev_instr_seq_d = Reg(Bool)

            # Do not check for sequential increase after a branch , jump ,exception , interrupt, or debug
            # request, all of which will set branch_req. Also do not check after reset or for dummys
            prev_instr_seq_d <<= (prev_instr_seq_q | instr_new_id_d) & ~branch_req & ~stall_dummy_instr

            with when(Module.reset):
                prev_instr_seq_q <<= U.w(1)(0)
            with otherwise:
                prev_instr_seq_q <<= prev_instr_seq_d

            prev_instr_addr_incr <<= io.pc_id_o + Mux((io.instr_is_compressed_id_o & (~io.instr_fetch_err_o),U.w(32)(3),U.w(32)(4)))

            # Check that the address equals the previous address +2/+4
            io.pc_mismatch_alert_o = prev_instr_seq_q & (io.pc_if_o != prev_instr_addr_incr)

        else:
            io.pc_mismatch_alert_o = U.w(1)(0)

        if(BranchPredictor):
            instr_skid_data_q = Reg(U.w(32))
            instr_skid_addr_q = Reg(U.w(32))
            instr_skid_bp_taken_q = Reg(Bool)
            instr_skid_valid_q = Reg(Bool)
            instr_skid_valid_d = Reg(Bool)
            instr_skid_en = Reg(Bool)
            instr_bp_taken_q = Reg(Bool)
            instr_bp_taken_d = Reg(Bool)

            predict_branch_taken_raw = Wire(Bool)

            # ID stages needs to know if branch was predicted taken so it can signal mispredicts
            with when(if_id_pipe_reg_we):
                instr_bp_taken_q <<= instr_bp_taken_d

            # When branch prediction is enable a skid buffer between the IF and ID/EX stage is instroduced.
            # if an instruction in IF is predicted to be a taken branch and ID/EX is not ready the
            # instruction in IF is moved to the skid buffer which becomes output of the IF stage until
            # the ID/EX stage accepts the instruction. The skid buffer is required as otherwise the ID/EX
            # ready signal is coupled to the instr_req_o output which produces a feedthrough path from
            # data_gnt_i -> instr_req_o (which needs to be avoided as for some interconnects this will result in a combinational loop)

            instr_skid_en <<= predicted_branch & ~io.id_in_ready_i & ~instr_skid_valid_q
            instr_skid_valid_d <<= (instr_skid_valid_q & ~io.id_in_ready_i & ~stall_dummy_instr) | instr_skid_en

            with when(Module.reset):
                instr_skid_valid_q <<= U.w(1)(0)
            with otherwise:
                instr_skid_valid_q <<= instr_skid_valid_d

            with when(instr_skid_en):
                instr_skid_bp_taken_q <<= predict_branch_taken
                instr_skid_data_q <<= fetch_rdata
                instr_skid_addr_q <<= fetch_addr

            branch_predict_i = branch_predict().io
            branch_predict_i.fetch_rdata_i <<= fetch_rdata
            branch_predict_i.fetch_pc_i <<= fetch_addr
            branch_predict_i.fetch_valid_i <<= fetch_valid
            predict_branch_taken_raw <<= branch_predict_i.predict_branch_taken_o
            predict_branch_pc <<= branch_predict_i.predict_branch_pc_o

            # if there is an instruction in the skid buffer there must be no branch prediction
            # Instructions are only placed in the skid after they have been predicted to be a taken ranch
            # so with the skid valid any prediction has already occurred
            # Do not branch predict on instruction errors
            predict_branch_taken <<= predict_branch_taken_raw & ~instr_skid_valid_q & ~fetch_err

            # pc_set_i takes precendence over branch prediction
            predicted_branch <<= predict_branch_taken & ~io.pc_set_i

            if_instr_valid <<= fetch_valid | instr_skid_valid_q
            if_instr_rdata <<= Mux(instr_skid_valid_q,instr_skid_data_q,fetch_rdata)
            if_instr_addr  <<= Mux(instr_skid_valid_q,instr_skid_addr_q,fetch_addr)

            #Don`t branch predict on instruction error so only instructons without errors end up in the skid buffer
            if_instr_err <<= ~instr_skid_addr_q & fetch_err
            instr_bp_taken_d <<= Mux(instr_skid_valid_q, instr_skid_bp_taken_q, predict_branch_taken)

            fetch_ready <<= io.id_in_ready_i & ~stall_dummy_instr & ~instr_skid_valid_q
            io.instr_bp_taken_o <<= instr_bp_taken_q

            # `ASSERT(NoPredictSkid, instr_skid_valid_q |-> ~predict_branch_taken)
            # `ASSERT(NoPredictIllegal, predict_branch_taken |-> ~illegal_c_insn)

        else:
            io.instr_bp_taken <<= U.w(1)(0)
            predict_branch_taken <<= U.w(1)(0)
            predicted_branch <<= U.w(1)(0)
            predict_branch_pc <<= U.w(32)(0)

            if_instr_valid <<= fetch_valid
            if_instr_rdata <<= fetch_rdata
            if_instr_addr <<= fetch_addr
            if_instr_err <<= fetch_err
            fetch_ready <<= io.id_in_ready_i & ~stall_dummy_instr

        ########################
        ###### Assertions ######
        ########################

        # Selectors must be known/valid.
        # `ASSERT_KNOWN(IbexExcPcMuxKnown, exc_pc_mux_i)
