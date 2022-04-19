Shothammer - a custom file metadata integration between Hammerspace and Shotgrid

Maintainer: mike.bott@hammerspace.com

Shothammer is a ShotgridEvents plugin that can respond to status change events by setting
custom metadata on files and directories. This metadata can be used to drive data placement and location
using SmartObjectives on a Hammerspace Global Data Environment.

Currently, shothammer.py watches for tags added to or removed from shots in Shotgrid. When 
it sees tags in the allowed namespace (currently tags named `SGHS_*`) it adds them as
Hammerspace keywords to the root of the shot folder on disk. The tag schema is controlled in Shotgrid,
and they are passed through directly as keywords.

It finds the shot folder by using a per-project Pipeline Configuration fed to it by Shotgrid. This config can be specified
in Shotgrid by adding the plugin id `sghs.` to the specific pipeline configuration for the project.

Currently shothammer requests the template specified in `shothammer_config.ini` as `SGHS_PATH_TEMPLATE`.

sghs is intended to grow as a package over time with multiple plugin modules that do different things with Shotgrid's
events.

#Prerequisites
1. Shotgrid API installed and configured 
2. Shotgrid event daemon installed and configured
3. Hammerspace Toolkit (hstk) installed: `$ pip install hstk`
4. Hammerspace file system mounted

#Installation
1. Clone this repository `git clone https://github.com/mabott/sghs.git`
2. Copy or hard link shothammer.py to your shotgunEvents plugin directory.

#Configuration
1. Adjust shothammer_config.ini to fit environment (paths, fixing namespace overlap, etc.)
2. Copy shothammer_config.ini to shotgunEvents working directory 
3. One or more Hammerspace clusters set up with keyword-based objectives to drive data placement

#Troubleshooting
Given the appropriate values in shothammer_config.ini, the tests in test_shothammer.py should pass. If the plugin gets
disabled by shotgunEvents then there is a fatal problem somewhere. Running the tests using nose or your favorite IDE
should give enough details to show what is broken.

##Things to check:
1. Make sure hstk is installed in the same environment running shotgunEvents.
2. Make sure the authentication information for Shotgrid is complete, both name and application key.
3. 