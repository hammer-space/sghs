import os
import configparser
from unittest import TestCase
from subprocess import run
from shutil import rmtree

# system under test
import shothammer

# Hammerspace mount required for these tests to work
# Change settings in shothammer_config.ini if they collide with the existing file system
config = configparser.ConfigParser()
config.read('shothammer_config.ini')
HS_MOUNT = config['test']['HS_MOUNT']
TEST_FILE_NAME = config['test']['TEST_FILE_NAME']
TEST_DIR_NAME = config['test']['TEST_DIR_NAME']
TEST_TAG = config['test']['TEST_TAG']
TEST_VALUE = config['test']['TEST_VALUE']


class TestShotHammer(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammer, self).__init__(*args, **kwargs)
        self.testfilename = TEST_FILE_NAME
        self.testfilepath = os.path.join(HS_MOUNT, self.testfilename)
        self.testdirname = TEST_DIR_NAME
        self.testdirfilepath = os.path.join(HS_MOUNT, self.testdirname, self.testfilename)
        self.testdirpath = os.path.join(HS_MOUNT, self.testdirname)
        self.test_tag = TEST_TAG
        self.test_value = TEST_VALUE

    def setUp(self):
        # make a test file in the root of the mount
        F = open(self.testfilepath, 'w+')
        F.write("0")
        F.close()

        # make a test directory in the root of the mount, then a test file inside it
        os.mkdir(self.testdirpath)
        F = open(self.testdirfilepath, 'w+')
        F.write("0")
        F.close()

    def tearDown(self) -> None:
        os.remove(self.testfilepath)
        rmtree(self.testdirpath)

    def test_hs_tag_set_norecurse(self) -> None:
        shothammer.hs_tag_set(self.testfilepath, self.test_tag, self.test_value, recursive=False)
        cmd = 'hs tag get %s %s' % (self.test_tag, self.testfilepath)
        result = run(cmd, shell=True, capture_output=True)
        # since we're scraping CLI output need to strip CRLF and quotes before comparison
        tag_value = result.stdout.decode('utf-8').rstrip().strip('"')
        print("TAG_VALUE:", tag_value)
        self.assertEqual(self.test_value, tag_value)

    def test_hs_tag_set_recurse(self) -> None:
        shothammer.hs_tag_set(self.testdirpath, self.test_tag, self.test_value, recursive=True)
        cmd = 'hs tag get %s %s' % (self.test_tag, self.testdirfilepath)
        result = run(cmd, shell=True, capture_output=True)
        tag_value = result.stdout.decode('utf-8').rstrip().strip('"')
        print("TAG_VALUE:", tag_value)
        self.assertEqual(self.test_value, tag_value)

    def test_path_from_project_name(self) -> None:
        test_project = "awesome_project"
        path = shothammer.config['shothammer']['SGHS_PROJECT_PATH']
        expected_fullpath = os.path.join(path, test_project)
        result = shothammer.path_from_project_name(test_project)
        self.assertEqual(expected_fullpath, result)
