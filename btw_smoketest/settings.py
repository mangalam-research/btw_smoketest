# -*- coding: utf-8 -*-

BOT_NAME = 'btw_smoketest'

SPIDER_MODULES = ['btw_smoketest.spiders']
NEWSPIDER_MODULE = 'btw_smoketest.spiders'
HTTPERROR_ALLOW_ALL = True

VNU_JAR_PATH = "/home/ldd/src/git-repos/validator/build/dist/vnu.jar"

ITEM_PIPELINES = {
    'btw_smoketest.pipelines.JSONWriterPipeline': 300,
}

USER_AGENT = 'btw_smoketest (+http://btw.mangalamresearch.org)'
