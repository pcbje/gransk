#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
import os
import pickle
import glob
from operator import itemgetter

import gransk.core.abstract_subscriber as abstract_subscriber
import gransk.core.helper as helper


class Subscriber(abstract_subscriber.Subscriber):
  """
  Find entities and documents that are related to each other based on
  found entities.
  """
  CONSUMES = [
      helper.FINISH_DOCUMENT
  ]

  NAME = None

  def setup(self, config):
    """
    Load existing data for given worker.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.path = os.path.join(
        config[helper.DATA_ROOT], '%s_buckets-%s.pickle' %
        (self.NAME, config[helper.WORKER_ID]))

    with open(self.path, 'a') as _:
      pass

    with open(self.path, 'rb') as inp:
      try:
        self.buckets = pickle.load(inp)
      except Exception:
        self.buckets = {}

    config_related = config.get(helper.RELATED, {}).get(self.NAME, {})
    self.min_score = config_related.get(helper.MIN_SCORE, 0.4)
    self.min_shared = config_related.get(helper.MIN_SHARED, 5)
    self.max_results = config_related.get(helper.MAX_RESULTS, 100)

  def save_all(self):
    file_dir = os.path.dirname(self.path)

    if not os.path.exists(file_dir):
      os.makedirs(file_dir)

    with open(self.path, 'wb') as out:
      pickle.dump(self.buckets, out)

  def load_all(self, config):
    """
    Load all existing data.

    :param config: Configuration object.
    :type config: ``dict``
    """
    self.buckets = {}

    for path in glob.glob(os.path.join(
            config[helper.DATA_ROOT], '%s_buckets-*.pickle' % self.NAME)):
      with open(path, 'rb') as inp:
        try:
          for key, value in pickle.load(inp).items():
            if key in self.buckets:
                self.buckets[key]['bins'].update(value['bins'])
            else:
              self.buckets[key] = value
        except:
          pass

  def stop(self):
    """Write data to file."""
    logging.debug('flushing %s.', self.NAME)
    self.save_all()

  def consume(self, doc, payload):
    """
    Abstract method that when implemented should add data from documents.

    :param doc: Document object.
    :param payload: File pointer beloning to document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    raise NotImplementedError('Please implement this method!')

  def get_related_to(self, _id, min_score=None, min_shared=None, max_results=None):
    """
    Get objects related to the given ID, based on:
      - How many entities they have in common (related documents)
      - How many documents they have in common (related entities)

    :param _id: ID of the object (entity or document) to get related for.
    :param min_score: shared / min(a_frequency, b_frequency).
    :param min_shared: Minimum amount of shared documetns or entities.
    :param max_results: Maximum number of related objects to return.
    :type _id: ``str``
    :type min_score: ``float``
    :type min_shared: ``int``
    :type max_results: ``int``
    """
    if min_score is None:
      min_score = self.min_score

    if min_shared is None:
      min_shared = self.min_shared

    if max_results is None:
      max_results = self.max_results

    _id = _id.lower()

    if _id not in self.buckets:
      return []

    bins = self.buckets[_id]['bins']
    this_fill = len(bins)

    if this_fill == 0:
      return []

    scores = []

    for other_id, other_bucket in self.buckets.items():
      if other_id == _id:
        continue

      other_fill = len(other_bucket['bins'])

      shared = bins.intersection(other_bucket['bins'])

      if len(shared) < min_shared:
        continue

      score = float(len(shared)**2) / min(this_fill, other_fill)

      scores.append((other_id, other_bucket['ref'], other_bucket['type'], float('%.2f' % score), list(shared)))

    results = []
    sorted_scores = sorted(scores, key=itemgetter(3), reverse=True)
    for a, b, c, d, e in sorted_scores[0:max_results]:
      results.append({
          'id': a,
          'ref': b,
          'type': c,
          'score': d / sorted_scores[0][3],
          'shared': e
      })

    return results
