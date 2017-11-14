import unittest
from kpack_linux import CPU, Memory, Storage, Network, LinuxHost
from komlogd.api.model.metrics import Datasource, Datapoint, Anomaly

class InitTest(unittest.TestCase):

    def test_cpu_creation(self):
        ''' creating a CPU object should succeed '''
        root_uri = 'host.resources'
        my_cpu = CPU(root_uri)
        self.assertTrue(isinstance(my_cpu.info, Datasource))
        self.assertEqual(my_cpu.info.uri, '.'.join((root_uri, 'cpu')))
        self.assertTrue('user' in my_cpu.use_metrics)
        self.assertTrue('nice' in my_cpu.use_metrics)
        self.assertTrue('system' in my_cpu.use_metrics)
        self.assertTrue('steal' in my_cpu.use_metrics)
        self.assertTrue('iowait' in my_cpu.use_metrics)
        self.assertTrue('idle' in my_cpu.use_metrics)
        self.assertTrue('cpu_count' in my_cpu.use_metrics)
        self.assertTrue('t_runnable' in my_cpu.use_metrics)
        self.assertTrue('ldavg1' in my_cpu.use_metrics)
        self.assertEqual(my_cpu.use_metrics['user'], Datapoint('.'.join((my_cpu.info.uri,'all.user'))))
        self.assertEqual(my_cpu.use_metrics['nice'], Datapoint('.'.join((my_cpu.info.uri,'all.nice'))))
        self.assertEqual(my_cpu.use_metrics['system'], Datapoint('.'.join((my_cpu.info.uri,'all.system'))))
        self.assertEqual(my_cpu.use_metrics['steal'], Datapoint('.'.join((my_cpu.info.uri,'all.steal'))))
        self.assertEqual(my_cpu.use_metrics['iowait'], Datapoint('.'.join((my_cpu.info.uri,'all.iowait'))))
        self.assertEqual(my_cpu.use_metrics['idle'], Datapoint('.'.join((my_cpu.info.uri,'all.idle'))))
        self.assertEqual(my_cpu.use_metrics['cpu_count'], Datapoint('.'.join((my_cpu.info.uri,'cpu_count'))))
        self.assertEqual(my_cpu.use_metrics['t_runnable'], Datapoint('.'.join((my_cpu.info.uri,'tasks.runnable'))))
        self.assertEqual(my_cpu.use_metrics['ldavg1'], Datapoint('.'.join((my_cpu.info.uri,'ldavg.1min'))))
        self.assertEqual(len(my_cpu.tms),1)

    def test_memory_creation(self):
        ''' creating a Memory object should succeed '''
        root_uri = 'host.resources'
        my_mem = Memory(root_uri)
        self.assertTrue(isinstance(my_mem.info, Datasource))
        self.assertEqual(my_mem.info.uri, '.'.join((root_uri, 'memory')))
        self.assertTrue('memused' in my_mem.use_metrics)
        self.assertTrue('majflt' in my_mem.use_metrics)
        self.assertEqual(my_mem.use_metrics['memused'], Datapoint('.'.join((my_mem.info.uri,'memused'))))
        self.assertEqual(my_mem.use_metrics['majflt'], Datapoint('.'.join((my_mem.info.uri,'majflt'))))
        self.assertEqual(len(my_mem.tms),1)

    def test_storage_creation(self):
        ''' creating a Storage object should succeed '''
        root_uri = 'host.resources'
        my_st = Storage(root_uri)
        self.assertTrue(isinstance(my_st.info, Datasource))
        self.assertEqual(my_st.info.uri, '.'.join((root_uri, 'storage')))
        self.assertEqual(my_st._devs, [])
        self.assertEqual(my_st._fss, [])
        self.assertEqual(my_st.tms, [])

    def test_storage_creation(self):
        ''' creating a Storage object should succeed '''
        root_uri = 'host.resources'
        my_st = Storage(root_uri)
        self.assertTrue(isinstance(my_st.info, Datasource))
        self.assertEqual(my_st.info.uri, '.'.join((root_uri, 'storage')))
        self.assertEqual(my_st._devs, [])
        self.assertEqual(my_st._fss, [])
        self.assertEqual(my_st.tms, [])

    def test_network_creation(self):
        ''' creating a Network object should succeed '''
        root_uri = 'host.resources'
        my_net = Network(root_uri)
        self.assertTrue(isinstance(my_net.info, Datasource))
        self.assertEqual(my_net.info.uri, '.'.join((root_uri, 'network')))
        self.assertEqual(my_net._ifaces, [])
        self.assertEqual(my_net.tms, [])

    def test_linuxHost_creation(self):
        ''' creating a LinuxHost object should succeed '''
        base_uri = 'hosts.my_host'
        my_host = LinuxHost(base_uri=base_uri)
        self.assertEqual(my_host.res_uri, '.'.join((base_uri, 'system.resources')))
        self.assertEqual(len(my_host.resources),4)
        self.assertTrue(isinstance(my_host.resources[0], CPU))
        self.assertTrue(isinstance(my_host.resources[1], Memory))
        self.assertTrue(isinstance(my_host.resources[2], Storage))
        self.assertTrue(isinstance(my_host.resources[3], Network))
        self.assertEqual(my_host.resources[0].info, CPU(my_host.res_uri).info)
        self.assertEqual(my_host.resources[1].info, Memory(my_host.res_uri).info)
        self.assertEqual(my_host.resources[2].info, Storage(my_host.res_uri).info)
        self.assertEqual(my_host.resources[3].info, Network(my_host.res_uri).info)
        self.assertEqual(len(my_host.tms),1)

