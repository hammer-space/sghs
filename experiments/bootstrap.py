import sys
import os

# insert the correct path for sgtk
sys.path.insert(0, "C:/shotgrid-hammerspace/tk-core/python")
import sgtk

def project_id_from_event(event) -> int:
    return event['project']['id']

sa = sgtk.authentication.ShotgunAuthenticator()
# Create a user object
user = sa.create_script_user(api_script=os.environ['SGDAEMON_LOGARGS_NAME'],
                             api_key=os.environ['SGDAEMON_LOGARGS_KEY'],
                             host=os.environ['SG_ED_SITE_URL'])
sgtk.set_authenticated_user(user)

mgr = sgtk.bootstrap.ToolkitManager(sg_user=user)
mgr.plugin_id = "basic."


# Now that we've got an initial sgtk bootstrap we should be able to pull per-project configs
# the below needs to be in the callback function so that it gets called for every matching event
# Get the project id from the event
project_id = project_id_from_event(event)
# bootstrap the specific project
engine = mgr.bootstrap_engine("tk-shell", entity={"type": "Project", "id": project_id})
# now we're bootstrapped, we can do what we need to do

# Get the path template
# Get any info we need from the event
# fill the template
# use that path to recursively set hammerspace keywords for each of the new shotgrid tags on the target
# use that path to recursively remove hammerspace keywords for each of the removed shotgrid tags on the target

# now we're done, so we can destroy the engine and await another callback
engine.destroy()