#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
import inspect
import os
from collections import defaultdict

import gransk.core.helper as helper

LOGGER = logging.getLogger('pipeline')


class Pipeline(object):
  """
  Class for instatiating and managing subscribers and events during processing.
  Subscribers are registered to topics (``str``). A subscriber may register to
  any number of topics, or a magic header. When a subscriber produces an event,
  the pipeline finds all subscribers for that event topic and calls these (their
  ``consume(doc, payload)`` function) one by one. See
  ``gransk.core.abstract_subscriber.Subscriber.CONSUME``.

  During text extraction, we may want to implement custom extractors. This is
  done by registering to a magic header, which means the first N bytes of the
  document. See ``gransk.core.abstract_subscriber.Subscriber.MAGIC``.
  """

  def __init__(self):
    self.listeners = {}
    self.services = {}
    self.magic = defaultdict(list)
    self.subscribers = []

  def register_listener(self, topic, callback):
    """
    Register a subscriber callback to a topic.

    :param topic: The topic to subscribe to.
    :param callback: Function to call when an event with this topic is produced.
    :type topic: ``str``
    :type callback: ``function``
    """
    if topic not in self.listeners:
      self.listeners[topic] = []

    self.listeners[topic].append(callback)

  def register_service(self, service_id, service):
    """
    Register a subscriber as a service that is fetchable by ID. There may only
    be a single service with a given ID.

    :param service_id: The ID of the service.
    :param service: The service object.
    :type service_id: ``str``
    :type service: ``object``
    """
    self.services[service_id] = service

  def register_magic(self, magic, subscriber):
    """
    Register a subscriber to a magic header.

    :param magic: The header of files to subscribe to.
    :param subscriber: The subscriber object.
    :type service_id: ``str``
    :type service: ``object``
    """
    self.magic[magic].append(subscriber)

  def get_service(self, service_id):
    """
    Get service by ID.

    :param service_id: ID of service to fetch.
    :type service_id: ``str``
    :returns: ``object`` service. None if no service is found.
    """
    return self.services.get(service_id)

  def produce(self, topic, doc, payload):
    """
    Produce a new event.

    :param topic: The topic of the produced event.
    :param doc: The document to which the event belongs.
    :param payload: The file pointer beloning to the document.
    :type topic: ``str``
    :type doc: ``gransk.core.Document``
    :type payload: ``file``
    """
    caller = inspect.currentframe().f_back.f_locals['self'].__module__
    listeners = self.listeners.get(topic, [])
    filename = os.path.basename(doc.path)

    for listener, callback in listeners:
      LOGGER.debug('[%s] %s -> %s (%s)', topic, caller, listener, filename)
      callback(doc, payload)

    if len(listeners) == 0:
      LOGGER.debug('[%s] %s -> no listeners (%s)', topic, caller, filename)

  def stop(self):
    """Stop all subscribers."""
    for subscriber in self.subscribers:
      LOGGER.debug('> stopping %s', subscriber)
      subscriber.stop()

  def get_time_report(self):
    for subscriber in self.subscribers:
      yield subscriber, subscriber.time_report()


def init_subscriber(config, subscriber_mod, pipeline):
  """
  Instatiate a Subscriber object and add it to the pipeline.

  :param subscriber_mod: Reference to the module containing the Subscriber.
  :param pipline: The pipeline object to add the subscriber to.
  :type subscriber_mod: ``str``
  :type pipline: ``gransk.core.Pipeline``
  """
  LOGGER.debug('> starting %s', subscriber_mod)

  try:
    mod = __import__(subscriber_mod, fromlist=['Subscriber'])
    subscriber = mod.Subscriber(pipeline)
    subscriber.setup(config)

    pipeline.subscribers.append(subscriber)
  except Exception as err:
    LOGGER.exception('! %s could not be loaded: %s', subscriber_mod, err)


def build_pipeline(config):
  """
  Build the pipeline based on the given configuration.

  :param config: The configuration object.
  :type config: ``dict``
  :returns: Instantiated ``gransk.core.pipeline.Pipeline``
  """
  pipeline = Pipeline()

  for subscriber in config.get(helper.SUBSCRIBERS, []):
    init_subscriber(config, subscriber, pipeline)

  return pipeline
