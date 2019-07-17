# -*- coding: utf-8 -*-
import os
import datetime
import subprocess
from urllib.parse import urlparse

from scrapy import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.item import Item, Field
from slugify import slugify


class LinkItem(Item):
    url = Field()
    referer = Field()
    status = Field()
    html_path = Field()
    validation_report_path = Field()
    validation_error = Field()
    header_errors = Field()

SHORTCUTS = {
    "demo": "https://btw-demo.mangalamresearch.org",
    "local": "http://localhost:8000",
}

def format_header_error(key, value):
    return "{0} has no value".format(key) if value is None else \
        "{0} has the value {1}".format(key, value)

def check_header_value(header_errors, headers, key, expected_value):
    value = headers.get(key)

    # If expected_value is a callable, we call it to test the value,
    # otherwise we just compare.
    if not (expected_value(value) if callable(expected_value) else
            value == expected_value):
        header_errors.append(
            format_header_error(key, value))


class BtwSpider(CrawlSpider):
    name = "btw"

    def __init__(self, url="https://btw.mangalamresearch.org",
                 send_to=None, btw_dev=None, naked=False,
                 *args, **kwargs):
        """
        :param url: The URL of the site to test. By default it tests
        ``https://btw.mangalamresearch.org``. The spider supports two
        "shortcut" values. ``@demo`` tests
        ``https://btw-demo.mangalam...``. ``@local`` tests
        ``http://localhost:8000``.

        :param send_to: Email address where to send a report. Defaults
        to ``None``, which means no report is mailed.

        :param btw_dev: A value to set the ``btw_dev`` cookie to. This
        is useful if the site is in maintenance mode. Setting
        ``btw_dev`` to a secret value will bypass the maintenance
        block. Defaults to ``None``.

        :param naked: Whether or not the site is being accessed
        "naked", as a server started by Django with ``runserver`` or a
        similar command, rather than through Nginx, Apache, or some
        other server software. Defaults to ``False``. On a naked site,
        there are some header checks we cannot perform because they
        are the responsibility of the server software that first
        receives the requests.
        """

        if url[0] == "@":
            # Shortcut, resolve it to a real URL
            url = SHORTCUTS[url[1:]]

        self.send_to = send_to

        parsed = urlparse(url)
        self.my_domain = parsed.hostname
        self.start_urls = (
            url,
        )

        # Only set btw_dev if we are accessing the site through HTTPS.
        self.btw_dev = btw_dev \
            if btw_dev is not None and parsed.scheme == "https" \
            else None

        self.naked = naked

        # These rules make it so that we will test all links on our site,
        # including links to external sites. However, we do not *crawl*
        # the external sites.
        self.rules = (
            Rule(LinkExtractor(allow_domains=[self.my_domain]),
                 callback='parse_item'),
            Rule(LinkExtractor(), follow=False, callback='parse_item'),
        )

        super(BtwSpider, self).__init__(*args, **kwargs)
        now = datetime.datetime.utcnow().replace(microsecond=0)
        self.outdir = os.path.join("out", now.isoformat())
        os.makedirs(self.outdir)

    def start_requests(self):
        requests = super(BtwSpider, self).start_requests()
        if not self.btw_dev:
            return requests

        # We add the cookie to the request. The default middleware
        # that ships with scrapy will act like a browser. Since the
        # cookie is set now and is not removed by the site, all
        # subsequent requests will use the cookie too.
        for request in requests:
            request.cookies['btw_dev'] = self.btw_dev

        return requests

    def parse_start_url(self, response):
        return self.handle_response(response)

    def parse_item(self, response):
        return self.handle_response(response)

    def handle_response(self, response):
        headers = response.headers
        item = LinkItem()
        url = response.url
        item['url'] = url
        referer = response.request.headers.get('Referer')
        item['referer'] = None if referer is None else referer.decode("utf8")
        item['status'] = response.status

        parsed = urlparse(url)

        item['validation_error'] = False
        item['header_errors'] = header_errors = []
        if parsed.hostname == self.my_domain:
            # We perform header checks only on non-naked sites.
            if not self.naked:
                check_header_value(header_errors, headers,
                                   b'X-Frame-Options', b'SAMEORIGIN')
                check_header_value(header_errors, headers,
                                   b'X-Content-Type-Options', b'nosniff')
                check_header_value(header_errors, headers,
                                   b'X-XSS-Protection', b'1; mode=block')

                def sts_check(value):
                    return value is not None and value.startswith(b"max-age=")

                check_header_value(header_errors, headers,
                                   'Strict-Transport-Security', sts_check)

            html_path = os.path.join(self.outdir, slugify(url))
            validation_report_path = html_path + ".report"
            item['html_path'] = html_path
            item['validation_report_path'] = validation_report_path
            with open(html_path, 'wb') as f:
                f.write(response.body)

            try:
                subprocess.check_call(['java', '-jar',
                                       self.settings["VNU_JAR_PATH"],
                                       html_path],
                                      stderr=open(validation_report_path, 'w'))
            except subprocess.CalledProcessError:
                pass

            item['validation_error'] = \
                not os.path.exists(validation_report_path) or \
                os.stat(validation_report_path).st_size != 0

        return item
