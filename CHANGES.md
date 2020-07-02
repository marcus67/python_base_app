# Change History 

This document lists all changes of `python_base_app` with the most recent changes at the top.

## Version 0.2.0 (May/June, 2020)

*   Add classes BaseUserHandler and UnixUserHandler
*   Optional deployment of an apparmor configuration file
*   Optional deployment of a tmpfiles.d configuration file

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
 