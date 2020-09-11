# Change History 

This document lists all changes of `python_base_app` with the most recent changes at the top.

## Version 0.2.2 (September 12th, 2020)

*   First version of Croatian localization (incomplete and without special characters)
*   Support different PyPi targets depending on CI build branch 
*   Publish master branch to [PyPi-Test](https://test.pypi.org/)

## Version 0.2.1 (September 6th, 2020)

*   Improve logging when opening web server

## Version 0.2.1 (July 18th, 2020)

*   Support for saving configurations back to file

## Version 0.2.0 (July 18th, 2020)

*   Add classes BaseUserHandler and UnixUserHandler
*   Optional deployment of an apparmor configuration file
*   Optional deployment of a tmpfiles.d configuration file
*   Support for template in Debian configuration 
*   Remove old Debian file tree before build package (to remove obsolete files)

## Version 0.1.11 (June 7th, 2020)

*   Add Spanish localization (locale "es")

## Version 0.1.10 (May 23rd, 2020)

*   Add Danish localization (locale "da")

## Version 0.1.9 (May 5th, 2020)

*   Integrate compilation of binary Babel files (*.mo) into BUILD
*   Provide translations of texts in python_base_app 
*   Provide gettext function to call Babel
*   Closes #6, see [here](https://github.com/marcus67/python_base_app/issues/6)
*   Create python_base_app/settings.py to make settings available to CI process
*   Add tests for module `base_ci_toolbox`

## Version 0.1.8 (April 18th, 2020)

*   Add simple helper class TimingContext 
*   Provide access method for retrieving most recent value of class MovingAverage
 
## Version 0.1.7 (April 13th, 2020)

*   Removed some historic references to LittleBrother
*   Integrate original PYTHONPATH while testing 
 
## Version 0.1.6 (April 11th, 2020)

*   Moved helper classes for audio handling from LittleBrother to python_base_app
*   Integrated pytest tests
 