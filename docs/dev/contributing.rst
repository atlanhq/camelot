.. _contributing:

Contributor's Guide
===================

The preferred way to contribute to Camelot is to fork this repository, and then submit a "pull request" (PR):

1. Create an account on GitHub if you don't already have one.

2. Fork the project repository: click on the ‘Fork’ button near the top of the page. This creates a copy of the code under your account on the GitHub server.

3. Clone this copy to your local disk.
4. Create a branch to hold your changes::

    git checkout -b my-feature

  and start making changes. Never work in the `master` branch!

5. Work on this copy, on your computer, using Git to do the version control. When you’re done editing, do::

    $ git add modified_files
    $ git commit

  to record your changes in Git, then push them to GitHub with::

    $ git push -u origin my-feature

Finally, go to the web page of the your fork of the camelot repo, and click ‘Pull request’ to send your changes to the maintainers for review.

Code
----

You can check the latest sources with the command::

    git clone https://github.com/socialcopsdev/camelot.git

Contributing
------------

See :doc:`Contributing guidelines <contributing>`.

Testing
-------

::

    python setup.py test