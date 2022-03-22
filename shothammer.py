import os
import logging
import subprocess
import pprint
import configparser
import pickle

config = configparser.ConfigParser()
config.read('shothammer_config.ini')
SGHS_NAME = config['shothammer']['SGHS_NAME']
SGHS_KEY = config['shothammer']['SGHS_KEY']

CAPTURE_LAST_EVENT = True
LAST_EVENT_FILE = 'sghs_event.pickle'

# global pretty printer
PP = pprint.PrettyPrinter(indent=2)


def registerCallbacks(reg):
    """
    Register all the callbacks for this plugin
    :param reg:
    :return:
    """
    eventFilter = {
        'Shotgun_Sequence_Change': ['*'],
        'Shotgun_Shot_Change': ['*'],
        'Shotgun_Asset_Change': ['*'],
        'Shotgun_Task_Change': ['*']
    }
    # eventFilter = None
    reg.registerCallback(
        SGHS_NAME,
        SGHS_KEY,
        shothammer,
        eventFilter,
        None,
    )

    # log level DEBUG during development
    reg.logger.setLevel(logging.DEBUG)
    # reg.logger.setLevel(logging.INFO)


def shothammer(sg, logger, event, args):
    """
    Set custom metadata on files in a local file system

    :param sg:
    :param logger:
    :param event:
    :param args:
    :return:
    """
    # logger.info("%s" % str(event))
    logger.debug(PP.pprint(event))
    logger.debug(project_name_from_event(event))
    if CAPTURE_LAST_EVENT:
        F = open(LAST_EVENT_FILE, 'wb')
        pickle.dump(event, F)
        F.close()
    if is_attribute_change(event):
        old_value = event['meta']['old_value']
        new_value = event['meta']['new_value']
        attribute_name = event['meta']['attribute_name']
        logger.debug("Status change:")
        logger.debug("Field: %s" % attribute_name)
        logger.debug("%s -> %s" % (old_value, new_value))
        path = path_from_project_name(project_name_from_event(event))
        logger.info("Setting tag %s=%s recursively on %s" % (attribute_name, new_value, path))
        hs_tag_set(path, attribute_name, new_value)
        logger.info("Done setting tags")


def hs_tag_set(path, tag, value, recursive=True) -> None:
    if recursive:
        cmd = 'hs tag set -r -e \'%s\' %s %s' % (value, tag, path)
    else:
        cmd = 'hs tag set -e \'%s\' %s %s' % (value, tag, path)
    result = subprocess.run(cmd, shell=True, capture_output=True)
    logging.debug("STDOUT:")
    logging.debug(result.stdout)
    logging.debug("STDERR:")
    logging.debug(result.stderr)


def project_name_from_event(event) -> str:
    return event['project']['name']


def path_from_project_name(project) -> str:
    return os.path.join(config['shothammer']['SGHS_PROJECT_PATH'], project)


def is_attribute_change(event) -> bool:
    return event['meta']['type'] == 'attribute_change'
