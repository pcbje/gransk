#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper


class Subscriber(abstract_subscriber.Subscriber):
  """
  Class for uploading documents to Apache Tika and reading text response.
  Tika is an open source tool that is capable of parsing a vast number (>200)
  of document formats.
  """
  CONSUMES = [helper.EXTERNAL_EXTRACTOR]

  SERVICES = []

  def _accept(self, doc):
    return doc.meta['size'] < self.max_size

  def setup(self, config):
    """
    Define maximum size of document to upload.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.config = config
    self.max_size = config.get(helper.TIKA_MAX_SIZE, 1024 * 1024 * 64)
    self.ocr_languages = config.get(helper.OCR_LANGUAGES)

  def consume(self, doc, payload):
    """
    Upload document to Apache Tika and add result to document as text.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    if not self._accept(doc):
      return

    filename = os.path.basename(doc.path).encode('utf-8')
    content_type = doc.meta['Content-Type']

    headers = {
        'Content-Disposition': 'attachment; filename=%s' % filename,
        'Content-type': content_type,
    }

    if self.ocr_languages:
        headers['X-Tika-OCRLanguage'] = self.ocr_languages

    connection = self.config[helper.INJECTOR].get_http_connection()
    connection.request('PUT', '/tika', payload.read(), headers)

    doc.set_size(payload.tell())

    response = connection.getresponse()

    text = response.read().strip().decode('utf-8')

    response.close()

    doc.text = text
