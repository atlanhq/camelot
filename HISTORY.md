Release History
===============

master
------

0.4.1 (2018-12-05)
------------------

**Bugfixes**

* Add chardet to `install_requires` to fix [#210](https://github.com/socialcopsdev/camelot/issues/210). More details in [pdfminer.six#213](https://github.com/pdfminer/pdfminer.six/issues/213).

0.4.0 (2018-11-23)
------------------

**Improvements**

* [#102](https://github.com/socialcopsdev/camelot/issues/102) Detect tables automatically when Stream is used. [#206](https://github.com/socialcopsdev/camelot/pull/206) Add implementation of Anssi Nurminen's table detection algorithm by Vinayak Mehta.

0.3.2 (2018-11-04)
------------------

**Improvements**

* [#186](https://github.com/socialcopsdev/camelot/issues/186) Add `_bbox` attribute to table. [#193](https://github.com/socialcopsdev/camelot/pull/193) by Vinayak Mehta.
    * You can use `table._bbox` to get coordinates of the detected table.

0.3.1 (2018-11-02)
------------------

**Improvements**

* Matplotlib is now an optional requirement. [#190](https://github.com/socialcopsdev/camelot/pull/190) by Vinayak Mehta.
    * You can install it using `$ pip install camelot-py[plot]`.
* [#127](https://github.com/socialcopsdev/camelot/issues/127) Add tests for plotting. Coverage is now at 87%! [#179](https://github.com/socialcopsdev/camelot/pull/179) by [Suyash Behera](https://github.com/Suyash458).

0.3.0 (2018-10-28)
------------------

**Improvements**

* [#162](https://github.com/socialcopsdev/camelot/issues/162) Add password keyword argument. [#180](https://github.com/socialcopsdev/camelot/pull/180) by [rbares](https://github.com/rbares).
    * An encrypted PDF can now be decrypted by passing `password='<PASSWORD>'` to `read_pdf` or `--password <PASSWORD>` to the command-line interface. (Limited encryption algorithm support from PyPDF2.)
* [#139](https://github.com/socialcopsdev/camelot/issues/139) Add suppress_warnings keyword argument. [#155](https://github.com/socialcopsdev/camelot/pull/155) by [Jonathan Lloyd](https://github.com/jonathanlloyd).
    * Warnings raised by Camelot can now be suppressed by passing `suppress_warnings=True` to `read_pdf` or `--quiet` to the command-line interface.
* [#154](https://github.com/socialcopsdev/camelot/issues/154) The CLI can now be run using `python -m`. Try `python -m camelot --help`. [#159](https://github.com/socialcopsdev/camelot/pull/159) by [Parth P Panchal](https://github.com/pqrth).
* [#165](https://github.com/socialcopsdev/camelot/issues/165) Rename `table_area` to `table_areas`. [#171](https://github.com/socialcopsdev/camelot/pull/171) by [Parth P Panchal](https://github.com/pqrth).

**Bugfixes**

* Raise error if the ghostscript executable is not on the PATH variable. [#166](https://github.com/socialcopsdev/camelot/pull/166) by Vinayak Mehta.
* Convert filename to lowercase to check for PDF extension. [#169](https://github.com/socialcopsdev/camelot/pull/169) by [Vinicius Mesel](https://github.com/vmesel).

**Files**

* [#114](https://github.com/socialcopsdev/camelot/issues/114) Add Makefile and make codecov run only once. [#132](https://github.com/socialcopsdev/camelot/pull/132) by [Vaibhav Mule](https://github.com/vaibhavmule).
* Add .editorconfig. [#151](https://github.com/socialcopsdev/camelot/pull/151) by [KOLANICH](https://github.com/KOLANICH).
* Downgrade numpy version from 1.15.2 to 1.13.3.
* Add requirements.txt for readthedocs.

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
