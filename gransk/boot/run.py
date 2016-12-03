#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Process a document or folder or folder from command line."""
from __future__ import absolute_import
import os
import argparse
import logging
import six.moves.http_client
import shutil
import sys

import yaml

import gransk.core.helper as helper
import gransk.api

from multiprocessing import Queue, Process
from six.moves.queue import Empty
import time
import traceback
import logging
import os
import sys
import glob
import six
from six.moves import range

from tqdm import tqdm

import gransk.core.file_collector as collector
import gransk.core.pipeline as pipeline
import gransk.core.document as document
import gransk.core.helper as helper


class Worker(object):
  """
  Class for initializing pipeline and subscribers for a given worker. Several
  workers may be initialized, but they read from the same queue.
  """

  def init(self, config, queue, worker_id, injector):
    """
    Initialize worker and read paths from queue, stopping when queue is empty.

    :param config: Configuration object.
    :param queue: Multiprcessing Queue object.
    :param worker_id: Value identifying this worker.
    :param injector: Object from which to fetch dependencies.
    :type config: ``dict``
    :type queue: ``multiprocessing.Queue``
    :type worker_id: ``int``
    :type injector: ``gransk.core.injector.Injector``
    """
    logger = logging.getLogger(u'worker')

    config[helper.WORKER_ID] = worker_id
    config[helper.INJECTOR] = injector

    pipe = pipeline.build_pipeline(config)

    mod = gransk.api.Subscriber(pipe)
    mod.setup(config)

    while True:
      try:
        path = queue.get(timeout=1)
      except Empty:
        logger.info((u'[normal stop] worker %s' % worker_id).encode('utf-8'))
        break

      try:
        doc = document.get_document(path, parent=document.get_document('root'))
        mod.consume(doc)
      except KeyboardInterrupt:
        logger.info("[aborting] worker %s" % worker_id)
        break

    pipe.stop()

    with open(os.path.join(config[helper.DATA_ROOT], 'time-%s.csv' % worker_id), 'w') as out:
      out.write('%s;%s;%s;%s\n' % ('consumer', 'total', 'consume_count', 'avg'))
      for consumer, (total, consume_count, avg) in pipe.get_time_report():
        out.write('%s;%.2f;%.2f;%.2f\n' % (consumer, total, consume_count, avg))

  def boot(self, injector, config, match_path):
    """
    Initialize workers and queue. Find all matching documents and add these
    to the pipeline.

    :param injector: Object from which to fetch dependencies.
    :param config: Configuration object.
    :param match_path: Path passed to ``glob()`` to identify folders and files.
    :param injector: Object from which to fetch dependencies.
    :type config: ``dict``
    :type match_path: ``unicode``
    :returns: Processed paths.
    """
    logger = logging.getLogger(u'boot')

    data_root = config.get(helper.DATA_ROOT, 'local_data')
    config[helper.DATA_ROOT] = data_root

    if not os.path.exists(config[helper.DATA_ROOT]):
      os.makedirs(config[helper.DATA_ROOT])

    queue = Queue(maxsize=2)
    workers = []

    for worker_id in range(config.get(helper.WORKERS, 1)):
      proc = Process(
          target=self.init,
          args=(config, queue, worker_id, injector))

      workers.append(proc)
      proc.start()

    paths = []

    for path in glob.glob(match_path):
      paths.extend([x for x in collector.Collector(
          config.get(helper.COLLECTOR, {})).collect(path)])

    for path in tqdm(paths):
      queue.put(path)

    running = 1

    while running > 0:
      running = 0
      for worker in workers:
        if worker.is_alive():
          running += 1

      time.sleep(0.01)

    logger.info('Stopping')

    return paths



def parse_args(arg_list):
  """
  Parse command line arguments.

  :param arg_list: Command line arguments
  :type arg_list: ``list``
  :returns: argparse object.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument('path')
  parser.add_argument('--config', '-c', default=None)
  parser.add_argument('--tag', '-t', default='default')
  parser.add_argument('--%s' % helper.IN_FILTER, default=[], nargs='*')
  parser.add_argument('--%s' % helper.END_FILTER, default=[], nargs='*')
  parser.add_argument(
      '--%s' % helper.MAX_FILE_SIZE, default=64, type=float, help='In megabytes. 0 = no limit')
  parser.add_argument('--%s' % helper.WORKERS, default=1, type=int)
  parser.add_argument(
      '--%s' %
      helper.NEGATE,
      dest='negate',
      action='store_true')
  parser.add_argument('--debug', dest='debug', action='store_true')
  parser.add_argument('--clear', dest='clear', action='store_true')

  parser.set_defaults(debug=False, unpack=False, clear=False)
  return parser.parse_args(arg_list)


def load_config(args, inject=None):
  """
  Load configuration file. Override with arguments from command line.

  :param args: Argparse object.
  :returns: Gransk API object (``API``)
  """
  config_path = getattr(args, 'config', None)

  gransk_api = gransk.api.API(config_path=config_path, injector=inject)

  gransk_api.config[helper.WORKERS] = getattr(args, 'workers', 0)
  gransk_api.config[helper.MAX_FILE_SIZE] = getattr(args, 'max_file_size', 0)
  gransk_api.config[helper.TAG] = getattr(args, 'tag', 'default')

  gransk_api.config[helper.COLLECTOR] = {
      helper.IN_FILTER: getattr(args, 'in_filter', []),
      helper.END_FILTER: getattr(args, 'end_filter', []),
      helper.NEGATE: getattr(args, 'negate', False)
  }

  return gransk_api


def run(inject, arg_list):
  """
  Start processing using the provided arguments.

  :param inject: Inector object from wich dependencies are fetched from.
  :param arg_list: List of arguments from command line.
  :type inject: ``gransk.core.injector.Injector``
  :type arg_list: ``list``
  """
  args = parse_args(arg_list)

  logging.getLogger('urllib3').setLevel(logging.ERROR)
  logging.getLogger('requests').setLevel(logging.ERROR)
  logging.getLogger('polyglot').setLevel(logging.ERROR)
  logging.basicConfig(
      format=u'[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
      level=logging.DEBUG if args.debug else logging.INFO,
      datefmt=u'%Y-%m-%d %H:%M:%S')

  gransk = load_config(args, inject)

  inject.set_config(gransk.config)

  worker = inject.get_worker()

  if args.clear:
    gransk.clear_all()

  for _ in worker.boot(inject, gransk.config, args.path):
    pass


def main():
  """Entry point - Start processing. Reads arguments from sys.argv."""
  import gransk.core.injector as injector

  inject = injector.Injector()
  run(inject, sys.argv[1:])

if __name__ == '__main__':
  main()
