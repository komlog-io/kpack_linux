import asyncio
import re
from kpack_linux import settings
from komlogd.base import logging
from komlogd.api.transfer_methods import transfermethod
from komlogd.api.model.metrics import Datasource, Datapoint, Anomaly
from komlogd.api.model.schedules import OnUpdateSchedule
from komlogd.api.protocol import validation

async def run_cmd(cmd):
    try:
        p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr = asyncio.subprocess.PIPE)
        stdout = await p.stdout.read()
        stderr = await p.stderr.read()
    except Exception as e:
        logging.logger.error('Exception running command.')
        logging.logger.error(str(e))
        return None
    else:
        await p.wait()
        content = stdout.decode('utf-8')
        error = stderr.decode('utf-8')
        if not content and error:
            logging.logger.error('Error running command.')
            logging.logger.error(error)
        return content

def get_margin(lines):
    margin = -1
    for line in lines:
        for item in re.finditer('\w+',line):
            start = item.start()
            if start>0:
                if start < margin or margin == -1:
                    margin = start
                break
    return margin

class CPU:

    def __init__(self, root_uri):
        self.info = Datasource(
            uri = '.'.join((root_uri,'cpu')),
            supplies = ['ldavg.1min','ldavg.5min','ldavg.15min','cpu_count','all.user','all.nice','all.system','all.iowait','all.steal','all.idle','tasks.runnable','tasks.total','tasks.blocked']
        )
        self.use_metrics= {
            'user':Datapoint('.'.join((self.info.uri,'all.user'))),
            'nice':Datapoint('.'.join((self.info.uri,'all.nice'))),
            'system':Datapoint('.'.join((self.info.uri,'all.system'))),
            'steal':Datapoint('.'.join((self.info.uri,'all.steal'))),
            'iowait':Datapoint('.'.join((self.info.uri,'all.iowait'))),
            'idle':Datapoint('.'.join((self.info.uri,'all.idle'))),
            'cpu_count':Datapoint('.'.join((self.info.uri,'cpu_count'))),
            't_runnable':Datapoint('.'.join((self.info.uri,'tasks.runnable'))),
            'ldavg1':Datapoint('.'.join((self.info.uri,'ldavg.1min')))
        }

        self.tms = [
            transfermethod(f=self.check_anom, schedule=OnUpdateSchedule(activation_metrics=self.use_metrics)),
        ]

    async def load(self):
        for tm in self.tms:
            await tm.bind()

    async def update(self, t, content):
        if not content:
            return
        cpu_block = False
        load_block = False
        header = ''
        cpu_block_lines = []
        load_block_lines = []
        for i,line in enumerate(content.split('\n')):
            fields = line.split()
            if len(fields) > 1:
                if fields[0].count(':') == 0:
                    # this should be the header with kernel information
                    header = line
                elif fields[0].count(':') == 1:
                    # this should be a resume or average line
                    if (fields[1] == 'CPU' and fields[2] == '%user') or cpu_block:
                        cpu_block = True
                        load_block = False
                        cpu_block_lines.append(line)
                    elif fields[1] == 'runq-sz' or load_block:
                        load_block = True
                        cpu_block = False
                        load_block_lines.append(line)
            else:
                cpu_block = False
                load_block = False
        if header and (cpu_block_lines or load_block_lines):
            value = header+'\n\n'
            for block in [cpu_block_lines, load_block_lines]:
                margin = get_margin(block)
                if margin > -1:
                    for line in block:
                        value += line[margin:]+'\n'
                    value += '\n'
            self.info.insert(t=t, value=value)

    async def check_anom(self, t):
        user = await self.use_metrics['user'].get(t=t)
        system = await self.use_metrics['system'].get(t=t)
        steal = await self.use_metrics['steal'].get(t=t)
        nice = await self.use_metrics['nice'].get(t=t)
        cpu_count = await self.use_metrics['cpu_count'].get(t=t)
        t_runnable = await self.use_metrics['t_runnable'].get(t=t)
        ldavg1 = await self.use_metrics['ldavg1'].get(t=t)
        use = user + system + steal + nice
        sat_sz = t_runnable / cpu_count
        sat_ld = ldavg1 / cpu_count
        if use is None and (sat_sz is None or sat_ld is None):
            return
        elif use is not None and use[0] > 90:
            anom_metric = Anomaly(metric=self.info)
            anom_metric.insert(t=t, value=1)
        elif sat_sz is not None and sat_ld is not None and sat_sz[0] > 1 and sat_ld[0] > 1:
            anom_metric = Anomaly(metric=self.info)
            anom_metric.insert(t=t, value=1)
        else:
            anom_metric = Anomaly(metric=self.info)
            anom_metric.insert(t=t, value=0)

