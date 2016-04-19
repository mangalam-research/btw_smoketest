This is a very ad-hoc tool designed to test the BTW site and its
siblings.

You would typically invoke it like this from the top of the directory
that contains this README::

    $ scrapy crawl btw [-a url=something...]

Please read the documentation in ``btw_smoketest/spiders/btw.py`` to
see what parameters can be passed to the spider with ``-a``.

The spider crawls the site given in the ``url`` parameter and checks
that:

* Loading pages return a 200 status code. (Redirections are ignored:
  the spider wants the final load to resolve to an actual page.)

* The HTML returned is valid.

* Some headers are properly set.

Each time it is run, it creates a new subdirectory in ``out/``. The
subdirectory is created with the UTC date and time at the start of the
crawl in ISO 8601 format. The results of the run are stored in the
subdirectory:

* If there are no errors, a file named ``CLEAN`` will be created with
  the text "yes".

* If there are errors, a file named ``ERRORS`` will contain the items
  that have errors, in JSON format. There will also be a file named
  ``REPORT`` that contains a human-readable error report. This is also
  what is sent by email, if the spider was invoked with an email
  address passed to it. (Again, read ``btw_smoketest/spiders/btw.py``
  to know how to pass such address.)

* Whether there are errors or not, the content of each page visited is
  stored in the output directory in a file named after the URL of the
  page, but slugified.

* Whether there are errors or not, each page visited gets a validation
  report which has the same file name as the file that saves the
  content of the page (see the previous item in this list) but has
  ``.report`` appended to it.

Note that the spider will only visit those pages that are readily
available to the general public. Any page that requires speciall
permissions for access will not be visited. Moreover, the spider is
not able to interpret JavaScript. Therefore, URLs that get added by
JavaScript won't be seen by the spider.

INSTALLATION
============

This spider requires that the settings for Scrapy contain a
``VNU_JAR_PATH`` setting which should be set to the location of the
VNU jar on your system. (Get it from here:
https://github.com/validator/validator/releases/tag/16.3.3) The VNU
jar is used to validate the HTML of the pages. This is the only
setting you should be messing with.

We recommend you set a virtualenv for this spider. For instance,
assuming you start in the top directory of ``btw_smoketest``::

    $ cd ..
    $ virtualenv btw_smoketest_env
    $ cd btw_smoketest
    $ . ../btw_smoketest_env/bin/activate
    $ pip install -r requirements.txt
