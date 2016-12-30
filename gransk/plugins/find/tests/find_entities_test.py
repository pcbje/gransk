#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import unittest
import yaml

import gransk.core.document as document
import gransk.core.helper as helper
import gransk.plugins.find.find_entities as find_entities
import gransk.core.tests.test_helper as test_helper


class FindEntitiesTest(unittest.TestCase):

  def test_config(self):
    with open('config.default.yml') as inp:
      config = yaml.load(inp.read())

    _find_entities = find_entities.Subscriber(test_helper.get_mock_pipeline([]))
    _find_entities.setup(config)

    doc = document.get_document('dummy')

    for entity_type, pattern_conf in config.get(helper.ENTITIES, {}).items():
      if not isinstance(pattern_conf['test'], list):
        pattern_conf['test'] = [pattern_conf['test']]

      for test in pattern_conf['test']:
        doc.text = 'dum dum {} dum'.format(test)
        _find_entities.consume(doc, None)
        entities = doc.entities.get_all()

        self.assertEqual(1, len(entities),
                         msg='regex for %s found nothing' % entity_type)
        self.assertEqual(entity_type, entities[0][1]['type'])
        self.assertEqual(test, entities[0][1]['value'])


if __name__ == '__main__':
  unittest.main()
