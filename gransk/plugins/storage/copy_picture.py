#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import logging

from werkzeug import secure_filename

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper

LOGGER = logging.getLogger(__name__)


class Subscriber(abstract_subscriber.Subscriber):
  """
  Class for copying pictures into local data so that they can be accessed
  through the web interface.
  """
  CONSUMES = [helper.PICTURE]

  def setup(self, config):
    """
    Determine target directory.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.root = os.path.join(config[helper.DATA_ROOT], 'pictures')
    if not os.path.exists(self.root):
      try:
        os.makedirs(self.root)
      except Exception as err:
        LOGGER.exception('could not create dir %s: %s', self.root, err)

  def consume(self, doc, payload):
    """
    Write payload to target directory, using a combination of filename and file
    ID as path.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    new_filename = '%s-%s' % \
      (doc.docid[0:8], secure_filename(os.path.basename(doc.path)))

    if not os.path.exists(self.root):
      os.makedirs(self.root)

    new_path = os.path.join(self.root, new_filename)

    with open(new_path, 'wb') as out:
      payload.seek(0)
      out.write(bytes(payload.read()))
      payload.seek(0)
      doc.meta['picture'] = new_filename