class Memory:

    def __init__(self, root_uri):
        self.info = Datasource(
            uri='.'.join((root_uri,'memory')),
            supplies = ['pswpin','pswpout','pgpgin','pgpgout','fault','majflt','pgfree','pgscank','pgscand','pgsteal','vmeff','kbmemfree','kbmemused','memused','kbbuffers','kbcached','kbcommit','commit','kbactive','kbinact','kbdirty']
        )
        self.use_metrics= {
            'memused':Datapoint('.'.join((self.info.uri,'memused'))),
            'majflt':Datapoint('.'.join((self.info.uri,'majflt')))
        }

        self.tms = [
            transfermethod(f=self.check_anom, schedule=OnUpdateSchedule(activation_metrics=self.use_metrics)),
        ]

    async def load(self):
        for tm in self.tms:
            await tm.bind()

    async def update(self, t, content):
        if not content:
            return
        swp_block = False
        pg_block = False
        mem_block = False
        swp_block_lines = []
        pg_block_lines = []
        mem_block_lines = []
        for i,line in enumerate(content.split('\n')):
            fields = line.split()
            if len(fields) > 1:
                if fields[0].count(':') == 1:
                    # this should be a resume or average line
                    if fields[1] == 'pswpin/s' or swp_block:
                        swp_block = True
                        pg_block = False
                        mem_block = False
                        swp_block_lines.append(line)
                    elif fields[1] == 'pgpgin/s' or pg_block:
                        swp_block = False
                        pg_block = True
                        mem_block = False
                        pg_block_lines.append(line)
                    elif fields[1] == 'kbmemfree' or mem_block:
                        swp_block = False
                        pg_block = False
                        mem_block = True
                        mem_block_lines.append(line)
            else:
                swp_block = False
                pg_block = False
                mem_block = False
        if swp_block_lines or pg_block_lines or mem_block_lines:
            value = ''
            for block in [mem_block_lines, swp_block_lines, pg_block_lines]:
                margin = get_margin(block)
                if margin > -1:
                    for line in block:
                        value += line[margin:]+'\n'
                    value += '\n'
            self.info.insert(t=t, value=value)

    async def check_anom(self, t):
        memused = await self.use_metrics['memused'].get(t=t)
        majflt = await self.use_metrics['majflt'].get(t=t)
        if memused is None and majflt is None:
            return
        elif memused is not None and memused[0] > 85:
            anom_metric = Anomaly(metric=self.info)
            anom_metric.insert(t=t, value=1)
        elif majflt is not None and majflt[0] > 100:
            anom_metric = Anomaly(metric=self.info)
            anom_metric.insert(t=t, value=1)
        else:
            anom_metric = Anomaly(metric=self.info)
            anom_metric.insert(t=t, value=0)

