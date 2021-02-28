![PythonBaseApp-Logo](python_base_app/static/icons/icon-python-base-app-128x128.png)

# Python Application Framework `python_base_app`

## Overview

`python_base_app` is a simple framework for Python applications with a web frontend using 
[Flask](https://palletsprojects.com/p/flask/). It is used by [LitleBrother](https://github.com/marcus67/little_brother).

## Change History 

See [here](https://github.com/marcus67/python_base_app/blob/master/CHANGES.md)

## GitHub Status

<A HREF="https://github.com/marcus67/python_base_app">
<IMG SRC="https://img.shields.io/github/forks/marcus67/python_base_app.svg?label=forks"></A> 
<A HREF="https://github.com/marcus67/python_base_app/stargazers">
<IMG SRC="https://img.shields.io/github/stars/marcus67/python_base_app.svg?label=stars"></A> 
<A HREF="https://github.com/marcus67/python_base_app/watchers">
<IMG SRC="https://img.shields.io/github/watchers/marcus67/python_base_app.svg?label=watchers"></A> 
<A HREF="https://github.com/marcus67/python_base_app/issues">
<IMG SRC="https://img.shields.io/github/issues/marcus67/python_base_app.svg"></A> 
<A HREF="https://github.com/marcus67/python_base_app/pulls">
<IMG SRC="https://img.shields.io/github/issues-pr/marcus67/python_base_app.svg"></A>

## Continuous Integration Status Overview

| Status              | Master                                                                                                                                                                                                                                                                                                                                                          | Release                                                                                                                                                                                   |
|:------------------- |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CircleCI            | <A HREF="https://circleci.com/gh/marcus67/python_base_app/tree/master"><IMG SRC="https://img.shields.io/circleci/project/github/marcus67/python_base_app/master.svg?label=master"></A>                                                                                                                                                                          | <A HREF="https://circleci.com/gh/marcus67/python_base_app/tree/release"><IMG SRC="https://img.shields.io/circleci/project/github/marcus67/python_base_app/release.svg?label=release"></A> |
| Test Coverage       | <A HREF="https://codecov.io/gh/marcus67/python_base_app/branch/master"><IMG SRC="https://img.shields.io/codecov/c/github/marcus67/python_base_app.svg?label=master"></A>                                                                                                                                                                                        | <A HREF="https://codecov.io/gh/marcus67/python_base_app/branch/release"><IMG SRC="https://img.shields.io/codecov/c/github/marcus67/python_base_app/release.svg?label=release"></A>        | 
| Snyk Vulnerability  | <a href="https://snyk.io/test/github/marcus67/python_base_app?targetFile=requirements.txt"><img src="https://snyk.io/test/github/marcus67/python_base_app/badge.svg?targetFile=requirements.txt" alt="Known Vulnerabilities" data-canonical-src="https://snyk.io/test/github/marcus67/python_base_app?targetFile=requirements.txt" style="max-width:100%;"></a> | not available                                                                                                                                                                             |
| Codacy Code Quality | <a href="https://www.codacy.com/app/marcus67/python_base_app?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=marcus67/python_base_app&amp;utm_campaign=Badge_Grade"><img src="https://api.codacy.com/project/badge/Grade/3e3130c1c450404db9b16e10ab8af7fd"/></a>                                                                                  | not available                                                                                                                                                                             |

Note: The vulnerability status is derived from the Python PIP packages found in `requirements.txt`.

## Features

`python_base_app` has the following features:

*   (Base) classes for handling
    *   configuration,
    *   HTTP server (Flask with optional authentication (simple configured admin password and LDAP)),
    *   helper classes for Flask WTF,
    *   actuator providing a health endpoint,
    *   helpers for notification using popups or audio messages,
    *   REST access,
    *   logging,
    *   daemon processes
    *   wrapper for pinging other servers with integration of [ProxyPing](https://github.com/marcus67/proxy_ping)

*   Templates and generator (Jinja2) for creating
    *   Debian packages for Python applications,
    *   PIP packages (build, test, publish),
    *   control files for continous integration platforms CircleCI and GitLab,
    *   control file abalyzing test coverage using Python module `coverage`
     
## Caveats

The framework is far from perfect. Some major caveats are listed here and/or in the 
issue list on GitHub (see [here](https://github.com/marcus67/python_base_app/issues)).
