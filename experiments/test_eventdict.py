import sys, os
import pickle
import yaml
import pprint

from unittest import TestCase

pp = pprint.PrettyPrinter(indent=4)

with open('shothammer_config.yml') as F:
    config = yaml.load(F, Loader=yaml.FullLoader)

pp.pprint(config)

TEMPLATES = {"Shot": ['shot_template_1', 'shot_template_2'],
             "Sequence": ['sequence_template_1', 'sequence_template_2'],
             "Task": ['task_template_1', 'task_template_2'],
             }
with open('../sghs_event_sequence.pickle', 'rb') as F:
    tag_change_sequence = pickle.load(F)

with open('../sghs_event_shot.pickle', 'rb') as F:
    tag_change_shot = pickle.load(F)

with open('../sghs_event_task.pickle', 'rb') as F:
    tag_change_task = pickle.load(F)

print(TEMPLATES.keys())

print(tag_change_shot)
print(tag_change_sequence)
print(tag_change_task)

for key in TEMPLATES.keys():
    for template in TEMPLATES[key]:
        print("Bootstrapping template %s" % template)

# insert the correct path for sgtk from the config.ini then import it
sys.path.insert(0, config['SG_TOOLKIT'])
import sgtk

sgtk.LogManager().initialize_custom_handler()
sgtk.LogManager().global_debug = False

sa = sgtk.authentication.ShotgunAuthenticator()
# Create a user object
user = sa.create_script_user(api_script=config['SGHS_NAME'],
                             api_key=config['SGHS_KEY'],
                             host=os.environ['SG_ED_SITE_URL'])


sgtk.set_authenticated_user(user)


# Re-bootstrap the engine under the correct context...
mgr = sgtk.bootstrap.ToolkitManager(sgtk.get_authenticated_user())
mgr.plugin_id = "sghs."
# mgr.pipeline_configuration = 'distro_rez'

print("here is the manager object:")
print(mgr)

def bootstrap_shot(mgr):
    # Now that we've got an initial sgtk bootstrap we should be able to pull per-project configs
    # the below needs to be in a plugin's callback function so that it gets called for every matching event
    shot_id = 862
    # bootstrap the specific project
    print("trying to bootstrap shot ID %s" % shot_id)
    # engine = mgr.bootstrap_engine("tk-shell", entity={"type": "Project", "id": project_id})
    engine = mgr.bootstrap_engine("tk-shell", entity={"type": "Shot", "id": shot_id})

    # now we're bootstrapped, we can do what we need to do
    print("here is the engine object: %s" % str(engine))

    # Get the shot_root_template from the new engine.sgtk
    shot_root_template = engine.sgtk.templates["shot_root"]

    print("shot_root_template: %s" % str(shot_root_template))

    print("shot_root_template.keys: %s" % str(shot_root_template.keys))
    print("shot_root_template.definition: %s" % str(shot_root_template.definition))

    # set up the filter and the fields to pass to find_one
    filters = [["id", "is", shot_id]]
    fields = ["id", "type", "code", "sg_episode", "sg_sequence"]

    # get full_shot
    full_shot = engine.shotgun.find_one("Shot", filters=filters, fields=fields)

    print("full_shot:\n%s" % str(full_shot))
    Shot = full_shot['code']
    Sequence = full_shot['sg_sequence']['name']
    # Episode = full_shot['sg_episode']['name']

    # apply_fields to get the whole path
    print("shot_root_template.apply_fields():\n%s" %
        str(shot_root_template.apply_fields({'Shot':Shot,
                                            'Sequence':Sequence,
                                            # 'Episode':Episode,
                                            })))
    # print(shot_root_template.apply_fields({'Episode':'ep888', 'Shot':'sh0000'}))

    # fields = project_context.as_template_fields(shot_root_template)
    # fields = engine.context.as_template_fields(shot_root_template)
    # print(fields)

    # now we're done, so we can destroy the engine and await another callback
    engine.destroy()

