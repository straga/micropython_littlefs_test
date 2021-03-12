

from core.core import uCore
import gc

from core import logging
log = logging.getLogger("LOADER")

import sys
from core.tools.tool import launch


try:
    import uasyncio as asyncio
except Exception:
    import asyncio as asyncio


class uAction:
    def __init__(self, env, module):

        self.core = uCore.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf
        self.env = env
        self.module = module
        self.depend = module.depend
        self.wait_depend = None
        launch(self.start)

    # Humanize sub to topic
    def sub_h(self, topic, func):
        return self.mbus.sub_h(topic=topic, env=self.env, func=func)

    async def start(self):
        log.info("")

        # Load Data
        await self.uconf.call("from_file", "./_conf/data_{}.json".format(self.module.env))
        log.info("MOD: {} : Data <- _conf  ".format(self.module.env))

        await self.uconf.call("from_file", "./mod/{}/_data.json".format(self.module.env))
        log.info("MOD: {} : Data <-  mod".format(self.module.env))

        # Wait dependence if exist.
        if self.depend:
            self.wait_depend = self.sub_h(topic="module/#", func="_wait_depend")
        log.info("MOD: {} : Wait = {}".format(self.module.env, self.depend))

        # gc.collect()
        # log.info("{} - RAM free: {}, Done".format(self.env, gc.mem_alloc()))
        launch(self.run)

    async def run(self):
        log.info("MOD: Run: {}".format(self.env))
        if not self.depend:
            launch(self.reg_module)

    def _wait_depend(self, msg):
        log.debug(" Module ({}) - wait {}: <- Loaded: {}".format(self.env, self.depend, msg.payload))
        # Remove dependence adter loaded
        if msg.payload in self.depend:
            self.depend.remove(msg.payload)

        # No more dependece: unsubscribe
        if not self.depend and self.wait_depend:
            self.mbus.usub(self.wait_depend)
            launch(self.reg_module)

    def done(self):
        del self.core.env[self.env]
        log.info("MOD: Loaded: {}".format(self.env))

    async def reg_module(self):
        try:
            await self.module._activate()
        except Exception as e:
            log.error("Reg: {} - : {}".format(self.module, e))
        pass

        self.mbus.pub_h("module", self.module.env)
        self.done()


class uLoad:
    def __init__(self, env, depend):
        self.core = uCore.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf
        self.env = env
        self.depend = depend
        # log.info("{} - RAM free: {}, Done".format(self.env, gc.mem_alloc()))

    # Humanize sub to topic
    def sub_h(self, topic, func):
        return self.mbus.sub_h(topic=topic, env=self.env, func=func)

    async def _activate(self):
        pass


class uLoader:

    __slots__ = ('mbus', 'uconf', 'core', '_modules')

    def __init__(self):

        self.core = uCore.get_core()
        self.mbus = self.core.mbus
        self.uconf = self.core.uconf

        _schema = '''{
            "data": {
                "_schema": "_schema",
                "name": "_module",
                "sch": [
                    ["name", ["str", ""]],
                    ["active", ["bool", true]],
                    ["depend", ["list", []]],
                    ["status", ["str", ""]]
                ]
            }
        }
        '''
        self.uconf.from_string(_schema)


    # 1. Load/Update module list from config to store
    async def module_list(self):
        await self.uconf.call("from_file", "./_conf/_mod.json")

    # 2. Activate modules
    async def module_act(self):
        _modules = []
        # Get list of modules
        _mod_list = await self.uconf.call("scan_name", "_module")
        log.info("Modules: {}".format(_mod_list))

        # Select active module
        log.info("-")
        for name_mod in _mod_list:
            _mod = await self.uconf.call("select_one", "_module", name_mod, True)
            a_info = ""
            if _mod and _mod.active:
                a_info = "{} : {}".format(_mod.active, _mod.name)
                _modules.append(_mod.name)
            log.info("Active: {}".format(a_info))

        # Activate data schema for each module
        log.info("-")
        for _mod in _modules:
            m_path = "mod.{}._act_mod".format(_mod)
            mod_schema = None
            result = True
            try:
                mod_schema = __import__(m_path, None, None, ["_act_mod"], 0)._schema
                del sys.modules[m_path]
            except Exception as e:
                result = e
                pass

            if mod_schema:
                await self.uconf.call("from_string", mod_schema)

            log.info("Sch: {} path: {}, result: {} ".format(_mod, m_path, result))

        # Garbage
        gc.collect()

        # Init module from active list
        log.info("-")
        for _mod in _modules:
            log.info("Init: {}".format(_mod))
            m_path = "mod.{}._act_mod".format(_mod)
            try:
                module_name   = __import__(m_path, None, None, ["_act_mod"], 0)._name
                module_action = __import__(m_path, None, None, ["_act_mod"], 0)._action
                module_depend = __import__(m_path, None, None, ["_act_mod"], 0)._depend
                del sys.modules[m_path]
                self.core.env_set(module_name, module_action, module_depend)
            except Exception as e:
                log.error("Init: {} - : {}".format(_mod, e))
                pass

        # Garbage
        gc.collect()

        # Activate module from active list
        log.info("-")
        for name in list(self.core.env):
            # if not name.startswith("_"):
            try:
                self.core.env_set("_{}".format(name), uAction, self.core.env.get(name))
            except Exception as e:
                log.error("Action: {} - : {}".format(name, e))
                pass


