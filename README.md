Shothammer - a custom file metadata integration between Hammerspace and Shotgrid

Maintainer: mike.bott@hammerspace.com

Shothammer is a ShotgridEvents plugin that can respond to status change events by setting
custom metadata on files and directories. This metadata can be used to drive data locality
using SmartObjectives on a Hammerspace Global Data Environment.

#Dependencies
1. Shotgrid event daemon installed
2. Hammerspace Toolkit (hstk) installed
3. Hammerspace file system mounted
4. Shotgrid event daemon configured including location of shothammer.py

#Configuration
1. shothammer_config.ini adjusted to fit environment
2. shothammer_config.ini copied to shotgunEvents dir as a sibling of shotgunEventDaemon.py 

