import sys
import pickle
import pprint

import shothammer

TEMPLATES = {"Shot": ['shot_template_1', 'shot_template_2'],
             "Sequence": ['sequence_template_1', 'sequence_template_2'],
             "Task": ['task_template_1', 'task_template_2'],
             }

PP = pprint.PrettyPrinter(indent=4)


def get_object_type_from_event(event):
    """Eat an event, return 'Shot', 'Sequence', or 'Task'"""
    return event['meta']['entity_type']


def main():
    EVENT = sys.argv[1]
    with open(EVENT, 'rb') as F:
        data = pickle.load(F)


if __name__ == '__main__':
    main()