class Storage:
    _dev_metrics = ['tps','rd_sec','wr_sec','avgrq-sz','avgqu-sz','await','svctm','util']
    _fs_metrics = ['MBfsfree', 'MBfsused', 'fsused', 'ufsused', 'Ifree', 'Iused', 'pIused']

    def __init__(self, root_uri):
        self.info = Datasource(
            uri='.'.join((root_uri,'storage')),
            supplies = []
        )
        self._devs = []
        self._fss = []
        self.tms = []

    async def load(self):
        for tm in self.tms:
            await tm.bind()

    async def update(self, t, content):
        if not content:
            return
        dev_block = False
        fs_block = False
        dev_block_lines = []
        fs_block_lines = []
        for i,line in enumerate(content.split('\n')):
            fields = line.split()
            if len(fields) > 1:
                if fields[0].count(':') == 1:
                    # this should be a resume or average line
                    if fields[1] == 'DEV' or dev_block:
                        dev_block = True
                        fs_block = False
                        dev_block_lines.append(line)
                    elif fields[-1] == 'FILESYSTEM' or fs_block:
                        dev_block = False
                        fs_block = True
                        fs_block_lines.append(line)
            else:
                dev_block = False
                fs_block = False
        if dev_block_lines or fs_block_lines:
            value = ''
            for block in [dev_block_lines, fs_block_lines]:
                margin = get_margin(block)
                if margin > -1:
                    for line in block:
                        value += line[margin:]+'\n'
                    value += '\n'
            await self.find_missing(value)
            self.info.insert(t=t, value=value)

    async def find_missing(self, content):
        devs = []
        fss = []
        dev_block = False
        fs_block = False
        for line in content.split('\n'):
            fields = line.split()
            if dev_block and fields:
                dev_name = fields[0]
                final_name = ''
                for i,c in enumerate(dev_name):
                    if validation.is_local_uri(c):
                        final_name += c
                    elif i>0:
                        final_name += '_'
                if validation.is_local_uri(final_name):
                    devs.append(final_name)
            elif fs_block and fields:
                fs_name = fields[-1]
                final_name = ''
                for i,c in enumerate(fs_name):
                    if validation.is_local_uri(c):
                        final_name += c
                    elif i>0:
                        final_name += '_'
                if validation.is_local_uri(final_name):
                    fss.append(final_name)
            else:
                dev_block = False
                fs_block = False
                if fields and fields[0][0] == 'D':
                    dev_block = True
                elif fields and fields[0][0:2] == 'MB':
                    fs_block = True
        for dev in devs:
            if not dev in self._devs:
                logging.logger.debug('New device found: '+dev)
                self._devs.append(dev)
                for m in self._dev_metrics:
                    self.info.supplies.append('.'.join((dev,m)))
                f_params = {
                    'util':Datapoint(uri='.'.join((self.info.uri,dev,'util')))
                }
                tm = transfermethod(f=self.check_anom_dev, f_params=f_params)
                await tm.bind()
                self.tms.append(tm)
        for fs in fss:
            if not fs in self._fss:
                logging.logger.debug('New filesystem found: '+fs)
                self._fss.append(fs)
                for m in self._fs_metrics:
                    self.info.supplies.append('.'.join((fs,m)))
                f_params = {
                    'fsused':Datapoint(uri='.'.join((self.info.uri,fs,'fsused'))),
                    'ufsused':Datapoint(uri='.'.join((self.info.uri,fs,'ufsused'))),
                    'pIused':Datapoint(uri='.'.join((self.info.uri,fs,'pIused')))
                }
                tm = transfermethod(f=self.check_anom_fs, f_params=f_params)
                await tm.bind()
                self.tms.append(tm)

    async def check_anom_dev(self, t, util):
        util_s = await util.get(end=t, count=2)
        if util_s is not None:
            anom = Anomaly(util)
            if util_s[0] > 80:
                # set anomaly signal to 1
                anom.insert(t=t, value=1)
            elif len(util_s)==2 and util_s.index[-1] < t and util_s[-1] > 80:
                # cancel previously set anomaly
                anom.insert(t=t, value=0)

    async def check_anom_fs(self, t, fsused, ufsused, pIused):
        fsused_s = await fsused.get(end=t, count=2)
        ufsused_s = await ufsused.get(end=t, count=2)
        pIused_s = await pIused.get(end=t, count=2)
        if fsused_s is None and ufsused_s is None and pIused_s is None:
            return
        elif fsused_s is not None and fsused_s.index[0] == t:
            if fsused_s[0] > 80:
                fsused_anom = Anomaly(fsused)
                fsused_anom.insert(t=t, value=1)
            elif len(fsused_s) == 2 and fsused_s[-1] > 80:
                fsused_anom.insert(t=t, value=0)
        elif ufsused_s is not None and ufsused_s.index[0] == t:
            if ufsused_s[0] > 80:
                ufsused_anom = Anomaly(ufsused)
                ufsused_anom.insert(t=t, value=1)
            elif len(ufsused_s) == 2 and ufsused_s[-1] > 80:
                ufsused_anom.insert(t=t, value=0)
        elif pIused_s is not None and pIused_s.index[0] == t:
            if pIused_s[0] > 80:
                pIused_anom = Anomaly(pIused)
                pIused_anom.insert(t=t, value=1)
            elif len(pIused_s) == 2 and pIused_s[-1] > 80:
                pIused_anom.insert(t=t, value=0)

