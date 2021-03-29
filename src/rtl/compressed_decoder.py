# /**
#  * Compressed instruction decoder
#  *
#  * Decodes RISC-V compressed instructions into their RV32 equivalent.
#  * This module is fully combinatorial, clock and reset are used for
#  * assertions only.
#  */

from pyhcl import *


def compressed_decoder(
#函数参数
):
    class COMPRESSED_DECODER(Module):
        #本地参数

        io = IO(
        #io端口

        )
