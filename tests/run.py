import logging
import unittest
from time import sleep
from utils import Pool
from multiprocessing import Process
from zatt.client import DistributedDict
from zatt.client.clientProcess import ClientProcess
from zatt.server.config import Config
from zatt.server.logger import start_logger

logger = logging.getLogger(__name__)
config_file = "../zatt.conf"

class BasicAppendTest(unittest.TestCase):
    def setUp(self):
        self.pool = Pool(4, config_file)
        self.pool.start(self.pool.ids)
        self.client_pool = ClientProcess(3, config_file)
        self.client_pool.start(self.client_pool.ids)
        sleep(1)

    def tearDown(self):
        self.pool.stop(self.pool.ids)
        self.pool.rm(self.pool.ids)
        self.client_pool.stop(self.client_pool.ids)

    def test_append_read_same(self):
        print('Append test - Read Same')
        d = DistributedDict('127.0.0.1', 9116)
        d['adams'] = 'the hitchhiker guide'
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        del d

    def test_append_read_different(self):
        print('Append test - Read Different')
        d = DistributedDict('127.0.0.1', 9116)
        d['adams'] = 'the hitchhiker guide'
        del d
        d = DistributedDict('127.0.0.1', 9117)
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        del d
        d = DistributedDict('127.0.0.1', 9118)
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        del d

    def test_append_write_multiple(self):
        print('Append test - Write Multiple')
        d0 = DistributedDict('127.0.0.1', 9116)
        d1 = DistributedDict('127.0.0.1', 9117)
        d2 = DistributedDict('127.0.0.1', 9118)
        d0['0'] = '0'
        d1['1'] = '1'
        d2['2'] = '2'
        self.assertEqual(d1['0'], '0')
        self.assertEqual(d2['1'], '1')
        self.assertEqual(d0['2'], '2')
        del d0
        del d1
        del d2

    def test_delete_simple(self):
        print('Delete test - Simple')
        d = DistributedDict('127.0.0.1', 9116)
        d['adams'] = 'the hitchhiker guide'
        del d['adams']
        self.assertEqual(d['adams'], None)
        del d

    def test_delete_complex(self):
        print('Delete test - Complex')
        d = DistributedDict('127.0.0.1', 9116)
        d['0'] = '0'
        d['1'] = '1'
        d['2'] = '2'
        d['3'] = '3'
        self.assertEqual(d['0'], '0')
        self.assertEqual(d['1'], '1')
        self.assertEqual(d['2'], '2')
        self.assertEqual(d['3'], '3')
        del d['0']
        self.assertEqual(d['0'], None)
        self.assertEqual(d['1'], '1')
        self.assertEqual(d['2'], '2')
        self.assertEqual(d['3'], '3')
        del d['3']
        del d['2']
        self.assertEqual(d['0'], None)
        self.assertEqual(d['1'], '1')
        self.assertEqual(d['2'], None)
        self.assertEqual(d['3'], None)
        d['2'] = '3'
        self.assertEqual(d['0'], None)
        self.assertEqual(d['1'], '1')
        self.assertEqual(d['2'], '3')
        self.assertEqual(d['3'], None)
        del d

class FailureModeAppendTest(unittest.TestCase):
    def setUp(self):
        self.pool = Pool(4, config_file)
        self.pool.start(self.pool.ids)
        self.client_pool = ClientProcess(1, config_file)
        self.client_pool.start(self.client_pool.ids)
        sleep(1)

    def tearDown(self):
        self.pool.stop(self.pool.ids)
        self.pool.rm(self.pool.ids)
        self.client_pool.stop(self.client_pool.ids)

    def test_append_write_failure_simple(self):
        print('Append test - Write Failure Simple')
        d = DistributedDict('127.0.0.1', 9116)
        d['adams'] = 'the hitchhiker guide'
        self.pool.stop(0)
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        self.pool.start(0)
        self.pool.stop(1)
        d['0'] = '1'
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        self.pool.start(1)
        self.pool.stop(2)
        d['1'] = '0'
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        del d

    def test_append_write_failure_complex(self):
        print('Append test - Write Failure Complex')
        d = DistributedDict('127.0.0.1', 9116)
        d['adams'] = 'the hitchhiker guide'
        self.pool.stop(0)
        self.assertEqual(d['adams'], 'the hitchhiker guide')
        del d['adams']
        self.pool.start(0)
        self.pool.stop(1)
        d['foo'] = 'bar'
        self.assertEqual(d['adams'], None)
        self.assertEqual(d['foo'], 'bar')
        self.pool.start(1)
        self.pool.stop(2)
        d['bar'] = 'foo'
        del d['foo']
        self.assertEqual(d['adams'], None)
        self.assertEqual(d['foo'], None)
        self.assertEqual(d['bar'], 'foo')
        del d['bar']
        self.pool.start(2)
        self.pool.stop(0)
        d['1'] = '0'
        self.assertEqual(d['adams'], None)
        self.assertEqual(d['foo'], None)
        self.assertEqual(d['bar'], None)
        self.assertEqual(d['1'], '0')
        self.pool.start(0)
        del d


if __name__ == '__main__':
    config = Config(config={})
    start_logger()
    unittest.main(verbosity=2)
