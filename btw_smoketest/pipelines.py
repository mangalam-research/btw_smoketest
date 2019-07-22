# -*- coding: utf-8 -*-

import os
import json

from scrapy.mail import MailSender

class JSONWriterPipeline(object):

    def __init__(self):
        self.info = {}

    def process_item(self, item, spider):
        info = self.info.get(spider.name)
        if info is not None:
            info['items'].append(item)
        return item

    def open_spider(self, spider):
        if not hasattr(spider, "spider_outdir"):
            return

        self.info[spider.name] = {
            'items': [],
        }

    def close_spider(self, spider):
        info = self.info.pop(spider.name)
        if info is None:
            return

        spider_outdir = spider.spider_outdir
        # We use dict() to convert the objects stored in items to plain
        # dictionaries. Otherwise, they cannot be serialized by json.dump.
        items = [dict(i) for i in info['items']]
        with open(os.path.join(spider_outdir, "links.json"), 'w') as f:
            json.dump(items, f)

        errors = [i for i in items if i['status'] != 200 or
                  i['validation_error'] or i['header_errors']]
        if not errors:
            with open(os.path.join(spider_outdir, 'CLEAN'), 'w') as f:
                f.write("yes\n")
            return

        with open(os.path.join(spider_outdir, 'ERRORS'), 'w') as f:
            json.dump(errors, f)

        message = []
        for i in errors:
            item_message = ["===\nURL: {0}\n\n".format(i['url'])]

            status = i['status']
            if status != 200:
                item_message.append("Failed retrieval with status: {0}\n"
                                    .format(status))

            if i['validation_error']:
                item_message.append("Failed validation.\n\n")

            header_errors = i['header_errors']
            if header_errors:
                item_message.append("Failed header checks with the following "
                                    "errors:\n{0}\n"
                                    .format("\n".join(header_errors)))

            if len(item_message) > 1:
                message += item_message

        message.append("\nSee %s for details of validation errors." %
                       spider_outdir)

        email_body = "".join(message)
        with open(os.path.join(spider_outdir, 'REPORT'), 'w') as f:
            f.write(email_body)

        send_to = spider.send_to
        if send_to is not None:
            sender = MailSender(mailfrom="btw@btw.mangalamresearch.org")
            sender.send([send_to], "Smoketest failure", email_body)
