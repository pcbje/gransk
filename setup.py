#!/usr/bin/env python
from setuptools import setup, find_packages
from setuptools.command.develop import develop

import glob
import os


class DownloadPolyglotData(develop):

  def run(self):
    os.system('polyglot download embeddings2.no ner2.no')
    os.system('polyglot download embeddings2.en ner2.en')

data_files = []

for folder, _, filenames in os.walk('gransk/web'):
    if 'node_modules' in folder:
      continue
      
    for filename in filenames:
        data_files.append((folder, [os.path.join(folder, filename)]))

data_files.append(('utils', [x for x in glob.glob('utils/*') if os.path.isfile(x)]))
data_files.append('config.yml')

setup(
    name='gransk',
    author='Petter Christian Bjelland',
    version='0.3',
    author_email='petter.bjelland@gmail.com',
    description='',
    license='',
    packages=find_packages('.', exclude=['*.py', '*.tests']),
    data_files=data_files,
    cmdclass={
        'download': DownloadPolyglotData
    }
)
