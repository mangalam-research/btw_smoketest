# -*- coding: utf-8 -*-
import os
import datetime
import subprocess
from urlparse import urlparse

from scrapy import Request
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.item import Item, Field
from slugify import slugify


class LinkItem(Item):
    url = Field()
    referer = Field()
    status = Field()
    html_path = Field()
    validation_report_path = Field()
    validation_error = Field()

SHORTCUTS = {
    "demo": "https://btw-demo.mangalamresearch.org",
    "local": "http://localhost:8000",
}

class BtwSpider(CrawlSpider):
    name = "btw"

    def __init__(self, url="https://btw.mangalamresearch.org",
                 btw_dev=None, *args, **kwargs):

        if url[0] == "@":
            # Shortcut, resolve it to a real URL
            url = SHORTCUTS[url[1:]]

        parsed = urlparse(url)
        self.my_domain = parsed.hostname
        self.start_urls = (
            url,
        )

        # Only set btw_dev if we are accessing the site through HTTPS.
        self.btw_dev = btw_dev \
            if btw_dev is not None and parsed.scheme == "https" \
            else None

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

    def make_requests_from_url(self, url):
        request = super(BtwSpider, self).make_requests_from_url(url)
        # We add the cookie to the request. The default middleware
        # that ships with scrapy will act like a browser. Since the
        # cookie is set now and is not removed by the site, all
        # subsequent requests will use the cookie too.
        if self.btw_dev:
            request.cookies['btw_dev'] = self.btw_dev
        return request

    def parse_start_url(self, response):
        return self.handle_response(response)

    def parse_item(self, response):
        return self.handle_response(response)

    def handle_response(self, response):
        item = LinkItem()
        item['url'] = response.url
        item['referer'] = response.request.headers.get('Referer')
        item['status'] = response.status

        parsed = urlparse(response.url)

        item['validation_error'] = False
        if parsed.hostname == self.my_domain:
            html_path = os.path.join(self.outdir, slugify(response.url))
            validation_report_path = html_path + ".report"
            item['html_path'] = html_path
            item['validation_report_path'] = validation_report_path
            with open(html_path, 'w') as f:
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
