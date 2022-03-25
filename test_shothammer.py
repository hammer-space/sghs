import os
import configparser
import pickle
import logging
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


class TestShotHammerFileAccess(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerFileAccess, self).__init__(*args, **kwargs)
        self.testfilename = config['test']['TEST_FILE_NAME']
        self.testfilepath = os.path.join(HS_MOUNT, self.testfilename)
        self.testdirname = config['test']['TEST_DIR_NAME']
        self.testdirfilepath = os.path.join(HS_MOUNT, self.testdirname, self.testfilename)
        self.testdirpath = os.path.join(HS_MOUNT, self.testdirname)
        self.test_tag = config['test']['TEST_TAG']
        self.test_value = config['test']['TEST_VALUE']
        self.test_keyword = config['test']['TEST_KEYWORD']

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
        os.remove(self.testdirfilepath)
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

    def test_hs_keyword_add_norecurse(self):
        shothammer.hs_keyword_add(self.testfilepath, self.test_keyword, recursive=False)
        cmd = 'hs keyword has %s %s' % (self.test_keyword, self.testfilepath)
        result = run(cmd, shell=True, capture_output=True)
        retval = result.stdout.decode('utf-8').rstrip().strip('"')
        print("got %s" % retval)
        self.assertEqual(retval, "TRUE")

    def test_hs_keyword_add_recurse(self):
        shothammer.hs_keyword_add(self.testdirpath, self.test_keyword, recursive=True)
        cmd = 'hs keyword has %s %s' % (self.test_keyword, self.testdirfilepath)
        result = run(cmd, shell=True, capture_output=True)
        retval = result.stdout.decode('utf-8').rstrip().strip('"')
        print("got %s" % retval)
        self.assertEqual(retval, "TRUE")

class TestShotHammerEventProcessing(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerEventProcessing, self).__init__(*args, **kwargs)
        with open('sghs_event_shot_tag_add.pickle', 'rb') as F:
            self.event = pickle.load(F)

    def test_get_shot_code(self):
        target_shot_code = 'ep101_sh0000'
        result_shot_code = shothammer.get_shot_code(self.event)
        self.assertEqual(result_shot_code, target_shot_code)

    def test_get_episode_code(self):
        target_episode_code = 'ep101'
        result_episode_code = shothammer.get_episode_code(self.event)
        self.assertEqual(result_episode_code, target_episode_code)


class TestShotHammerBootstrapping(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerBootstrapping, self).__init__(*args, **kwargs)
        with open('sghs_event_shot_tag_add.pickle', 'rb') as F:
            self.event = pickle.load(F)
        self.logger = logging.getLogger(__name__)

    def test_get_directory(self):
        target_path = "P:\\testshow\\work\\episodes\\ep101\\ep101_sh0000"
        result_path = shothammer.bootstrap_engine_to_shot_path(self.logger, self.event)
        self.assertEqual(result_path, target_path)
