import sys
import os
import configparser
import pickle
import logging
from unittest import TestCase
from unittest.mock import patch
from subprocess import run
from shutil import rmtree

# system under test
import shothammer

# get a logger
logger=logging.getLogger(__name__)

# Hammerspace mount required for these tests to work
# Change settings in shothammer_config.ini if they collide with the existing file system
config = configparser.ConfigParser()
config.read('shothammer_config.ini')
HS_MOUNT = config['test']['HS_MOUNT']
sys.path.insert(0, "C:/shotgrid-hammerspace/tk-core/python")
import tank.errors


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
        self.project_filter = [int(s) for s in config['shothammer']['SGHS_PROJECTS'].split(',')]

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

    def test_hs_keyword_add_norecurse(self):
        shothammer.hs_keyword_add(self.testfilepath, self.test_keyword, recursive=False, logger=logger)
        cmd = 'hs keyword has %s %s' % (self.test_keyword, self.testfilepath)
        result = run(cmd, shell=True, capture_output=True)
        retval = result.stdout.decode('utf-8').rstrip().strip('"')
        print("got %s" % retval)
        self.assertEqual(retval, "TRUE")

    def test_hs_keyword_add_recurse(self):
        shothammer.hs_keyword_add(self.testdirpath, self.test_keyword, recursive=True, logger=logger)
        cmd = 'hs keyword has %s %s' % (self.test_keyword, self.testdirfilepath)
        result = run(cmd, shell=True, capture_output=True)
        retval = result.stdout.decode('utf-8').rstrip().strip('"')
        print("got %s" % retval)
        self.assertEqual(retval, "TRUE")

    @patch('shothammer.subprocess.run')
    def test_hs_keyword_add_filtered_tag(self, mock_subprocess_run):
        shotgrid_tag = 'SGHS_IN_AZ'
        shothammer.hs_keyword_add(self.testfilepath, shotgrid_tag, logger=logger)
        self.assertTrue(mock_subprocess_run.called)

    @patch('shothammer.subprocess.run')
    def test_hs_keyword_dont_add_tag(self, mock_subprocess_run):
        shotgrid_tag = 'FOO'
        shothammer.hs_keyword_add(self.testfilepath, shotgrid_tag)
        self.assertFalse(mock_subprocess_run.called)


class TestShotHammerEventFilter(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerEventFilter, self).__init__(*args, **kwargs)
        self.project_filter = [int(s) for s in config['shothammer']['SGHS_PROJECTS'].split(',')]
        with open('sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
            self.event = pickle.load(F)
        self.logger = logging.getLogger(__name__)

    def test_event_filter_list(self):
        print(self.project_filter)
        self.assertEqual(shothammer.SGHS_PROJECTS, self.project_filter)

    @patch('shothammer.remove_tags')
    @patch('shothammer.add_tags')
    @patch('shothammer.bootstrap_engine_to_shot_path')
    def test_filtered_event_calls_bootstrap(self, mock_bootstrap, mock_add_tags, mock_remove_tags):
        shothammer.SGHS_PROJECTS = [952, 122]
        shothammer.shothammer(None, self.logger, self.event, None)
        self.assertTrue(mock_bootstrap.called)

    @patch('shothammer.remove_tags')
    @patch('shothammer.add_tags')
    @patch('shothammer.bootstrap_engine_to_shot_path')
    def test_filtered_event_does_not_call_bootstrap(self, mock_bootstrap, mock_add_tags, mock_remove_tags):
        shothammer.SGHS_PROJECTS = [100, 101]
        shothammer.shothammer(None, self.logger, self.event, None)
        self.assertFalse(mock_bootstrap.called)

class TestShotHammerEventProcessing(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerEventProcessing, self).__init__(*args, **kwargs)
        with open('sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
            self.event = pickle.load(F)

    def test_get_shot_code(self):
        target_shot_code = 'ep888_sh0000'
        result_shot_code = shothammer.get_shot_code(self.event)
        self.assertEqual(result_shot_code, target_shot_code)

    def test_capture_event(self):
        test_pickle = 'shothammer_test.pickle'
        shothammer.capture_event(self.event, test_pickle)
        with open(test_pickle, 'rb') as F:
            saved_event = pickle.load(F)
        self.assertEqual(saved_event, self.event)

    def test_get_project_id(self):
        target_project_id = 952
        result = shothammer.get_project_id(self.event)
        self.assertEqual(result, target_project_id)


class TestShotHammerBootstrapping(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerBootstrapping, self).__init__(*args, **kwargs)
        with open('sghs_event_shot_tag_add_9502.pickle', 'rb') as F:
            self.event_9502 = pickle.load(F)
        with open('sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
            self.event_9583 = pickle.load(F)
        self.logger = logging.getLogger(__name__)

    def test_get_directory_ep888_sh0000_success(self):
        # ep888 sh0000 shot id 9583 has the expected path schema
        target_path = "P:\\testshow\\work\\episodes\\ep888\\ep888_sh0000"
        result_path = shothammer.bootstrap_engine_to_shot_path(self.logger, self.event_9583)
        self.assertEqual(target_path, result_path)


class TestShotHammerIntegration(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerIntegration, self).__init__(*args, **kwargs)
        # the shot without expected path schema
        with open('sghs_event_shot_tag_add_9502.pickle', 'rb') as F:
            self.event_9502 = pickle.load(F)
        # the shot with expected path schema
        with open('sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
            self.event_9583 = pickle.load(F)
        self.logger = logging.getLogger(__name__)

    def setUp(self) -> None:
        shothammer.SGHS_PROJECTS = [952, 122]

    @patch('shothammer.remove_tags')
    @patch('shothammer.add_tags')
    def test_shothammer(self, mock_add_tags, mock_remove_tags):
        shothammer.shothammer(None, self.logger, self.event_9583, None)
        self.assertTrue(mock_add_tags.called)
        self.assertTrue(mock_remove_tags.called)

# TODO: Just like above, this test passes when run by itself, but not when we run all the tests
class TestShotHammerIntegrationFails(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerIntegrationFails, self).__init__(*args, **kwargs)
        # the shot without expected path schema
        with open('sghs_event_shot_tag_add_9502.pickle', 'rb') as F:
            self.event_9502 = pickle.load(F)
        # the shot with expected path schema
        with open('sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
            self.event_9583 = pickle.load(F)
        self.logger = logging.getLogger(__name__)

    def setUp(self) -> None:
        shothammer.SGHS_PROJECTS = [952, 122]

    def tearDown(self) -> None:
        os.remove('shot_id-9502-2022-03-23_22-01-16.pickle')

    @patch('shothammer.remove_tags')
    @patch('shothammer.add_tags')
    def test_shothammer_fails_no_tags(self, mock_add_tags, mock_remove_tags):
        shothammer.shothammer(None, self.logger, self.event_9502, None)
        self.assertFalse(mock_add_tags.called)
        self.assertFalse(mock_remove_tags.called)

    def test_shothammer_fails_writes_event_pickle(self):
        shothammer.shothammer(None, self.logger, self.event_9502, None)
        with open('shot_id-9502-2022-03-23_22-01-16.pickle', 'rb') as F:
            saved_event = pickle.load(F)
        self.assertEqual(self.event_9502, saved_event)