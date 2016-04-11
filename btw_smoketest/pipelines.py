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
        outdir = getattr(spider, "outdir")
        if outdir is not None:
            self.info[spider.name] = {
                'items': [],
            }

    def close_spider(self, spider):
        info = self.info.pop(spider.name)
        if info is not None:
            outdir = spider.outdir
            outpath = os.path.join(outdir, "links.json")
            items = info['items']
            with open(outpath, 'w') as f:
                f.write(json.dumps([dict(i) for i in items]))

            errors = [
                i for i in items if i['status'] != 200 or
                i['validation_error'] or i['header_errors']]
            if errors:
                with open(os.path.join(outdir, 'ERRORS'), 'w') as f:
                    f.write(json.dumps([dict(i) for i in errors]))

                message = []
                for i in errors:
                    item_message = ["===\nURL: {0}\n\n".format(i['url'])]

                    status = i['status']
                    if status != 200:
                        item_message.append(
                            "Failed retrieval with status: {0}\n".format(
                                status))

                    if i['validation_error']:
                        item_message.append("Failed validation.\n\n")


                    header_errors = i['header_errors']
                    if header_errors:
                        item_message.append(
                            ("Failed header checks with the following "
                             "errors:\n{0}\n").format(
                                 "\n".join(header_errors)))

                    if len(item_message) > 1:
                        message += item_message

                message.append("\nSee %s for details of validation errors." %
                               outdir)

                email_body = "".join(message)
                with open(os.path.join(outdir, 'REPORT'), 'w') as f:
                    f.write(email_body)

                sender = MailSender(mailfrom="btw@btw.mangalamresearch.org")
                sender.send(["btw@btw.mangalamresearch.org"],
                            "Smoketest failure", email_body)
            else:
                with open(os.path.join(outdir, 'CLEAN'), 'w') as f:
                    f.write("yes\n")
