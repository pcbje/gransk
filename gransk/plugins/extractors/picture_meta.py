#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re
import struct

import gransk.core.helper as helper
import gransk.core.abstract_subscriber as abstract_subscriber


class Subscriber(abstract_subscriber.Subscriber):
  """Determine width and height. Called when the document is a picture."""
  CONSUMES = [helper.PICTURE]

  def setup(self, config):
    """
    Define picture magic headers and compute regex pattern to find correct
    parser later.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.signatures = {
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'\377\330': 'jpg',
        b'\211PNG\r\n\032\n': 'png'
    }

    self.max_len = 0

    for magic, _type in self.signatures.items():
      self.max_len = max(self.max_len, len(magic))

    self.pattern = re.compile(b'|'.join(list(self.signatures.keys())))

  def __get_image_size(self, _type, fhandle):
    head = fhandle.read(24)
    if len(head) != 24:
      return
    if _type == 'png':
      check = struct.unpack('>i', head[4:8])[0]
      if check != 0x0d0a1a0a:
        return
      width, height = struct.unpack('>ii', head[16:24])
    elif _type == 'gif':
      width, height = struct.unpack('<HH', head[6:10])
    elif _type == 'jpg':
      b = fhandle.read(1)
      try:
        while b and ord(b) != 0xDA:
          while ord(b) != 0xFF:
            b = fhandle.read(1)
          while ord(b) == 0xFF:
            b = fhandle.read(1)
          if ord(b) >= 0xC0 and ord(b) <= 0xC3:
            fhandle.read(3)
            y, x = struct.unpack('>HH', fhandle.read(4))
            break
          else:
            fhandle.read(int(struct.unpack('>H', fhandle.read(2))[0]) - 2)
          b = fhandle.read(1)
        width, height = int(x), int(y)
      except Exception as err:
        # Try alternative jpeg method.
        try:
          fhandle.seek(0)
          size = 2
          ftype = 0
          while not 0xc0 <= ftype <= 0xcf:
            fhandle.seek(size, 1)
            byte = fhandle.read(1)
            while ord(byte) == 0xff:
              byte = fhandle.read(1)
            ftype = ord(byte)
            size = struct.unpack('>H', fhandle.read(2))[0] - 2
          fhandle.seek(1, 1)
          height, width = struct.unpack('>HH', fhandle.read(4))
        except Exception as err:
          return
    else:
      return

    return width, height

  def consume(self, doc, payload):
    """
    Parse picture header and extract width/height information.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    magic = payload.read(self.max_len)

    payload.seek(0)

    hit = self.pattern.match(magic)

    if not hit:
      return

    _type = self.signatures[hit.group()]

    size = self.__get_image_size(_type, payload)

    if not size:
      return

    doc.meta['img_width'], doc.meta['img_height'] = size
