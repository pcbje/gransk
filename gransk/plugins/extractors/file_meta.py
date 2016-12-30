#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import re
import os
import logging
import json
import subprocess
import six
from six.moves.urllib.parse import quote as url_quote

import gransk.core.helper as helper
import gransk.core.abstract_subscriber as abstract_subscriber


class Subscriber(abstract_subscriber.Subscriber):
  """Class for extracting metadata from documents using Apache Tika."""
  CONSUMES = [helper.EXTRACT_META]

  def setup(self, config):
    """
    Load mediatype mapping from file. This is used to determine document type.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.config = config
    self.tmp_root = os.path.join(config[helper.DATA_ROOT], 'files', '.tmp')
    self.wid = config[helper.WORKER_ID]

    typecache = {}
    media_path = os.path.join(
        config[helper.CODE_ROOT], 'utils', 'media_types.txt')

    with open(media_path) as inp:
      current = None
      for line in inp:
        if len(line.strip()) == 0 or line.startswith('#'):
          continue

        if line.strip().startswith('-'):
          apptype = line.strip().partition('-')[2]
          apptype = apptype.strip()
          typecache[current].append(re.escape(apptype))
        else:
          current = line.strip()
          typecache[current] = []

    pattern_list = []

    for _type, patterns in typecache.items():
      pattern_list.append('(?P<%s>(%s))' % (_type, '|'.join(patterns)))

    self.typepattern = re.compile('|'.join(pattern_list), re.I)

  def __extract_metadata(self, doc, payload):
    filename = os.path.basename(doc.path)
    headers = {
      'Accept': 'application/json',
      'Content-Disposition': 'attachment; filename=%s' % url_quote(filename)
    }

    if doc.meta['Content-Type']:
      headers['Content-Type'] = doc.meta['Content-Type']

    tika_url = self.config.get(helper.TIKA_META)
    connection = self.config[helper.INJECTOR].get_http_connection(tika_url)
    payload.seek(0)
    connection.request('PUT', '/meta', payload.read(), headers)
    payload.seek(0)

    response = connection.getresponse()

    try:
      if response.status >= 400:
        logging.error('tika error %d (%s): %s', response.status,
                      response.reason, doc.path)
        return {}
      response_data = response.read()
    finally:
      response.close()

    try:
      result = json.loads(response_data.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
      logging.error('invalid response from tika for %s', doc.path)
      result = {}

    return result

  def __get_mime_type(self, doc, payload):
    tmp_path = os.path.join(self.tmp_root, '%s-%s.%s' %
      (self.wid, doc.docid[0:8], doc.ext))

    if not os.path.exists(self.tmp_root):
      os.makedirs(self.tmp_root)

    payload.seek(0)
    with open(tmp_path, 'wb') as out:
      out.write(payload.read())
    payload.seek(0)

    cmd = ('file', '--brief', '--mime-type', tmp_path)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = proc.communicate()

    if os.path.exists(tmp_path):
      os.remove(tmp_path)

    if proc.returncode != 0:
      return None

    return out.strip().decode('utf-8')

  def consume(self, doc, payload):
    """
    Upload document to Apache Tika and parse results.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    max_size = self.config.get(helper.MAX_FILE_SIZE, 0)

    if max_size > 0 and doc.meta['size'] > max_size:
      doc.meta['Content-Type'] = 'application/octet-stream'
      return

    mime_type = self.__get_mime_type(doc, payload)

    if mime_type:
      doc.meta['Content-Type'] = mime_type

    try:
      meta = self.__extract_metadata(doc, payload)
    except Exception as err:
      logging.exception('could not extract metadata from %s: %s', doc.path, err)
      doc.meta['meta_error'] = six.text_type(err)
      meta = {}

    if meta:
      for key, value in meta.items():
        doc.meta[key.replace('.', '_').replace(':', '_')] = value
    else:
      doc.meta['meta_error'] = 'unable to extract metadata using tika'

    for match in self.typepattern.finditer(doc.meta['Content-Type']):
      doc.set_type(match.lastgroup)
