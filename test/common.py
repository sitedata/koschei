import os
import sys
import unittest
import sqlalchemy
import logging
import shutil
import json

from datetime import datetime

testdir = os.path.dirname(os.path.realpath(__file__))
datadir = os.path.join(testdir, 'data')
os.chdir(testdir)
sys.path[:0] = [os.path.join(testdir, '..'),
                os.path.join(testdir, 'mocks')]

# our mock
import fedmsg

use_postgres = os.environ.get('TEST_WITH_POSTGRES')

test_cfg = os.path.join(testdir, 'test_config.cfg')
os.environ['KOSCHEI_CONFIG'] = test_cfg
from koschei import util
assert util.config.get('is_test') is True
if use_postgres:
    testdb = 'koschei_testdb'
    util.config['database_config']['drivername'] = 'postgres'
    util.config['database_config']['username'] = 'postgres'
    util.config['database_config']['database'] = testdb
else:
    util.config['database_config']['drivername'] = 'sqlite'

util.root_logger.removeHandler(util.log_handler)
util.root_logger.addHandler(logging.FileHandler('out.log'))
sql_log = logging.getLogger('sqlalchemy.engine')
sql_log.propagate = False
sql_log.setLevel(logging.INFO)
sql_log_file = 'sql.log'
sql_log.addHandler(logging.FileHandler(sql_log_file))

from koschei import service

def identity_decorator(*args, **kwargs):
    def decorator(function):
        return function
    return decorator

service.service_main = identity_decorator

from koschei import models as m

class MockDatetime(object):
    @staticmethod
    def now():
        return datetime(2000, 10, 10)

workdir = '.workdir'

def postgres_only(fn):
    return unittest.skipIf(not use_postgres, "Requires postgres")(fn)

class AbstractTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(AbstractTest, self).__init__(*args, **kwargs)
        self.fedmsg = fedmsg
        self.s = None

        if use_postgres:
            cfg = util.config['database_config'].copy()
            del cfg['database']
            url = sqlalchemy.engine.url.URL(**cfg)
            engine = sqlalchemy.create_engine(url, poolclass=sqlalchemy.pool.NullPool)
            conn = engine.connect()
            conn.execute("COMMIT")
            conn.execute("DROP DATABASE IF EXISTS {0}".format(testdb))
            conn.execute("COMMIT")
            conn.execute("CREATE DATABASE {0}".format(testdb))
            conn.close()

    def _rm_workdir(self):
        try:
            shutil.rmtree(workdir)
        except OSError:
            pass

    def setUp(self):
        self._rm_workdir()
        os.mkdir(workdir)
        os.chdir(workdir)
        m.Base.metadata.create_all(m.engine)
        tables = m.Base.metadata.tables
        conn = m.engine.connect()
        for table in tables.values():
            conn.execute(table.delete())
        conn.close()
        self.s = m.Session()
        self.fedmsg.mock_init()

    def tearDown(self):
        self.s.close()
        self.fedmsg.mock_verify_empty()
        m.engine.dispose()
        self._rm_workdir()

    def prepare_basic_data(self):
        pkg = m.Package(name='rnv')
        self.s.add(pkg)
        self.s.flush()
        build = m.Build(package_id=pkg.id, state=m.Build.RUNNING,
                        task_id=666)
        self.s.add(build)
        self.s.commit()
        return pkg, build

    def get_json_data(self, name):
        with open(os.path.join(datadir, name)) as fo:
            return json.load(fo)
