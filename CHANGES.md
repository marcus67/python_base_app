# Change History 

This document lists all changes of `python_base_app` with the most recent changes at the top.

## Version 0.2.33 (January 30th, 2022)

* Improve testing of `Pinger`
* Deactivate physical ping tests with environment variable `NO_PING`

## Version 0.2.32 (January 21st, 2022)

* Support `xvfb` for testing
* Change test image to `marcusrickert/docker-python-app:latest`
* Export env variable `DISPLAY`
* Closes #158 of `LittleBrother`, see [here](https://github.com/marcus67/little_brother/issues/158)

## Version 0.2.31 (January 18th, 2022)

* Put Debian installation packages into `/var/lib/<app-name>` in order to prevent collisions due to
  several applications using the same packages
* Use `pip3.sh` to retrieve packages during Debian post install to allow for download of development versions.

## Version 0.2.30 (January 8th, 2022)

* Add pip3 calls for packages required during build and publish
* Allow setting of user and URL for PyPi repository
* Add publishing of PyPi packages to GitLab-CI configuration
* Add generated `pip3.sh` script to download packages from private PyPi indexes 

## Version 0.2.29 (January 8th, 2022)

* Add jinja2 templates to PIP package

## Version 0.2.28 (January 2nd, 2022)

* Clean deployment to test.pypi.org

## Version 0.2.27 (January 1st, 2022)

* Cleanly handle stdout of ping command
* Generate extra package dependencies in Debian control file 
* Add CODE_OF_CONDUCT.md and CONTRIBUTING.md
* Execute daemon reload in Debian post-install script

## Version 0.2.26 (October 12th, 2021)

* Exclude .md files from Codacy checks
* Add support for snap runtime detection

## Version 0.2.25 (September 14th, 2021)

* Add improved HTTP header options using package `secure`
* Set session protection of login manager to `strong`
* Add utility function `get_today`
* Closes [LittleBrother issue 144](https://github.com/marcus67/little_brother/issues/144)
* Closes [LittleBrother issue 138](https://github.com/marcus67/little_brother/issues/138)
* Exclude alembic files from coverage analysis
* Fix alembic at 1.5.8
* Remove German logging messages
* Closes [LittleBrother issue 154](https://github.com/marcus67/little_brother/issues/154)
* Upgrade WTForms to version 3.0.0a1

## Version 0.2.24 (August 16th, 2021)

*   Add option `--allow-releaseinfo-change` to `apt-get update`

## Version 0.2.23 (August 15th, 2021)

*   Update Italian localization
*   Add missing dependencies to `requirements.txt`

## Version 0.2.22 (July 2nd, 2021)

*   Don't require users in /etc/passwd to have actual passwords in order to be used for the new user list

## Version 0.2.21 (June 13th, 2021)

*   New exception `RangeNotSatisfiableException`
*   Add support for parameters for requests methods "POST", "PUT", and "DELETE"
*   Support for https://github.com/marcus67/little_brother/issues/130

## Version 0.2.20 (May 24th, 2021)

*   Use new CSRF handling

## Version 0.2.19 (May 22nd, 2021)

*   Closes #12, see [here](https://github.com/marcus67/python_base_app/issues/12) 

## Version 0.2.18 (April 3nd, 2021)

*   Moved `copy_attributes` and `create_class_instance` from LittleBrother to `tools.py`
*   Added method `compare_objects` in `tools.py`
*   Moved `check_list_length` from LittleBrother to `base_test.py` 
*   Added support for SonarQube analysis (script generation)
*   Read `.dev-env-settings.sh` in `test-app.sh`
*   Don't assume `BaseWebServer` to have a blueprint
*   Show version details for Chrome/Selenium test environment 

## Version 0.2.17 (April 2nd, 2021)

*   Make test suite compile on MacOS

## Version 0.2.16 (February 27th, 2021)

*   Add Debian packages in `python_base_app/templates/debian_control.template.conf` to enable loading 
    of Python module `python-ldap`

*   Move functionality from `UnixUserHandler` to `BaseUserHandler`

*   Add new class `LdapUserHandler` for authorization and authentication with an LDAP server

*   Exclude template Python files  `.coveragerc`

*   Repair call of `coverage`

*   Add test cases for class `UnixUserHandler`

## Version 0.2.15 (February 23rd, 2021)

*   Add test case for health API 
*   Add babel-login to requirements.txt (triggered by new test case)
*   Add dependency on package `some_flask_helpers`
*   Add helper function `get_dns_name_by_ip_address()`

## Version 0.2.14 (February 12th, 2021)

*   Add class `Pinger` 
*   Exclude `sudo` package when not needed

## Version 0.2.13 (January 31st, 2021)

*   Fix usage of local make and export JOBS for WAF framework (just in case)

## Version 0.2.12 (January 31st, 2021)

*   Use local `make` script to set option `-j` according to `MAX_CPUS` 

## Version 0.2.11 (January 30th, 2021)

*   Check ENV variable `MAX_CPUS` and forward it as install option `pip` as `--cpus` to limit the maximum number of parallel threads

## Version 0.2.10 (January 25th, 2021)

*   Simple beacon for outputting message during execution of long generated scripts (fix CircleCI timeout issue)

## Version 0.2.8 (January 9th, 2021)

*   Provide helper function to check if running in Docker container

## Version 0.2.7 (January 2nd, 2021)

*   Make deployment to PyPi dependent on successful deployment to Docker registry  

## Version 0.2.6 (January 2nd, 2021)

*   Support alternate Docker registries in CI/CD environment

## Version 0.2.5 (November 28th, 2020)

*   Set owner of sudoers file in Debian postinstallation script
*   'Login' -> 'Username' in failed login message
*   Upgrade all required PyPi packages

## Version 0.2.4 (September 30th, 2020)

*   Update names of some Debian packages
*   Hide secrets in logged options

## Version 0.2.3 (September 14th, 2020)

*   Generate generic installation script `generic-install.sh` (using the same template as the Debian `postinst` script)
*   Add documentation page about non-Debian installation
*   Use more compatible commands and options to add users and groups in Debian `postinst` script

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
 