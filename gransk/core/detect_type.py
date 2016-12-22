#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
import traceback
import sys
import os
import six

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper

LOGGER = logging.getLogger('proc')


class Subscriber(abstract_subscriber.Subscriber):
  """Class for determining document type."""

  CONSUMES = [helper.PROCESS_FILE]

  def setup(self, config):
    """
    Generate file extension-based type detection from the given configuration.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.blacklist = set([n.lower() for n in config.get(helper.BLACKLIST, [])])

    self.ext_types = {}
    for ext_type, exts in config.get(helper.EXT_TYPES, {}).items():
      for ext in exts:
        self.ext_types[ext.lower()] = ext_type.lower()

  def __accept(self, doc):
    return (os.path.basename(doc.path).lower() not in self.blacklist
            and doc.doctype != helper.IGNORED)

  def consume(self, doc, payload):
    """
    Determine document type, either by extension or based on Tika mimetype.
    Produces an event based on the found type.

    :param doc: Document to process.
    :param payload: File pointer to the document.
    :type doc: ``gransk.core.document.Document``
    :type file_object: ``file``
    """
    if not doc.doctype or doc.doctype == helper.UNKNOWN:
      doc.set_type(self.ext_types.get(doc.ext, helper.UNKNOWN))

    if not self.__accept(doc):
      doc.status = helper.IGNORED
      doc.meta['status'] = helper.IGNORED
      self.produce(helper.IGNORED_FILE, doc, payload)
      return

    LOGGER.debug('processing: %s', doc.path[-40:])

    # Include hash of first 4KB as doc id.
    doc.set_id(payload.read(4096))

    # Find size of stream.
    payload.seek(0, 2)
    doc.set_size(payload.tell())

    # Reset.
    payload.seek(0)

    try:
      # If document seems to be a container, try to unpack it.
      if doc.doctype in set([helper.DISKIMAGE, helper.ARCHIVE, helper.PICTURE]):
        self.produce(doc.doctype, doc, payload)

      # If unpacking seems unsuccessful, process it as a document.
      if doc.children == 0:
        # Find extractor by file header.
        self.produce(helper.MAGIC, doc, payload)

        # If not extractors were found, use external extractor (e.g. Tika).
        if not doc.magic_hit or doc.children == 0:
          self.produce(helper.EXTERNAL_EXTRACTOR, doc, payload)
          payload.seek(0)

        # If no text is extracted, find raw strings within document (strings).
        if not doc.text and doc.children == 0:
          self.pipeline.produce(helper.RAW, doc, payload)

      # Process text and index document and results.
      self.produce(helper.RUN_PIPELINE, doc, None)

    except Exception as err:
      traceback.print_exc(file=sys.stdout)
      LOGGER.warning('could not process %s: %s', doc.path, err)
      doc.status = 'error'
      doc.meta['gransk_error'] = six.text_type(err)
      self.produce(helper.ERRORED_FILE, doc, payload)
