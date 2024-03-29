import os
import sys
import logging
import subprocess
import pprint
import yaml
import pickle

from datetime import datetime

# Read config and set up global auth variables
with open('shothammer_config.yml') as F:
    config = yaml.load(F, Loader=yaml.FullLoader)
SGHS_NAME = config['SGHS_NAME']
SGHS_KEY = config['SGHS_KEY']

# Set up project and tag filters
SGHS_PROJECTS = config['SGHS_PROJECTS']
SGHS_TAG_NAMESPACE = config['SGHS_TAG_NAMESPACE']

# Vanilla sgtk needed for auth so that we can get a context-specific engine
sys.path.insert(0, config['SG_TOOLKIT'])
import sgtk

# Whether to capture the last event, and where to put it. Edit in shothammer_config.yml
CAPTURE_LAST_EVENT = config['CAPTURE_LAST_EVENT']
LAST_EVENT_FILE = config['LAST_EVENT_FILE']

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
        'Shotgun_Sequence_Change': ['tags'],
        'Shotgun_Task_Change': ['tags'],
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
    logger.setLevel(logging.DEBUG)
    logger.debug(PP.pprint(event))
    try:
        logger.debug(get_project_name(event))
    except TypeError as e: # Project is None in event
        logger.warn("Project is none in event from shot %i" % get_shot_code(event))
        return

    if CAPTURE_LAST_EVENT:
        capture_event(event, LAST_EVENT_FILE)

    # only process events from projects in the allowed list if it exists
    paths = None
    if SGHS_PROJECTS is None or get_project_id(event) in SGHS_PROJECTS:
        paths = get_paths_from_event(logger, event)

    logger.debug("Paths: %s" % paths)
    # These functions take shotgrid tags and add/remove keywords to/from the paths specified
    # only if we got a non empty list
    if paths:
        for path in paths:
            add_tags(logger, event, path)
            remove_tags(logger, event, path)


def capture_event(event, filename) -> None:
    """
    Save a pickle to the location specified in the .ini config
    :param event:
    :return:
    """
    with open(filename, 'wb') as F:
        pickle.dump(event, F)


def add_tags(logger, event, path) -> None:
    """
    Take list of added tags from Shotgrid event, add them as keywords recursively to the path specified
    :param logger:
    :param event:
    :param path:
    :return:
    """
    tags_to_add = [element['name'] for element in event['meta']['added']]
    logger.debug("Tags to add: %s" % str(tags_to_add))
    for tag in tags_to_add:
        # Using Shotgrid tags -> Hammerspace keywords
        logger.info("Setting keyword %s on path %s" % (tag, path))
        hs_keyword_add(path, tag, recursive=False, logger=logger)


def remove_tags(logger, event, path) -> None:
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
        hs_keyword_delete(path, tag, recursive=False, logger=logger)


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


def hs_keyword_add(path, keyword, recursive=True, logger=None) -> None:
    if not keyword.startswith(SGHS_TAG_NAMESPACE):
        logging.debug("tag %s not in namespace, skipping")
        return
    if recursive:
        cmd = 'hs keyword add -r %s %s' % (keyword, path)
    else:
        cmd = 'hs keyword add %s %s' % (keyword, path)
    result = subprocess.run(cmd, shell=True, capture_output=True)
    logger.debug("hs_keyword_add()")
    logger.debug("STDOUT:")
    logger.debug(result.stdout)
    logger.debug("STDERR:")
    logger.debug(result.stderr)


def hs_keyword_delete(path, keyword, recursive=True, logger=None) -> None:
    if not keyword.startswith(SGHS_TAG_NAMESPACE):
        logging.debug("tag %s not in namespace, skipping")
        return
    if recursive:
        cmd = 'hs keyword delete -r %s %s' % (keyword, path)
    else:
        cmd = 'hs keyword delete %s %s' % (keyword, path)
    result = subprocess.run(cmd, shell=True, capture_output=True)
    logger.debug("hs_keyword_delete()")
    logger.debug("STDOUT:")
    logger.debug(result.stdout)
    logger.debug("STDERR:")
    logger.debug(result.stderr)


def get_project_name(event) -> str:
    return event['project']['name']


def is_attribute_change(event) -> bool:
    return event['meta']['type'] == 'attribute_change'


def get_shot_code(event) -> str:
    """
    This isn't just the shotid, but rather the full code including episode or sequence
    :param event:
    :return:
    """
    return event['entity']['name']


def get_project_id(event) -> int:
    return event['project']['id']


# def get_entity_type_from_event(event):
#     """Eat an event, return 'Shot', 'Sequence', or 'Task'"""
#     return event['meta']['entity_type']
#

def get_paths_from_event(logger, event):
    manager = initialize_shotgrid_manager()
    # Figure out what object type event relates to: Shot, Sequence, Task
    entity_type = event['meta']['entity_type']
    entity_id = event['entity']['id']
    # bootstrap should use the config dict to return a list of paths depending on object type
    template_names = config['SGHS_PATH_TEMPLATES'][entity_type]
    # bootstrap using the type name and id from the event
    engine = manager.bootstrap_engine("tk-shell", entity={"type": entity_type, "id": entity_id})

    # get template objects from names now that we have an engine
    templates = [engine.sgtk.templates[t] for t in template_names]
    # import tank.errors

    # set up filters and fields we want back from the query
    filters = [["id", "is", entity_id]]
    # TODO: does it make more sense to just have a single list of every field we could ever want?
    if entity_type != "Task":
        fields = ["id", "type", "code", "sg_episode", "sg_sequence"]
    else:
        fields = ["id", "type", "entity", "project", "step", "template_task", "content"]

    # get the full object
    full_obj = engine.shotgun.find_one(entity_type, filters=filters, fields=fields)

    if entity_type == "Shot":
        # Get enough data to fill shot templates
        Shot = full_obj['code']
        Sequence = full_obj['sg_sequence']['name']
        # loop through and fill them, returning a list of paths
        return [t.apply_fields({'Shot': Shot,
                                'Sequence': Sequence
                                })
                for t in templates]
    elif entity_type == "Sequence":
        # Get enough data to fill sequence templates
        Sequence = full_obj['code']
        # loop through and fill them, returning a list of paths
        return [t.apply_fields({'Sequence': Sequence,
                                })
                for t in templates]
    elif entity_type == "Task":
        # Get enough data to fill task templates
        # get step shortname ({Step} in a path template)
        step = engine.shotgun.find_one("Step", [['code', 'is', full_obj['step']['name']]], ["code", "short_name"])
        step_shortname = step['short_name']

        # get task name ({task_name})
        task_name = full_obj['content']

        # get Shot from Task
        fields = ["id", "type", "code", "sg_episode", "sg_sequence"]
        related_shot = engine.shotgun.find_one("Shot", [['id', 'is', full_obj['entity']['id']]], fields)
        shot_code = related_shot['code']

        # get Sequence from Shot
        related_sequence = related_shot['sg_sequence']['name']

        return [t.apply_fields({'Sequence': related_sequence,
                                'Shot': shot_code,
                                'Step': step_shortname,
                                'task_name': task_name,
                                })
                for t in templates]
    else:
        logger.warning("Entity type %s can't be handled" % entity_type)
        return None

def initialize_shotgrid_manager():
    # Re-bootstrap the engine in the correct user and plugin id
    manager = sgtk.bootstrap.ToolkitManager(sgtk.get_authenticated_user())
    manager.plugin_id = "sghs."
    return manager

def authenticate_sgtk_user():
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

# Do this so that sgtk has a working authenticated user for later bootstrapping
authenticate_sgtk_user()
