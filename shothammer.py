import os
import sys
import logging
import subprocess
import pprint
import configparser
import pickle

# Read config and set up global auth variables
config = configparser.ConfigParser()
config.read('shothammer_config.ini')
SGHS_NAME = config['shothammer']['SGHS_NAME']
SGHS_KEY = config['shothammer']['SGHS_KEY']

# Vanilla sgtk needed for auth so that we can get a context-specific engine
sys.path.insert(0, "C:/shotgrid-hammerspace/tk-core/python")
import sgtk

# Initial sgtk auth
sgtk.LogManager().initialize_custom_handler()
sgtk.LogManager().global_debug = False
# Create a ShotgunAuthenticator object
sa = sgtk.authentication.ShotgunAuthenticator()
# Use the ShotgunAuthenticator to create a user object
user = sa.create_script_user(api_script=SGHS_NAME,
                             api_key=SGHS_KEY,
                             host=os.environ['SG_ED_SITE_URL'])
# Authenticate
sgtk.set_authenticated_user(user)
# Now we are set up for bootstrapping the engine in various contexts, handled per-callback

# Make this true if you want to serialize and capture the last event seen
# TODO: Move this to the config file
CAPTURE_LAST_EVENT = False
LAST_EVENT_FILE = 'sghs_event.pickle'

# global pretty printer
PP = pprint.PrettyPrinter(indent=2)


def registerCallbacks(reg):
    """
    Register all the callbacks for this plugin
    :param reg:
    :return:
    """
    # We only care about changes to tags on Shots
    # added tags will be added as keywords recursively to the appropriate shot directory
    # removed tags will be removed recursively
    eventFilter = {
        'Shotgun_Shot_Change': ['tags'],
    }
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

    :param sg:      Shotgun API handle
    :param logger:  Logger instance
    :param event:   EventLogEntry dictionary
    :param args:    Additional arguments passed
    """
    # logger.info("%s" % str(event))
    logger.info(PP.pprint(event))
    logger.debug(project_name_from_event(event))
    if CAPTURE_LAST_EVENT:
        F = open(LAST_EVENT_FILE, 'wb')
        pickle.dump(event, F)
        F.close()

    path = bootstrap_engine_to_shot_path(logger, event)
    add_tags(logger, event, path)
    remove_tags(logger, event, path)


def add_tags(logger, event, path):
    """
    Take list of added tags from Shotgrid event, add them as keywords recursively to the path specified
    :param logger:
    :param event:
    :param path:
    :return:
    """
    tags_to_add = [element['name'] for element in event['meta']['added']]
    for tag in tags_to_add:
        # Using Shotgrid tags -> Hammerspace keywords
        logger.info("Setting keyword %s on path %s" % (tag, path))
        hs_keyword_add(path, tag, recursive=True)

def remove_tags(logger, event, path):
    """
    Take list of removed tags from Shotgrid event, remove the corresponding keywords directly on the path specified
    :param logger:
    :param event:
    :param path:
    :return:
    """
    tags_to_remove = [element['name'] for element in event['meta']['removed']]
    for tag in tags_to_remove:
        logger.info("Removing keyword %s from path %s" % (tag, path))
        hs_keyword_delete(path, tag, recursive=True)


def bootstrap_engine_to_shot_path(logger, event):
    shot_id = event['entity']['id']
    project_id = event['project']['id']
    manager = sgtk.bootstrap.ToolkitManager(sgtk.get_authenticated_user())
    # This must be configured as an id for the appropriate per-project config
    # This will let us select which config shothammer pulls per-project
    manager.plugin_id = "sghs."
    logger.debug("Manager object:\n%s" % str(manager))
    logger.debug("Trying to bootstrap project ID %s" % project_id)
    engine = manager.bootstrap_engine("tk-shell", entity={"type": "Shot", "id": shot_id})
    logger.debug("Engine object:\n%s" % str(engine))
    work_shot_area_template = engine.sgtk.templates["work_shot_area"]
    episode_code = get_episode_code(event)
    shot_code = get_shot_code(event)
    result = work_shot_area_template.apply_fields({'Episode': episode_code,
                                                   'Shot': shot_code,
                                                   })
    engine.destroy()
    return result


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

def hs_keyword_add(path, keyword, recursive=True) -> None:
    if recursive:
        cmd = 'hs keyword add -r %s %s' % (keyword, path)
    else:
        cmd = 'hs keyword add %s %s' % (keyword, path)
    result = subprocess.run(cmd, shell=True, capture_output=True)
    logging.debug("hs_keyword_add()")
    logging.debug("STDOUT:")
    logging.debug(result.stdout)
    logging.debug("STDERR:")
    logging.debug(result.stderr)

def hs_keyword_delete(path, keyword, recursive=True) -> None:
    if recursive:
        cmd = 'hs keyword delete -r %s %s' % (keyword, path)
    else:
        cmd = 'hs keyword delete %s %s' % (keyword, path)
    result = subprocess.run(cmd, shell=True, capture_output=True)
    logging.debug("hs_keyword_delete()")
    logging.debug("STDOUT:")
    logging.debug(result.stdout)
    logging.debug("STDERR:")
    logging.debug(result.stderr)

def project_name_from_event(event) -> str:
    return event['project']['name']

def path_from_project_name(project) -> str:
    """
    This is no longer valid, since the path needs to come from a bootstrapped engine
    """
    return os.path.join(config['shothammer']['SGHS_PROJECT_PATH'], project)

def is_attribute_change(event) -> bool:
    return event['meta']['type'] == 'attribute_change'

def get_shot_code(event):
    return event['entity']['name']

def get_episode_code(event):
    elements = event['entity']['name'].split('_')
    logging.debug(elements)
    return elements[0]
