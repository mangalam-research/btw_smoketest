# -*- coding: utf-8 -*-

import os

BOT_NAME = 'btw_smoketest'

SPIDER_MODULES = ['btw_smoketest.spiders']
NEWSPIDER_MODULE = 'btw_smoketest.spiders'
HTTPERROR_ALLOW_ALL = True

VNU_JAR_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "node_modules/vnu-jar/build/dist/vnu.jar")

ITEM_PIPELINES = {
    'btw_smoketest.pipelines.JSONWriterPipeline': 300,
}

USER_AGENT = 'btw_smoketest (+http://btw.mangalamresearch.org)'