class Network:
    _iface_metrics = ['rxpck','txpck','rxkB','txkB','rxcmp','txcmp','rxmcst','ifutil','rxerr','txerr','coll','rxdrop','txdrop','txcarr','rxfram','rxfifo','txfifo']

    def __init__(self, root_uri):
        self.info = Datasource(
            uri='.'.join((root_uri,'network')),
            supplies = []
        )
        self._ifaces = []
        self.tms = []

    async def load(self):
        for tm in self.tms:
            await tm.bind()

    async def update(self, t, content):
        if not content:
            return
        tr_block = False
        err_block = False
        tr_block_lines = []
        err_block_lines = []
        for i,line in enumerate(content.split('\n')):
            fields = line.split()
            if len(fields) > 1:
                if fields[0].count(':') == 1:
                    # this should be a resume or average line
                    if (fields[1] == 'IFACE' and fields[2] == 'rxpck/s') or tr_block:
                        tr_block = True
                        err_block = False
                        tr_block_lines.append(line)
                    elif (fields[1] == 'IFACE' and fields[2] == 'rxerr/s') or err_block:
                        tr_block = False
                        err_block = True
                        err_block_lines.append(line)
            else:
                tr_block = False
                err_block = False
        if tr_block_lines or err_block_lines:
            value = ''
            for block in [tr_block_lines, err_block_lines]:
                margin = get_margin(block)
                if margin > -1:
                    for line in block:
                        value += line[margin:]+'\n'
                    value += '\n'
            await self.find_missing(value)
            self.info.insert(t=t, value=value)

    async def find_missing(self, content):
        ifaces = []
        iface_block = False
        for line in content.split('\n'):
            fields = line.split()
            if iface_block and fields:
                iface_name = fields[0]
                final_name = ''
                for i,c in enumerate(iface_name):
                    if validation.is_local_uri(c):
                        final_name += c
                    elif i>0:
                        final_name += '_'
                if validation.is_local_uri(final_name):
                    ifaces.append(final_name)
            else:
                iface_block = False
                if fields and fields[0] == 'IFACE':
                    iface_block = True
        for iface in ifaces:
            if not iface in self._ifaces:
                logging.logger.debug('New network interface found: '+iface)
                self._ifaces.append(iface)
                for m in self._iface_metrics:
                    self.info.supplies.append('.'.join((iface,m)))
                f_params = {
                    'ifutil':Datapoint(uri='.'.join((self.info.uri,iface,'ifutil')))
                }
                tm = transfermethod(f=self.check_anom, f_params=f_params)
                await tm.bind()
                self.tms.append(tm)

    async def check_anom(self, t, ifutil):
        ifutil_s = await ifutil.get(end=t, count=2)
        if ifutil_s is not None:
            anom = Anomaly(ifutil)
            if ifutil_s[0] > 80:
                # set anomaly signal
                anom.insert(t=t, value=1)
            elif len(ifutil_s) == 2 and ifutil_s.index[1] < t and ifutil_s[1] > 80:
                # cancel previously set anomaly
                anom.insert(t=t, value=0)

class LinuxHost:
    _cmd = 'sar -BWrdFqu -n DEV,EDEV 2 1'

    def __init__(self, base_uri, ssh_cmd=None):
        self.res_uri = '.'.join((base_uri,'system.resources'))

        self.resources = [
            CPU(self.res_uri),
            Memory(self.res_uri),
            Storage(self.res_uri),
            Network(self.res_uri),
        ]

        if ssh_cmd:
            self._cmd = ' '.join((ssh_cmd,self._cmd))

        self.tms = [
            transfermethod(f=self.check, schedule=settings.SCHED)
        ]

    async def load(self):
        for tm in self.tms:
            await tm.bind()
        for res in self.resources:
            await res.load()


    async def check(self, t):
        content = await run_cmd(self._cmd)
        if content:
            for res in self.resources:
                await res.update(t, content)


