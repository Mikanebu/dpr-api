# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from flask import current_app as app
from flask import url_for


class Packaged(object):
    def __init__(self, metadata):
        self.metadata = metadata
        self.publisher = metadata.get('publisher')
        self.package = metadata.get('name')
        self.readme = metadata.get('readme')
        self.descriptor = metadata.get('descriptor')
        self.resources = self.descriptor.get('resources') or []

    def get_views(self):
        return self.descriptor.get('views') or []

    def construct_dataset(self, url_root=''):
        clone = self.clone(self.resources)
        self.descriptor['owner'] = self.publisher
        self.descriptor['resources'] = clone
        self.descriptor['readme'] = self.readme
        return self.descriptor

    def clone(self, clone):
        return clone[:]
