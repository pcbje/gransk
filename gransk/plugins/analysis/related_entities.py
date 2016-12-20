#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import json
import os

import gransk.plugins.analysis.abstract_related as abstract_related


class Subscriber(abstract_related.Subscriber):
  """
  Class for finding related entities based on the documents they have in common.
  """
  SERVICE_ID = 'related_entities'
  NAME = 'entity'

  def consume(self, doc, _):
    """
    Add document to each entity's reference set.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    entities = doc.entities.get_all()

    doc = json.dumps({'id': doc.docid, 'filename': os.path.basename(doc.path)}, sort_keys=True)

    for _, entity in entities:
      key = entity['entity_id'].lower()

      if key not in self.buckets:
        self.buckets[key] = {
            'ref': entity['value'],
            'type': entity['type'],
            'bins': set()
        }

      self.buckets[key]['bins'].update([doc])

    self.new_data = True
