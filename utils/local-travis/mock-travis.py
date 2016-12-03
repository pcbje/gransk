import subprocess
import sys

proc = subprocess.Popen('pip install pyyaml'.split(), stdout=subprocess.PIPE)
out, err = proc.communicate()

import yaml

with open('.travis.yml') as inp:
    data = yaml.load(inp.read())

cmds = ['set -e']

for python_version in data['python']:
    python = 'python%s' % python_version
    cmds.append('find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf')
    cmds.append('virtualenv --system-site-packages -p %s /pyenv/%s' % (python, python))
    cmds.append('. /pyenv/%s/bin/activate' % python)
    cmds.extend(data['install'])
    cmds.extend(data['script'])
    cmds.append('deactivate')

with open('mock-travis.sh', 'w') as out:
    out.write('\n'.join(cmds))

proc = subprocess.Popen('/bin/bash mock-travis.sh'.split(), stdout=subprocess.PIPE)

while True:
  line = proc.stdout.readline()
  if not line:
    break
  sys.stdout.write(line)
  sys.stdout.flush()

proc.communicate()

if proc.returncode == 0:
    print ('BUILD OK')
else:
    print ('BUILD FAILED')
