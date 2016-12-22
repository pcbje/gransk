#!/usr/bin/env python

from __future__ import print_function

import os
import re
import sys
from collections import defaultdict

pattern = re.compile('(?:[^_])helper\.([A-Z_]+)')

direct_patterns = [
    re.compile('(?:[^_])config\.get\((?:u?)(?:\'|\")([^\'\"]+)'),
    re.compile('(?:[^_])config\[(?:\'|\")([^\'\"]+)')
]


use = defaultdict(set)
direct = defaultdict(set)

for folder, _, paths in os.walk(sys.argv[1]):
    for p in paths:
        with open(os.path.join(folder, p)) as inp:
            data = inp.read()
            for m in pattern.findall(data):
                use[m].update([p])

            for direct_pattern in direct_patterns:
                for m in direct_pattern.findall(data):
                    direct[m].update([p])

for m in sorted(use.keys()):
    #print("%s = '%s' # %s" % (m, m.lower(), ', '.join(use[m])))
    print("%s = '%s'" % (m, m.lower()))

print("\n\n__DIRECT__")

for m in sorted(direct.keys()):
    print("%s = '%s' # %s" % (m.upper(), m, ', '.join(direct[m])))