def bootstrap_sequence(mgr):
    # Now that we've got an initial sgtk bootstrap we should be able to pull per-project configs
    # the below needs to be in a plugin's callback function so that it gets called for every matching event
    sequence_id = 23
    # bootstrap the specific project
    print("trying to bootstrap sequence ID %s" % sequence_id)
    engine = mgr.bootstrap_engine("tk-shell", entity={"type": "Sequence", "id": sequence_id})

    # now we're bootstrapped, we can do what we need to do
    print("here is the engine object: %s" % str(engine))

    # Get the shot_root_template from the new engine.sgtk
    sequence_root_template = engine.sgtk.templates["sequence_root"]

    print("sequence_root_template: %s" % str(sequence_root_template))

    print("sequence_root_template.keys: %s" % str(sequence_root_template.keys))
    print("sequence_root_template.definition: %s" % str(sequence_root_template.definition))

    # set up the filter and the fields to pass to find_one
    filters = [["id", "is", sequence_id]]
    fields = ["id", "type", "code", "sg_episode", "sg_sequence"]

    # get full_sequence
    full_sequence = engine.shotgun.find_one("Sequence", filters=filters, fields=fields)

    print("full_sequence:\n%s" % str(full_sequence))
    # Shot = full_shot['code']
    Sequence = full_sequence['code']
    # Episode = full_shot['sg_episode']['name']

    # apply_fields to get the whole path
    print("sequence_root_template.apply_fields():\n%s" %
        str(sequence_root_template.apply_fields({# 'Shot':Shot,
                                            'Sequence':Sequence,
                                            # 'Episode':Episode,
                                            })))
    # print(shot_root_template.apply_fields({'Episode':'ep888', 'Shot':'sh0000'}))

    # fields = project_context.as_template_fields(shot_root_template)
    # fields = engine.context.as_template_fields(shot_root_template)
    # print(fields)

    # now we're done, so we can destroy the engine and await another callback
    engine.destroy()

def bootstrap_task(mgr):
    # Now that we've got an initial sgtk bootstrap we should be able to pull per-project configs
    # the below needs to be in a plugin's callback function so that it gets called for every matching event
    # task_id = 3684
    task_id = 3697
    # bootstrap the specific project
    print("trying to bootstrap task ID %s" % task_id)
    engine = mgr.bootstrap_engine("tk-shell", entity={"type": "Task", "id": task_id})

    # now we're bootstrapped, we can do what we need to do
    print("here is the engine object: %s" % str(engine))

    # Get the shot_root_template from the new engine.sgtk
    task_root_template = engine.sgtk.templates["task_template_1"]

    print("task_root_template: %s" % str(task_root_template))

    print("task_root_template.keys: %s" % str(task_root_template.keys))
    print("task_root_template.definition: %s" % str(task_root_template.definition))

    # set up the filter and the fields to pass to find_one
    filters = [["id", "is", task_id]]
    fields = ["id", "type", "entity", "project", "step", "template_task", "content"]

    # get full_task
    full_task = engine.shotgun.find_one("Task", filters=filters, fields=fields)
    print("full_task:\n%s" % str(full_task))

    # get step shortname ({Step} in a path template)
    step = engine.shotgun.find_one("Step", [['code', 'is', full_task['step']['name']]], ["code", "short_name"])
    step_shortname = step['short_name']
    print("Step short_name: %s" % step_shortname)

    # get task name ({task_name})
    task_name = full_task['content']
    print("task_name: %s" % task_name)

    # get Shot from Task
    fields = ["id", "type", "code", "sg_episode", "sg_sequence"]
    related_shot = engine.shotgun.find_one("Shot", [['id', 'is', full_task['entity']['id']]], fields)
    print("Task-related shot: %s" % related_shot)
    shot_code = related_shot['code']
    print("Shot code: %s" % shot_code)

    # get Sequence from Shot
    related_sequence = related_shot['sg_sequence']['name']
    print("Task-related sequence code: %s" % related_sequence)

    # fill out the template
    template = engine.sgtk.templates["task_template_1"]
    print(template)
    result = template.apply_fields({'Sequence': related_sequence,
                                    'Shot': shot_code,
                                    'Step': step_shortname,
                                    'task_name': task_name,
                                    })
    print(result)
    # task = full_task['code']

    # task_name = full_task['step']['name']
    # print("Task name: %s" % task_name)

    # apply_fields to get the whole path
    # print("task_root_template.apply_fields():\n%s" %
    #     str(task_root_template.apply_fields({# 'Shot':Shot,
    #                                         'task':Sequence,
    #                                         # 'Episode':Episode,
    #                                         })))
    # print(shot_root_template.apply_fields({'Episode':'ep888', 'Shot':'sh0000'}))

    # fields = project_context.as_template_fields(shot_root_template)
    # fields = engine.context.as_template_fields(shot_root_template)
    # print(fields)

    # now we're done, so we can destroy the engine and await another callback
    engine.destroy()

# bootstrap_shot(mgr)
# bootstrap_sequence(mgr)
bootstrap_task(mgr)
