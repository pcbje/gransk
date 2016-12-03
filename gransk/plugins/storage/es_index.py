#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import threading
import time
import re
import json
import os

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper

LOGGER = logging.getLogger(__name__)
logging.getLogger('elasticsearch').setLevel(logging.ERROR)


class Subscriber(abstract_subscriber.Subscriber):
  """Class for adding documents to an Elasticsearch cluster."""
  SERVICE_ID = 'elasticsearch'
  CONSUMES = [
      helper.FINISH_DOCUMENT,
      helper.IGNORED_FILE,
      helper.ERRORED_FILE,
      helper.OVERSIZED_FILE
  ]

  def setup(self, config):
    """
    Establish connection to Elasticsearch cluster and start periodic commit.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.config = config
    self.context_size = config.get(helper.CONTEXT_SIZE, 120)
    self.elastic_bulk = []
    self.elastic = self.config[helper.INJECTOR].get_elasticsearch()
    self.helper = self.config[helper.INJECTOR].get_elasticsearch_helper()
    self.create_mapping()

    self.last_commit = 0
    self.comitted = False

    thread = threading.Thread(target=self._time_commit, args=())
    thread.daemon = True
    thread.start()

  def _maybe_commit(self):
    if len(self.elastic_bulk) < 200:
      return

    self._commit()

  def _commit(self):
    self.last_commit = int(time.time())
    try:
      self.comitted = True
      tmp = self.elastic_bulk
      self.elastic_bulk = []
      self.helper.bulk(self.elastic, tmp)
    except Exception as err:
      LOGGER.error('es index error: %s' % err)

  def _time_commit(self):
    while True:
      if not self.comitted:
        self._commit()
      self.comitted = False
      time.sleep(1)

  def stop(self):
    """Commit current remaning documents."""
    self._commit()

  def create_mapping(self):
    """Create index mappig in Elasticsearch cluster."""
    LOGGER.info(self.elastic.indices.create(index=u'gransk', ignore=400, body={
        "settings": {
            "number_of_shards": 5,
            "analysis": {
                "analyzer": {
                    "lowercase_keyword": {
                        "type:": "custom",
                        "filter": ["lowercase"],
                        "tokenizer": "keyword"
                    }
                }
            },
            "index": {
                "analysis": {
                    "analyzer": {
                        "keyword": {
                            "type": "custom",
                            "tokenizer": "keyword",
                            "filter": ["standard", "lowercase"]
                        },
                        "default": {
                            "type": "custom",
                            "tokenizer": "uax_url_email",
                            "filter": ["standard", "lowercase", "stop"]
                        },
                    }
                }
            }
        },
        "mappings": {
            "document": {
                "dynamic": "true",
                "properties": {
                    "parent": {
                        "type": "nested"
                    },
                    "meta": {
                        "type": "nested"
                    }
                }
            },
            "entity": {
                "properties": {
                    "type": {
                        "type": "string"
                    },
                    "value": {
                        "type": "string"
                    }
                }
            },
            "in_doc": {
                "dynamic": "true",
                "properties": {
                    "entity_value": {
                        "type": "string",
                        "analyzer": "keyword"
                    },
                    "raw_entity": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            }
        }
    }))

  def consume(self, doc, _):
    """
    Add document to Elasticsearch.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    tag = self.config[helper.TAG]

    if doc.tag:
      tag = doc.tag

    obj = {
        u"_op_type": u"index",
        u"_index": u'gransk',
        u"_type": u'document',
        u"_source": doc.as_obj(),
        u'_id': doc.docid
    }

    obj['_source'][u'tag'] = tag

    self.elastic_bulk.append(obj)

    cache = {}

    for start, entity_obj in doc.entities.get_all():
      entity_type = entity_obj['type']
      entity_value = entity_obj['value']
      entity_id = entity_obj['entity_id']

      if entity_id in cache:
        continue

      cache[entity_id] = True

      self.elastic_bulk.append({
          u"_op_type": u"index",
          u"_index": u'gransk',
          u"_type": u'entity',
          u"_source": {
              'type': entity_type,
              'value': entity_value,
              'entity_id': entity_id
          },
          u'_id': '%s\x00%s' % (entity_type, entity_value)
      })

      ctx_start = max(
          0, start - (self.context_size // 2 - len(entity_value) // 2))
      ctx_end = min(len(doc.text), start + self.context_size)

      context = doc.text[ctx_start:ctx_end]
      context = re.sub('\s+', ' ', context)

      self.elastic_bulk.append({
          u"_op_type": u"index",
          u"_index": u'gransk',
          u"_type": u'in_doc',
          u"_source": {
              'entity_id': entity_id,
              'entity_type': entity_type,
              'entity_value': entity_value,
              'doc_id': doc.docid,
              'doc_path': doc.path,
              'doc_filename': os.path.basename(doc.path),
              'context': context,
              'raw_entity': json.dumps(entity_obj)
          },
          u'_id': '%s\x00%s\x00%s\x00%s' % (
              doc.docid[-12::], entity_value, entity_type, start)
      })

    self._maybe_commit()
