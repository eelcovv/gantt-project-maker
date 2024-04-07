=========
Changelog
=========

Version 0.4.2
=============
- Added new Excel format output to collect all the projects per contributor
- Added possibility to assign number of hours to each contributor's task
- Added summations of hours per contributor

Version 0.4.0
=============
- Added option --suffix in order add a extra suffix to the filename
- Added option --project in order to filter on the main projects which are going to be included
- Added replacement variable for both titles and date/time. Now a variable 'my_variable'
  can be defined which replaces all occurrences of {{ my_variable }}

Version 0.3.7
=============
- Added option --vacations in order to export a gantt chart of the vacations per employer
- Added option --collaps_tasks in order to collaps the tasks per project to one task in order to simplify the output
- Improved some feedback at errors with missing employees
- if --output_filename is given on the command line, do not add employees to the base
- bug fix on quarter label in excel output
- bug fix on pdf output of resources

Version 0.2.4
=============
- Added --pdf option in order to convert svg file into pdf as well

Version 0.2.3
=============
- Added possibility to add margin_left and margin_right property to project to prevent cluttering of labels
- Added possibility to filter on one or more employees to only display the project of the selected employees
- Change default font size for level 0 and 1 in project plan
- Add name of employee to title if a filter was used

Version 0.1.9
=============
- In resources overview, task colors now match the colors in the project overview
- The task color can now explicitly be given. Default task color matches the project color.
- Started to update the documentation. Still needs to be finished


Version 0.1.7
=============
- Improved colouring of resources schema

Version 0.1.6
=============
- Added some basic checks on the tasks start and end dates to be more specifics on errors

Version 0.1.5
=============
- Bug today reference fixed
- Vacation now correctly added
- Font properties can be specified in setting file
- dayfist can be set to false

Version 0.1.3
=============

- Dynamic columns added
- First version of Gantt Project maker
- First bug fixes established
