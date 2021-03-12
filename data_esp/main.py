
import uasyncio as asyncio
import machine, _thread
import uos
import gc

from core import logging

log = logging.getLogger('MAIN')
logging.basicConfig(level=logging.INFO)

# WDT
async def run_wdt():
    wdt = machine.WDT(timeout=120000)
    print("WDT RUN")
    while True:
        wdt.feed()
        # gc.collect()
        print("WDT RESET")
        await asyncio.sleep(30)

# Core
def core():
    from core.core import uCore
    from core.mbus.mbus import MbusManager
    from core.config.config import ConfigManager

    # VFS SIZE
    fs_stat = uos.statvfs('/')
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    print("File System Size {:,} - Free Space {:,}".format(fs_size, fs_free))

    part_name = uos.getcwd()
    print(part_name)

    # MBUS
    log.info("MBUS START")
    _mbus = MbusManager()

    # CONF
    log.info("CONF START")
    _conf = ConfigManager("./u_config")

    # CORE
    log.info("CORE: init")
    _core = uCore(_mbus, _conf)
    _core.part_name = part_name

# Lloader
async def loader():

    from core.loader.loader import uLoader

    log.info("Module: Init")
    _umod = uLoader()

    log.info("Module: List")
    await _umod.module_list()

    log.info("Module: Act")
    await _umod.module_act()


def main():

    # Activate Core
    core()

    # AsyncIO in thread
    loop = asyncio.get_event_loop()
    _ = _thread.stack_size(8 * 1024)
    _thread.start_new_thread(loop.run_forever, ())

    # Run Loader Task
    loop.create_task(run_wdt())
    loop.create_task(loader())



if __name__ == '__main__':

    print("MAIN")

    from core import logging
    log = logging.getLogger("FJSON")
    log.setLevel(logging.DEBUG)

    main()

    #if error - run manualy in UART:
    # import network
    # sta = network.WLAN(network.STA_IF)
    # sta.active(True)
    # sta.connect("ssid", "psswd")
    #
    # import uftpd


    # from esp32 import Partition
    # ota_0 = Partition('ota_0')
    # Partition.set_boot(ota_0)

    # import _thread
    # _thread.stack_size(4 * 1024)

    # change file syste to vfat
    # import uos
    # from flashbdev import bdev
    # uos.VfsLfs2.mkfs(bdev) #littlefs
    # uos.VfsFat.mkfs(bdev) #fat





