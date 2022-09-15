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
SGHS_NAME = config['shothammer']['SGHS_NAME']
SGHS_KEY = config['shothammer']['SGHS_KEY']

# Set up project and tag filters
SGHS_PROJECTS = config['shothammer']['SGHS_PROJECTS']
SGHS_TAG_NAMESPACE = config['shothammer']['SGHS_TAG_NAMESPACE']

# Vanilla sgtk needed for auth so that we can get a context-specific engine
sys.path.insert(0, config['shothammer']['SG_TOOLKIT'])
import sgtk
import tank.errors

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

# Whether to capture the last event, and where to put it. Edit in shothammer_config.yml
CAPTURE_LAST_EVENT = config['shothammer']['CAPTURE_LAST_EVENT']
LAST_EVENT_FILE = config['shothammer']['LAST_EVENT_FILE']

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
    logger.setLevel(logging.DEBUG)
    logger.debug(PP.pprint(event))
    try:
        logger.debug(get_project_name(event))
    except TypeError as e: # Project is None in event
        logger.warn("Project is none in event from shot %i" % get_shot_code(event))
        return

    if CAPTURE_LAST_EVENT:
        capture_event(event, LAST_EVENT_FILE)

    # only process events from projects in the allowed list
    path = None
    if get_project_id(event) in SGHS_PROJECTS:
        path = bootstrap_engine_to_shot_path(logger, event)

    logger.debug("Path: %s" % path)
    # These functions take shotgrid tags and add/remove keywords to/from the path specified
    # only if we got a real path
    if path:
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


def bootstrap_engine_to_shot_path(logger, event) -> str:
    """
    Get the shot_id from the event, and use that to bootstrap to a project-specific engine
    that can access the template and configuration needed to return a full path to the shot

    :param logger:
    :param event:
    :return:
    """
    shot_id = event['entity']['id']
    #project_id = event['project']['id']

    # Use the existing sgtk auth user to get a manager
    manager = sgtk.bootstrap.ToolkitManager(sgtk.get_authenticated_user())
    # This plugin_id must be configured so we get the appropriate per-project config
    manager.plugin_id = "sghs."
    logger.debug("Manager object:\n%s" % str(manager))

    logger.debug("Trying to bootstrap shot ID %s" % shot_id)
    engine = manager.bootstrap_engine("tk-shell", entity={"type": "Shot", "id": shot_id})
    logger.debug("Engine object:\n%s" % str(engine))
    # import now that we have bootstrapped an entity-specific sgtk
    import tank.errors

    # use the work_shot_area_template from the engine-specific sgtk
    # TODO: figure out the name of the template we want and use that
    work_shot_area_template = engine.sgtk.templates[config['shothammer']['SGHS_PATH_TEMPLATE']]
    logger.debug("work_shot_area_template: %s" % str(work_shot_area_template))

    # set up filters and fields to pass to find_one so we get the right dict
    filters = [["id", "is", shot_id]]
    fields = ["id", "type", "code", "sg_episode", "sg_sequence"]
    full_shot = engine.shotgun.find_one("Shot", filters=filters, fields=fields)
    logger.debug("Full shot: %s" % str(full_shot))

    try:
        Shot = full_shot['code']
    except TypeError as e:
        logger.warning("TypeError trying to get Shot from full_shot: %s" % repr(e))
        Shot = None
    try:
        Sequence = full_shot['sg_sequence']['name']
    except TypeError as e:
        logger.warning("TypeError trying to get Sequence from full_shot: %s" % repr(e))
        Sequence = None
    try:
        Episode = full_shot['sg_episode']['name']
    except TypeError as e:
        logger.warning("TypeError trying to get Episode from full_shot: %s" % repr(e))
        Episode = None
    except KeyError as e:
        logger.warning("KeyError trying to get Episode from full_shot: %s" % repr(e))
        Episode = ''

    # compose a dict and feed it to apply_fields to get a path
    print("Shot: %s" % Shot)
    print("Sequence: %s" % Sequence)
    print("Episode: %s" % Episode)
    try:
        result = work_shot_area_template.apply_fields({'Shot':Shot,
                                                       'Sequence':Sequence,
                                                       # 'Episode': Episode,
                                                       })
        logger.debug("Full path: %s" % result)
    except tank.errors.TankError as e:
        # We didn't get a valid path for some reason, likely because we couldn't complete the template provided
        result = None
        msg = str(e)
        # Use the timestamp on the event itself
        event_time = event['created_at']
        date_string = event_time.strftime("%Y-%m-%d_%H-%M-%S")
        # filename includes the shot_id and the timestamp of the event
        filename = "shot_id-%s-%s.pickle" % (shot_id, date_string)
        logger.error("Unable to apply all required fields, saving event as %s\nException message: %s"
                     % (filename, msg))
        # save a pickle of the event for later analysis
        capture_event(event, filename)

    # clean up the engine before returning
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
