import os
import unittest

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

import carbon
from carbon.helpers import file_mgmt


class TestLogging(object):

    def test_logger_cache(self):
        cbn = carbon.Carbon(__name__)
        logger1 = cbn.logger
        assert cbn.logger is logger1
        assert cbn.name == __name__
        cbn.logger_name = __name__ + '/test_logger_cache'
        assert cbn.logger is not logger1


class TestFileMgmt(unittest.TestCase):

    def test_unknown_file_operation(self):
        with self.assertRaisesRegexp(Exception, "Unknown file operation: x."):
            file_mgmt('x', 'test.yml')

    def test_file_not_found(self):
        with self.assertRaisesRegexp(Exception, "test.yml file not found!"):
            file_mgmt('r', 'test.yml')

    def test_yaml_ext(self):
        _file = "test.yml"
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            assert file_mgmt('w', _file, _data) != 0
            self.assertIsInstance(file_mgmt('r', _file), dict)
        finally:
            os.remove(_file)

    def test_json_ext(self):
        _file = "test.json"
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            assert file_mgmt('w', _file, _data) != 0
            self.assertIsInstance(file_mgmt('r', _file), dict)
        finally:
            os.remove(_file)

    def test_text_ext(self):
        _file = "test.txt"
        _data = "Carbon project"
        try:
            assert file_mgmt('w', _file, _data) != 0
            assert file_mgmt('r', _file) == "Carbon project"
        finally:
            os.remove(_file)

    def test_ini_ext(self):
        _file = "test.ini"
        cfg1, cfg2 = ConfigParser(), ConfigParser()
        cfg1.add_section('Carbon')
        cfg1.set('Carbon', 'Team', 'PIT')
        try:
            assert file_mgmt('w', _file, cfg_parser=cfg1) != 0
            file_mgmt('r', _file, cfg_parser=cfg2)
            self.assertIsInstance(cfg2, ConfigParser)
        finally:
            os.remove(_file)
