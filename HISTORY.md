Release History
===============

master
------

* Downgrade numpy version from 1.15.2 to 1.13.3.
* Add requirements.txt for readthedocs.

**Improvements**

* [#139](https://github.com/socialcopsdev/camelot/issues/139) Add suppress_warnings flag. [#155](https://github.com/socialcopsdev/camelot/pull/155) by [Jonathan Lloyd](https://github.com/jonathanlloyd).
    * Warnings raised by Camelot can now be suppressed by passing `suppress_warnings=True` to `read_pdf` or `--quiet` to the command-line interface.
* [#154](https://github.com/socialcopsdev/camelot/issues/154) The CLI can now be run using `python -m`. Try `python -m camelot --help`. [#159](https://github.com/socialcopsdev/camelot/pull/159) by [Parth P Panchal](https://github.com/pqrth).
* [#114](https://github.com/socialcopsdev/camelot/issues/114) Add Makefile and make codecov run only once. [#132](https://github.com/socialcopsdev/camelot/pull/132) by [Vaibhav Mule](https://github.com/vaibhavmule).
* Add .editorconfig. [#151](https://github.com/socialcopsdev/camelot/pull/151) by [KOLANICH](https://github.com/KOLANICH).
* [#165](https://github.com/socialcopsdev/camelot/issues/165) Rename `table_area` to `table_areas`. [#171](https://github.com/socialcopsdev/camelot/pull/171) by [Parth P Panchal](https://github.com/pqrth).

**Bugfixes**

* Raise error if the ghostscript executable is not on the PATH variable. [#166](https://github.com/socialcopsdev/camelot/pull/166) by Vinayak Mehta.
* Convert filename to lowercase to check for PDF extension. [#169](https://github.com/socialcopsdev/camelot/pull/169) by [Vinicius Mesel](https://github.com/vmesel).

**Documentation**

* Add "Using conda" section to installation instructions.
* Add readthedocs badge.

0.2.3 (2018-10-08)
------------------

* Remove hard dependencies on requirements versions.

0.2.2 (2018-10-08)
------------------

**Bugfixes**

* Move opencv-python to extra\_requires. [#134](https://github.com/socialcopsdev/camelot/pull/134) by Vinayak Mehta.

0.2.1 (2018-10-05)
------------------

**Bugfixes**

* [#121](https://github.com/socialcopsdev/camelot/issues/121) Fix ghostscript subprocess call for Windows. [#124](https://github.com/socialcopsdev/camelot/pull/124) by Vinayak Mehta.

**Improvements**

* [#123](https://github.com/socialcopsdev/camelot/issues/123) Make PEP8 compatible. [#125](https://github.com/socialcopsdev/camelot/pull/125) by [Oshawk](https://github.com/Oshawk).
* [#110](https://github.com/socialcopsdev/camelot/issues/110) Add more tests. Coverage is now at 84%!
    * Add tests for `__repr__`. [#128](https://github.com/socialcopsdev/camelot/pull/128) by [Vaibhav Mule](https://github.com/vaibhavmule).
    * Add tests for CLI. [#122](https://github.com/socialcopsdev/camelot/pull/122) by [Vaibhav Mule](https://github.com/vaibhavmule) and [#117](https://github.com/socialcopsdev/camelot/pull/117) by Vinayak Mehta.
    * Add tests for errors/warnings. [#113](https://github.com/socialcopsdev/camelot/pull/113) by Vinayak Mehta.
    * Add tests for output formats and parser kwargs. [#126](https://github.com/socialcopsdev/camelot/pull/126) by Vinayak Mehta.
* Add Python 3.5 and 3.7 support. [#119](https://github.com/socialcopsdev/camelot/pull/119) by Vinayak Mehta.
* Add logging and warnings.

**Documentation**

* Copyedit all documentation. [#112](https://github.com/socialcopsdev/camelot/pull/112) by [Christine Garcia](https://github.com/christinegarcia).
* [#115](https://github.com/socialcopsdev/camelot/issues/115) Update issue labels in contributor's guide. [#116](https://github.com/socialcopsdev/camelot/pull/116) by [Johnny Metz](https://github.com/johnnymetz).
* Update installation instructions for Windows. [#124](https://github.com/socialcopsdev/camelot/pull/124) by Vinayak Mehta.

**Note**: This release also bumps the version for numpy from 1.13.3 to 1.15.2 and adds a MANIFEST.in. Also, openpyxl==2.5.8 is a new requirement and pytest-cov==2.6.0 is a new dev requirement.

0.2.0 (2018-09-28)
------------------

**Improvements**

* [#81](https://github.com/socialcopsdev/camelot/issues/81) Add Python 3.6 support. [#109](https://github.com/socialcopsdev/camelot/pull/109) by Vinayak Mehta.

0.1.2 (2018-09-25)
------------------

**Improvements**

* [#85](https://github.com/socialcopsdev/camelot/issues/85) Add Travis and Codecov.

0.1.1 (2018-09-24)
------------------

**Documentation**

* Add documentation fixes.

0.1.0 (2018-09-24)
------------------

* Rebirth!
