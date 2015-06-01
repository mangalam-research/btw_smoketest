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
                i['validation_error']]
            if errors:
                with open(os.path.join(outdir, 'ERRORS'), 'w') as f:
                    f.write(json.dumps([dict(i) for i in errors]))

                message = ["URL: %s\nFailed retrieval with: %d\n" %
                           (i['url'], i['status']) for i in items if
                           i['status'] != 200]

                message.append("\n")

                message += ["URL: %s\nFailed validation.\n" %
                            i['url'] for i in items if
                            i['validation_error']]

                message.append("\nSee %s for details." % outdir)

                sender = MailSender(mailfrom="btw@btw.mangalamresearch.org")
                sender.send(["btw@btw.mangalamresearch.org"],
                            "Smoketest failure",
                            "".join(message))
            else:
                with open(os.path.join(outdir, 'CLEAN'), 'w') as f:
                    f.write("yes\n")
