#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os
import logging
import re
import six

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper
import gransk.core.document as document
import gransk.plugins.unpackers.diskimage_reader as diskimage_reader


LOGGER = logging.getLogger(__name__)


class Subscriber(abstract_subscriber.Subscriber):
  """
  Class for unpacking diskimages using dvVFS. Each accepted and unpacked
  document is added to the pipeline. Unpacked documents are not written to
  disk here. To speed things up, a list of blacklisted directories are loaded
  from utils/diskimage_ignore.txt. Due to their large sized and serial nature
  of some disk image formats (like EWF), this module currently only works when
  ``gransk.boot.run`` is used.
  """
  CONSUMES = [helper.DISKIMAGE]

  _READ_BUFFER_SIZE = 32768

  def setup(self, config):
    """
    Deterine max size to unpack and which directories to ignore.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.max_size = config.get(helper.MAX_FILE_SIZE, 128) * 1024 * 1024
    self.config = config

    ignore = {}
    path = os.path.join(
        config[helper.CODE_ROOT], 'utils', 'diskimage_ignore.txt')
    with open(path) as inp:
      for line in inp:
        if len(line.strip()) == 0 or line.startswith('#'):
          continue
        ignore[re.escape(line.strip().lower())] = True

    self.ignore = re.compile('|'.join(list(ignore.keys())), re.I)

  def _accept(self, path, depth):
    return not self.ignore.match(path) and depth < 16

  def _callback(self, entry, path, data_stream, doc):
    stat = entry.GetStat()

    newdoc = document.get_document(path, parent=doc)
    newdoc.tag = doc.tag
    newdoc.meta['mtime'] = stat.mtime
    newdoc.meta['atime'] = stat.atime
    newdoc.meta['ctime'] = stat.ctime
    newdoc.meta['size'] = stat.size

    if stat.size < self.max_size:
      file_object = None
      try:
        file_object = entry.GetFileObject(data_stream_name=data_stream)
        self.produce(helper.EXTRACT_META, newdoc, file_object)
        self.produce(helper.PROCESS_FILE, newdoc, file_object)
        doc.children += 1
      except IOError as err:
        LOGGER.debug('could not read path "%s": %s', path, err)
        doc.meta['diskimage_read_error'] = six.text_type(err)
        return None
      except Exception as err:
        doc.meta['diskimage_other_read_error'] = six.text_type(err)
      finally:
        if file_object:
          file_object.close()
    else:
      self.produce(helper.OVERSIZED_FILE, newdoc, None)

  def consume(self, doc, _):
    """
    Unpack a disk image using dfVFS.

    :param doc: Document object.
    :type doc: ``gransk.core.document.Document``
    """
    diskreader = diskimage_reader.Reader(self._accept, self._callback, doc)

    try:
      diskreader.Read(doc.path.encode('utf-8'))
    except Exception as err:
      LOGGER.debug('could not read image: %s', err)
      doc.meta['diskimage_error'] = six.text_type(err)
