#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import six.moves.http_client
import random

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from polyglot.text import Text

import gransk.core.helper as helper


class Injector(object):
  """
  Class for injecting external dependencies to the application. This makes
  the application logic easier to test.
  """

  def __init__(self):
    self.config = None

  def set_config(self, config):
    """
    Set configuration object.

    :param config: The configuration object.
    :type config: ``dict``
    """
    self.config = config

  def get_http_connection(self, url=None):
    """
    Get a HTTP connection to the host. Currently only used by Tika.

    :returns: ``six.moves.http_client.HTTPConnection``
    """
    if not url:
      host = self.config['tika_host'][random.randint(0, len(self.config['tika_host'])-1)]
      url = '%s:%s' % (host, self.config.get(helper.TIKA_PORT, 9998))

    return six.moves.http_client.HTTPConnection(url)

  def get_elasticsearch(self):
    """
    Get a connection to the Elasticsearch cluster. Currently on supports a
    single host.

    :returns: ``elasticsearch.Elasticsearch``
    """
    return Elasticsearch(hosts=self.config['es_host'], timeout=30)

  def get_elasticsearch_helper(self):
    """
    Get helpers module for Elasticsearch. Used to bulk index documents.

    :returns: package ``elasticsearch.helpers``
    """
    return helpers

  def get_polyglot(self):
    """
    Get Polyglot NER class that can extract entities from text.

    :returns: Uninstantiated class ``polyglot.text.Text``
    """
    return Text
