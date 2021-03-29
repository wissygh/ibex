# /**
#  * Fetch Fifo for 32 bit memory interface
#  *
#  * input port: send address and data to the FIFO
#  * clear_i clears the FIFO for the following cycle, including any new request
#  */

from pyhcl import *


def fetch_fifo(
        # 函数参数
):
    class FETCH_FIFO(Module):
        # 本地参数

        io = IO(
            # io端口

        )
