#!python

from distutils.core import setup

setup(name='zftracking-linux64',
      version='2.2',
      description='Workflow for tracking fish',
      author='Nils Jonathan Trost',
      author_email='nils.trost@stud.uni-heidelberg.de',
      packages=['zftracking', 'zftracking.external', 'zftracking.tracking'],
      package_data={'zftracking.external': ['data/*.txt']},
      scripts=['zftracking/scripts/zftracking_wf.py',
               'zftracking/scripts/zftracking_adult.py',
               'zftracking/scripts/zftracking_larva.py'])
