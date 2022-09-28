import sys
import os
import yaml
import pickle
import logging
from unittest import TestCase
from unittest.mock import patch
from subprocess import run
from shutil import rmtree

# get a logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# system under test
import shothammer

# Hammerspace mount required for these tests to work
# Change settings in shothammer_config.yml if they collide with the existing file system
with open('shothammer_config.yml') as F:
    config = yaml.load(F, Loader=yaml.FullLoader)
HS_MOUNT = config['test']['HS_MOUNT']
sys.path.insert(0, config['test']['TK_CORE_PYTHON_PATH'])


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
        self.project_filter = config['SGHS_PROJECTS']

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
        self.project_filter = config['SGHS_PROJECTS']
        with open('test/sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
            self.event = pickle.load(F)
        self.logger = logger

    def test_event_filter_list(self):
        print(self.project_filter)
        self.assertEqual(shothammer.SGHS_PROJECTS, self.project_filter)

    @patch('shothammer.remove_tags')
    @patch('shothammer.add_tags')
    @patch('shothammer.get_paths_from_event')
    def test_filtered_event_calls_get_paths(self, mock_get_paths, mock_add_tags, mock_remove_tags):
        original_projects = shothammer.SGHS_PROJECTS
        shothammer.SGHS_PROJECTS = [952, 122]
        shothammer.shothammer(None, self.logger, self.event, None)
        shothammer.SGHS_PROJECTS = original_projects
        self.assertTrue(mock_get_paths.called)


    @patch('shothammer.remove_tags')
    @patch('shothammer.add_tags')
    @patch('shothammer.get_paths_from_event')
    def test_filtered_event_does_not_call_get_paths(self, mock_get_paths, mock_add_tags, mock_remove_tags):
        original_projects = shothammer.SGHS_PROJECTS
        shothammer.SGHS_PROJECTS = [100, 101]
        shothammer.shothammer(None, self.logger, self.event, None)
        shothammer.SGHS_PROJECTS = original_projects
        self.assertFalse(mock_get_paths.called)


class TestShotHammerEventProcessing(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerEventProcessing, self).__init__(*args, **kwargs)
        with open('test/sghs_event_shot_tag_add_9583.pickle', 'rb') as F:
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


class TestShotHammerIntegration(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestShotHammerIntegration, self).__init__(*args, **kwargs)
        with open('test/sghs_event_shot_tag_add_862.pickle', 'rb') as F:
            self.event_add_862 = pickle.load(F)
        with open('test/sghs_event_shot_tag_remove_862.pickle', 'rb') as F2:
            self.event_remove_862 = pickle.load(F2)
        self.logger = logger

    @patch('shothammer.add_tags')
    def test_shothammer_adds_tags(self, mock_add_tags):
        shothammer.shothammer(None, self.logger, self.event_add_862, None)
        self.assertTrue(mock_add_tags.called)

    @patch('shothammer.remove_tags')
    def test_shothammer_removes_tags(self, mock_remove_tags):
        shothammer.shothammer(None, self.logger, self.event_remove_862, None)
        self.assertTrue(mock_remove_tags.called)


class TestMultipleObjectTypes(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestMultipleObjectTypes, self).__init__(*args, **kwargs)
        with open('test/sghs_event_shot.pickle', 'rb') as F:
            self.sghs_event_shot = pickle.load(F)
        with open('test/sghs_event_sequence.pickle', 'rb') as F2:
            self.sghs_event_sequence = pickle.load(F2)
        with open('test/sghs_event_task.pickle', 'rb') as F3:
            self.sghs_event_task = pickle.load(F3)
        self.logger = logger

    def test_bootstrap_engine_to_shot_paths(self):
        """Given an event about a shot tag change, return a list of filled out templates"""
        target_paths = ["H:\\Animation\\sequences\\bunny_010\\bunny_010_0020\\PDF",
                        "H:\\Animation\\sequences\\bunny_010\\bunny_010_0020\\Pictures",
                        ]
        result_paths = shothammer.get_paths_from_event(logger, self.sghs_event_shot)
        self.assertEqual(target_paths, result_paths)

    def test_bootstrap_engine_to_sequence_paths(self):
        """Given an event about a sequence tag change, return a list of filled out templates"""
        target_paths = ["H:\\Animation\\sequences\\bunny_010",
                        "H:\\Animation\\sequences\\ALT\\bunny_010",
                        ]
        result_paths = shothammer.get_paths_from_event(logger, self.sghs_event_sequence)
        self.assertEqual(target_paths, result_paths)

    def test_bootstrap_engine_to_task_paths(self):
        """Given an event about a task tag change, return a list of filled out templates"""
        # task_template_1: sequences / {Sequence} / {Shot} / {Step} / {task_name}
        # task_template_2: sequences / ALT / {Sequence} / {Shot} / zip
        target_paths = ["H:\\Animation\\sequences\\bunny_010\\bunny_010_0010\\ANM\\Animation",
                        "H:\\Animation\\sequences\\ALT\\bunny_010\\bunny_010_0010\\zip",
                        ]
        result_paths = shothammer.get_paths_from_event(logger, self.sghs_event_task)
        self.assertEqual(target_paths, result_paths)
