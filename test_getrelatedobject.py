import unittest
import pickle

import shothammer

import getrelatedobject


class TestGetRelatedObject(unittest.TestCase):
    def test_get_object_type_from_event_shot(self):
        shot_pickle_file = 'sghs_event_shot.pickle'
        with open(shot_pickle_file, 'rb') as F:
            event = pickle.load(F)
        print(event)
        result = getrelatedobject.get_object_type_from_event(event)
        self.assertEqual(result, "Shot")

    def test_get_object_type_from_event_sequence(self):
        sequence_pickle_file = 'sghs_event_sequence.pickle'
        with open(sequence_pickle_file, 'rb') as F:
            event = pickle.load(F)
        print(event)
        result = getrelatedobject.get_object_type_from_event(event)
        self.assertEqual(result, "Sequence")

    def test_get_object_type_from_event_task(self):
        task_pickle_file = 'sghs_event_task.pickle'
        with open(task_pickle_file, 'rb') as F:
            event = pickle.load(F)
        print(event)
        result = getrelatedobject.get_object_type_from_event(event)
        self.assertEqual(result, "Task")