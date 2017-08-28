import asyncio
import socket
from kpack_linux import settings
from komlogd.base import logging
from komlogd.api.transfer_methods import transfermethod
from komlogd.api.model.metrics import Datasource
from komlogd.api.model.schedules import CronSchedule

class LinuxHost:

    def __init__(self, base_uri):
        self.base_uri = base_uri
        self._cpu_cmd = """top -b -n 2 | awk 'BEGIN {RS=""} FNR == 3 {print}'"""
        self._mem_cmd = "cat /proc/meminfo"
        self._disk_cmd = "df -k"
        self.tms = [
            transfermethod(f=self.check_cpu,schedule=settings.CPU_SCHED),
            transfermethod(f=self.check_mem,schedule=settings.MEM_SCHED),
            transfermethod(f=self.check_disk,schedule=settings.DISK_SCHED)
        ]
        for tm in self.tms:
            tm.bind()

    async def _run_cmd(self, cmd):
        try:
            p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr = asyncio.subprocess.PIPE)
            output = await p.stdout.read()
        except Exception as e:
            logging.logger.error('Exception running command.')
            logging.logger.error(str(e))
            return None
        else:
            await p.wait()
            content = output.decode('utf-8')
            return content

    async def check_cpu(self, t):
        content = await self._run_cmd(self._cpu_cmd)
        if content:
            uri = '.'.join((self.base_uri,'system.cpu'))
            metric = Datasource(uri=uri)
            metric.insert(t=t, value=content)

    async def check_mem(self, t):
        content = await self._run_cmd(self._mem_cmd)
        if content:
            uri = '.'.join((self.base_uri,'system.mem'))
            metric = Datasource(uri=uri)
            metric.insert(t=t, value=content)

    async def check_disk(self, t):
        content = await self._run_cmd(self._disk_cmd)
        if content:
            uri = '.'.join((self.base_uri,'system.disk'))
            metric = Datasource(uri=uri)
            metric.insert(t=t, value=content)

