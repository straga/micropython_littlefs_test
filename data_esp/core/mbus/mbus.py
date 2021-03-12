# Copyright (c) 2020 Viktor Vorobjov
from core.tools.tool import launch, is_coro
from core.tools.tool import DataClassArg

try:
    import uasyncio as asyncio
except Exception:
    import asyncio as asyncio
    pass

from core import logging
log = logging.getLogger("MBUS")


class RpcEnv:
    def __init__(self, core):
        self.core = core

    @staticmethod
    def isgenerator(iterable):
        return hasattr(iterable, '__iter__') and not hasattr(iterable, '__len__')

    class IsClass(object):
        pass


    '''
    Search method or arg in env by nema and path
    env_name = "mqtt"
    path = "client.status" / disconect
    '''
    def path(self, env_name, path):
        env_call = self.core.env.get(env_name)
        for _attr in path.split("."):
            if len(_attr):
                env_call = getattr(env_call, _attr)
        return env_call


    '''
    call path, check callable/asyncio_coro or return arg value
    '''
    @staticmethod
    async def call(path,  *args, **kwargs):
        if callable(path):
            call_func = path(*args, **kwargs)
            if is_coro(call_func):
                path = await call_func
            else:
                path = call_func
        return path


    '''
    Call from env and path some and return result
    '''
    async def action(self, env_name, path, args, kwargs, will_yield=False):

        path = self.path(env_name, path)
        result = await self.call(path, *args, **kwargs)
        if result and will_yield and self.isgenerator(result):
            return list(result)
        return result


    '''
    Return List(State) of env/path
    '''
    def state(self, env_name, path="", attr=None):
        path = self.path(env_name, path)
        state = {}
        for k in attr:
            val = getattr(path, k, None)
            if isinstance(val, (float, int, str, list, tuple)):
                state[k] = val
            else:
                state[k] = type(val).__name__

        return state


class MbusManager:

    def __init__(self):
        self.msub = []
        self.sub_id = 0
        self.rpc = None

    def activate(self, core):
        self.rpc = RpcEnv(core)

    # SUB
    def next_sub_id(self):
        self.sub_id += 1
        return self.sub_id

    @staticmethod
    def proto_subs(topic, sub_id, env, func):
        proto = DataClassArg(topic=topic, sub_id=sub_id, env=env, func=func)
        return proto

    def sub_h(self, topic, env, func):
        sub_id = self.next_sub_id()
        sub_data = self.proto_subs(topic=topic, sub_id=sub_id, env=env, func=func)
        self.msub.append(sub_data)
        return sub_id

    def usub(self, sub_id):
        search_subs = filter(lambda x: x.sub_id == sub_id, self.msub)
        for sub in search_subs:
            self.msub.remove(sub)

    # PUB
    @staticmethod
    def proto_msg(topic, payload, **properties):
        return DataClassArg(topic=topic, payload=payload, properties=properties)


    def pub_h(self, topic, payload, **properties):
        pub_data = self.proto_msg(topic=topic, payload=payload, **properties)
        launch(self.event_msg, pub_data)


    # Event
    async def event_msg(self, data):

        # log.debug("      ")
        log.debug("[PUB MSG]: tpc: {}, pld:{}".format(data.topic, data.payload))

        # Split topic, detect for subtopic subscripbe
        pub_topic_split = data.topic.rsplit("/", 1)

        pub_topic = pub_topic_split[0]
        pub_key = pub_topic_split[-1]
        # log.debug("Pub: {}, key: {}".format(pub_topic, pub_key))

        msg_topic = None
        if len(pub_topic_split) > 1:
            msg_topic = pub_topic

        for sub in list(filter(lambda x: x.topic.rsplit("/#", 1)[0] in pub_topic, self.msub)):

            log.debug("  sub Env: {}".format(sub.env))

            data.topic = msg_topic
            data.key = pub_key

            try:
                method = self.rpc.path(env_name=sub.env, path=sub.func)
                launch(method, data)
            except Exception as e:
                log.error("  Error: call_back: {} - {}".format(sub.func, e))
                pass
