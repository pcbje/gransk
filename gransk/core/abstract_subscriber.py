#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import time


class Subscriber(object):
  """Abstract class subscribers inherits from."""

  #: Subscribe to the following list of topics [``unicode``]
  CONSUMES = None

  #: This subscriber may be fetched from the pipeline by this ID.
  SERVICE_ID = None

  #: Documents starting whith these bytes should be passed to this subscriber.
  MAGIC = None

  def __init__(self, pipeline):
    """
    Add subscriber to pipeline.

    :param pipeline: Pipeline managing subscribers and events.
    :type pipeline: ``gransk.core.pipeline.Pipeline``
    """
    self.pipeline = pipeline
    self.time_used = []

    if self.CONSUMES is None and self.MAGIC is None:
      raise NotImplementedError('Please define CONSUMES or MAGIC.')

    if pipeline:
      if self.SERVICE_ID:
        self.pipeline.register_service(self.SERVICE_ID, self)

      if self.MAGIC:
        self.pipeline.register_magic(
            self.MAGIC, (self.__module__, self.time_consume))

      for topic in self.CONSUMES:
        self.pipeline.register_listener(
            topic, (self.__module__, self.time_consume))

  def setup(self, config):
    """
    Placeholder for configuration of subscriber, before receiving data.

    :param config: Configuration object for processing.
    :type config: ``dict``
    """
    pass

  def stop(self):
    """Stop subscriber after progressing is completed."""
    pass

  def time_consume(self, doc, payload):
    start = time.time()
    self.consume(doc, payload)
    end = time.time()
    self.time_used.append(end - start)

  def __str__(self):
    return self.__module__

  def time_report(self):
    if len(self.time_used) == 0:
      return 0, 0, 0

    total = sum(self.time_used)
    return total, len(self.time_used), total / len(self.time_used)

  def consume(self, doc, payload):
    """
    Abstract method for receiving data.

    :param doc: The document the event belongs to.
    :param payload: File pointer beloning to the document.
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    raise NotImplementedError('Please implement this method!')

  def produce(self, topic, doc, payload):
    """
    Add a new event to the pipeline.

    :param topic: Topic to add event to.
    :param doc: The document the event belongs to.
    :param payload: File pointer beloning to the document.
    :type topic: ``unicode``
    :type doc: ``gransk.core.document.Document``
    :type payload: ``file``
    """
    self.pipeline.produce(topic, doc, payload)
