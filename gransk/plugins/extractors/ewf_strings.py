#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pyewf

import gransk.plugins.extractors.strings as strings
import six


class Subscriber(strings.Subscriber):
  """
  Class for extracting raw content from Expert Witness Format (EWF) containers.
  The preferred option is to extract files from the container using dfVFS.
  However, if that for some reason fails, this is the fallback method.
  """
  MAGIC = b'\x45\x56\x46'  # 'EVF'
  CONSUMES = []

  def consume(self, doc, payload):
    """
    Open file pointer as using libewf and pass to strings. See
    ``gransk.plugins.extractors.strings``.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    payload.seek(0)
    ewf_handle = pyewf.handle()
    ewf_handle.open_file_objects([payload], "rb")

    for key, value in ewf_handle.get_header_values().items():
      doc.meta[key] = value

    self.buffer_size = ewf_handle.chunk_size

    try:
      super(Subscriber, self).consume(doc, ewf_handle)
    except Exception as err:
      doc.meta['ewf_strings_err'] = six.text_type(err)
      print (err)

    ewf_handle.close()
    payload.seek(0)
