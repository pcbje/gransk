#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: skip-file

from __future__ import absolute_import, unicode_literals

import logging
import os
from collections import OrderedDict
import six
from six.moves import range


import chardet

from dfvfs.helpers import source_scanner
from dfvfs.lib import definitions
from dfvfs.lib import errors
from dfvfs.resolver import resolver
from dfvfs.volume import tsk_volume_system
from dfvfs.volume import vshadow_volume_system
from dfvfs.path import factory as path_spec_factory


class Reader(object):
  """Disk image reader based on the recursive hasher example by Joachim Metz."""

  def __init__(self, accept, callback, parent):
    self.accept = accept
    self.callback = callback
    self.parent = parent
    self.parent.meta['directories'] = OrderedDict()

  def _ExtractFileEntries(
          self, file_system, file_entry, parent_full_path, depth):
    try:
      if isinstance(file_entry.name, six.text_type):
        name = file_entry.name
      else:
        enc = chardet.detect(file_entry.name).get('encoding')
        name = file_entry.name.decode(enc)

      full_path = file_system.JoinPath([parent_full_path, name])
    except Exception:
      logging.exception("could not extract file entries: %s", name)
      return

    if depth < 5:
      key = parent_full_path.replace('.', '\x00')
      if key not in self.parent.meta['directories']:
        self.parent.meta['directories'][key] = 0

      self.parent.meta['directories'][key] += 1

    if self.accept(full_path, depth):
      for data_stream in file_entry.data_streams:
        self.callback(file_entry, full_path, data_stream.name, self.parent)

      for sub_file_entry in file_entry.sub_file_entries:
        self._ExtractFileEntries(
            file_system, sub_file_entry, full_path, depth + 1)

  def _GetTSKPartitionIdentifiers(self, scan_node):
    if not scan_node or not scan_node.path_spec:
      raise RuntimeError('Invalid scan node.')

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)

    if not volume_identifiers:
      logging.warning('No partitions found.')
      return

    return volume_identifiers

  def _GetVSSStoreIdentifiers(self, scan_node):
    if not scan_node or not scan_node.path_spec:
      raise RuntimeError('Invalid scan node.')

    volume_system = vshadow_volume_system.VShadowVolumeSystem()
    volume_system.Open(scan_node.path_spec)

    volume_identifiers = self._source_scanner.GetVolumeIdentifiers(
        volume_system)

    if not volume_identifiers:
      return []

    return list(range(1, volume_system.number_of_volumes + 1))

  def _ScanVolume(self, scan_context, volume_scan_node, base_path_specs):
    if not volume_scan_node or not volume_scan_node.path_spec:
      raise RuntimeError('Invalid or missing volume scan node.')

    if len(volume_scan_node.sub_nodes) == 0:
      self._ScanVolumeScanNode(scan_context, volume_scan_node, base_path_specs)

    else:
      for sub_scan_node in volume_scan_node.sub_nodes:
        self._ScanVolumeScanNode(scan_context, sub_scan_node, base_path_specs)

  def _ScanVolumeScanNode(
          self, scan_context, volume_scan_node, base_path_specs):
    if not volume_scan_node or not volume_scan_node.path_spec:
      raise RuntimeError('Invalid or missing volume scan node.')

    scan_node = volume_scan_node
    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    if scan_node.type_indicator == definitions.TYPE_INDICATOR_VSHADOW:
      self._ScanVolumeScanNodeVSS(scan_context, scan_node, base_path_specs)

    elif scan_node.type_indicator in definitions.FILE_SYSTEM_TYPE_INDICATORS:
      base_path_specs.append(scan_node.path_spec)

  def _GetNextLevelTSKPartitionVolumeSystemPathSpec(self, source_path_spec):
    return path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, location='/p1',
        parent=source_path_spec)

  def _ScanVolumeScanNodeVSS(
          self, scan_context, volume_scan_node, base_path_specs):
    vss_store_identifiers = self._GetVSSStoreIdentifiers(volume_scan_node)

    self._vss_stores = list(vss_store_identifiers)

    # Process VSS stores starting with the most recent one.
    vss_store_identifiers.reverse()

    self.parent.meta['vss_count'] = len(vss_store_identifiers)

    for vss_store_identifier in vss_store_identifiers:
      location = '/vss{0:d}'.format(vss_store_identifier)
      sub_scan_node = volume_scan_node.GetSubNodeByLocation(location)
      if not sub_scan_node:
        continue

      self._source_scanner.Scan(
          scan_context, scan_path_spec=sub_scan_node.path_spec)

      self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

      # Process most recent VSS only.
      break

  def _Extract(self, base_path_specs):
    for base_path_spec in base_path_specs:
      file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
      if file_system.__class__.__name__ == 'OSFileSystem':
        continue
      file_entry = resolver.Resolver.OpenFileEntry(base_path_spec)
      if file_entry is None:
        logging.warning(
            'Unable to open base path specification:\n{0:s}'.format(
                base_path_spec.comparable))
        continue

      self._ExtractFileEntries(file_system, file_entry, '', 0)

      file_system.Close()

  def _GetBasePathSpecs(self, source_path):
    if (not source_path.startswith('\\\\.\\') and
            not os.path.exists(source_path)):
      raise RuntimeError(
          'No such device, file or directory: {0:s}.'.format(source_path))

    scan_context = source_scanner.SourceScannerContext()
    scan_context.OpenSourcePath(source_path)

    try:
      self._source_scanner.Scan(scan_context)
    except (errors.BackEndError, ValueError) as exception:
      raise RuntimeError(
          'Unable to scan source with error: {0:s}.'.format(exception))

    if scan_context.source_type not in [
            definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
            definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]:
      scan_node = scan_context.GetRootScanNode()
      return [scan_node.path_spec]

    scan_node = scan_context.GetRootScanNode()

    while len(scan_node.sub_nodes) == 1:
      scan_node = scan_node.sub_nodes[0]

    if scan_node.type_indicator != definitions.TYPE_INDICATOR_TSK_PARTITION:
      partition_identifiers = None

    else:
      partition_identifiers = self._GetTSKPartitionIdentifiers(scan_node)

    base_path_specs = []
    if not partition_identifiers:
      self._ScanVolume(scan_context, scan_node, base_path_specs)

    else:
      for partition_identifier in partition_identifiers:
        location = '/{0:s}'.format(partition_identifier)
        sub_scan_node = scan_node.GetSubNodeByLocation(location)

        self._ScanVolume(scan_context, sub_scan_node, base_path_specs)

    if not base_path_specs:
      raise RuntimeError(
          'No supported file system found in source.')

    return base_path_specs

  def Read(self, input_path):
    """
    Read disk image from a provided input path.

    :param input_path: Path to the disk image.
    :type input_path: ``str``
    """
    self._source_scanner = source_scanner.SourceScanner()
    base_path_specs = self._GetBasePathSpecs(input_path.decode('utf-8'))
    self._Extract(base_path_specs)
