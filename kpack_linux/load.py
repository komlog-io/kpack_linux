import asyncio
from kpack_linux import LinuxHost, settings

my_host = LinuxHost(settings.BASE_URI)
asyncio.ensure_future(my_host.load())
