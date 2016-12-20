#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import os

import gransk.plugins.analysis.abstract_related as abstract_related


class Subscriber(abstract_related.Subscriber):
  """
  Class for finding related documents based on the entities they have in common.
  """
  SERVICE_ID = 'related_documents'
  NAME = 'document'

  def consume(self, doc, _):
    """
    Add all entities to the reference set.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    entities = doc.entities.get_all()

    self.buckets[doc.docid] = {
        'ref': os.path.basename(doc.path),
        'type': 'doc',
        'bins': set()
    }

    for _, entity in entities:
      key = json.dumps(entity, sort_keys=True)
      self.buckets[doc.docid]['bins'].update([key])

    self.new_data = True
