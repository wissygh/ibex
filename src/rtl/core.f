ibex_pkg.py
ibex_alu.py
ibex_compressed_decoder.py
ibex_controller.py
ibex_counter.py
ibex_cs_registers.py
ibex_decoder.py
ibex_ex_block.py
ibex_id_stage.py
ibex_if_stage.py
ibex_load_store_unit.py
ibex_multdiv_slow.py
ibex_multdiv_fast.py
ibex_prefetch_buffer.py
ibex_fetch_fifo.py
ibex_register_file_ff.py
ibex_core.py




ibex_core_tracing
tracer_pkg
tracer

core:
    pkg


    if_stage:                (over)
        ichace
        prefetch_buffer:
            fetch_fifo
        compressed_decoder    (over)
        dummy_instr           (over)
        branch_predict        (over)

    id_stage:
        decoder
        controller

    ex_block:
        alu
        ibex_multdiv_slow
        ibex_multdiv_fast

    Load/store:
        ibex_load_store_unit
        ibex_wb_stage(writeback)

    ibex_register_file ECC:
        ibex_register_file_ff
        ibex_register_file_fpga
        ibex_register_file_latch

    CSRs (Control and Status Registers):
        ibex_cs_registers
            ibex_csr
            ibex_counter
        ibex_pmp


传
$ git add .
$ git commit -m ":memo: update"
$ git push -u origin dev
取
 在PC-1上获取PC-2更新的内容:
  git pull origin master        #将服务器端的代码下载到本地