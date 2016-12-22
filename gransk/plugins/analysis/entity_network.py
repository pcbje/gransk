#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import json
from collections import defaultdict

import gransk.core.abstract_subscriber as abstract_subscriber


class Subscriber(abstract_subscriber.Subscriber):
  """Class computing network surrounding an entity."""
  SERVICE_ID = 'entity_network'
  CONSUMES = []

  def setup(self, config):
    """
    Loads services for related entities and documents.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.related_entities = self.pipeline.get_service('related_entities')
    self.related_docs = self.pipeline.get_service('related_documents')
    self.max_network_size = config.get('max_network_size', 100)

  def consume(self, doc, payload):
    """Ignored."""
    # Ignore arguments.
    _ = (doc, payload)

  def __to_tuple(self, obj):
    return tuple([obj['entity_id'], obj['type'], obj['value']])

  def get_for(self, entity_id, hops=1):
    """
    Get network around the given entity ID.

    :param entity_id: Entity to get network for.
    :param hops: Maximum distance of included nodes from the given entity.
    :type entity_id: ``str``
    :type hops: ``int``
    :returns: ``dict``
    """
    entity_id = entity_id.lower()

    if entity_id not in self.related_entities.buckets:
      return {}

    network = defaultdict(int)
    nodes = {}

    done = {}
    queue = [entity_id]
    step = 0

    while step < hops:
      new_queue = []

      while queue:
        current = queue.pop(0)
        done[current] = True
        documents = self.related_entities.buckets[current]['bins']
        for document_str in documents:
          document = json.loads(document_str)
          bins = self.related_docs.buckets[document['id']]['bins']
          for a_entity_str in bins:
            a_entity = json.loads(a_entity_str)
            nodes[self.__to_tuple(a_entity)] = True
            if a_entity['entity_id'] not in done:
              new_queue.append(a_entity['entity_id'].lower())

              for b_entity_str in bins:
                b_entity = json.loads(b_entity_str)
                if a_entity['entity_id'] != b_entity['entity_id'] and (step < hops - 1 or self.__to_tuple(b_entity) in nodes):
                  nodes[self.__to_tuple(b_entity)] = True
                  key = sorted([
                      self.__to_tuple(a_entity),
                      self.__to_tuple(b_entity)])
                  if len(nodes) < self.max_network_size:
                    network[tuple(key)] += 1
                  else:
                    break
            if len(nodes) >= self.max_network_size:
                break

          if len(nodes) >= self.max_network_size:
              break

      queue = new_queue
      step += 1

    nodes = {}
    links = []

    for (source, target), count in network.items():
      if source[0] not in nodes:
        nodes[source[0]] = {'value': source[2], 'type': source[1]}
      if target[0] not in nodes:
        nodes[target[0]] = {'value': target[2], 'type': target[1]}

      links.append((source[0], target[0], {'count': count}))

    return {
        'seed': entity_id,
        'nodes': nodes,
        'links': links
    }
