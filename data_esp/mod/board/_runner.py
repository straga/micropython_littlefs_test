from core import logging
log = logging.getLogger("BOARD")


try:
    import ubinascii
except Exception:
    import binascii as ubinascii


import machine
from core.loader.loader import uLoad
from core.u_os import uname, mem_info
from esp32 import Partition


class BoardAction(uLoad):

    async def _activate(self):

        _mod = await self.uconf.call("select_one", "board_cfg", "default", True)

        if _mod:
            # BOARD ID
            self.board_id = ubinascii.hexlify(machine.unique_id()).decode()
            log.info("BOARD ID: {}".format(self.board_id))

            _mod.uid = self.board_id

            await _mod.update()

            self.board = _mod
            self.core.board = self.board


# class BoardEnv():


    @staticmethod
    def reboot(part=None):
        if part:
            _part = Partition(part)
            Partition.set_boot(_part)
        machine.reset()


    @property
    def uname(self):
        return uname()

    @property
    def mem_info(self):
        return mem_info()

    @property
    def part(self):
        runningpart = Partition(Partition.RUNNING)
        part_info = runningpart.info()
        part_name = part_info[4]
        return part_name


