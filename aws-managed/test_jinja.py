#!/usr/bin/env python3

import unittest
import jinja2
import os, yaml, subprocess

from yamllint.config import YamlLintConfig
from yamllint import linter

COMPILED = 'test_jinja_compiled'
DEVNULL = open(os.devnull, 'w')

class TestJinja(unittest.TestCase):

  with open('./test_data.yaml', 'r') as stream:
    try:
      test_data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
      print(exc)

  conf = YamlLintConfig('{\
    extends: relaxed,\
    rules: {\
      key-duplicates: enable,\
      new-line-at-end-of-file: disable,\
      line-length:{max: 150},\
      trailing-spaces: disable,\
      indentation: {spaces: whatever},\
    }}')

  def setUp(self):
    if not os.path.exists(COMPILED):
      os.makedirs(COMPILED)

  def test_jinja(self):

    for full_path, context in self.test_data.items():
      path = os.path.dirname(full_path)
      file_name = os.path.basename(full_path)

      rendered = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path)
      ).get_template(file_name).render(context)

      compiled = '{}/{}'.format(
        COMPILED, file_name.replace('.yaml','.compiled.yaml'))

      with open(compiled, 'w') as text_file:
        text_file.write(rendered)

      try:
        yaml.load(rendered, Loader=yaml.BaseLoader)
      except:
        self.fail("Compiled template is not valid YAML")
        
      gen = linter.run(rendered, self.conf)
      self.assertFalse(list(gen),
        "Yamllint issues in compiled template")

      try:
        print("Validating {} ...".format(compiled))
        command = "aws cloudformation validate-template \
          --template-body file://{}".format(compiled)
        subprocess.check_call(command.split(), stdout=DEVNULL)
      except:
        self.fail("Validate template failed")

def main():
  unittest.main()

if __name__ == "__main__":
  main()
