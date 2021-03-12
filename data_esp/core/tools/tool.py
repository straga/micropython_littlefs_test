
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


from core import logging
log = logging.getLogger("CORE")

def call_try(elog=log.error):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args,**kwargs)
            except Exception as e:
                elog("error: {}".format(e))
                pass
        return applicator
    return decorate


call_try_error = call_try()
call_try_debug = call_try(log.debug)
call_try_info = call_try(log.info)


@call_try_error
def encode_UTF8(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return data


@call_try_error
def decode_UTF8(data):
    if not isinstance(data, str):
        data = data.decode('utf-8')
    return data



class DataClassArg():

    def __init__(self, *args, **kwargs):

        for key in args:
            setattr(self, key, None)

        for key in kwargs:
            setattr(self, key, kwargs[key])


    def a_dict(self):
        return self.__dict__




async def _g():
    pass
type_coro = type(_g())


def is_coro(func):
    if isinstance(func, type_coro):
        return True
    return False



def launch(func, *args, loop=None, **kwargs):
    try:
        res = func(*args, **kwargs)
        if isinstance(res, type_coro):
            if not loop:
                loop = asyncio.get_event_loop()
            loop.create_task(res)
    except Exception as e:
        print(e)
        pass







