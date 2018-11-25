"""
CARPI COMMONS
(C) 2018, Raphael "rGunti" Guntersweiler
Licensed under MIT
"""

from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(name='carpi-settings',
      version='0.1.1',
      description='A library providing utilities for storing settings in a CarPi application.',
      long_description=long_description,
      url='https://github.com/rGunti/CarPi-Settings',
      keywords='carpi app settings',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6'
      ],
      author='Raphael "rGunti" Guntersweiler',
      author_email='raphael@rgunti.ch',
      license='MIT',
      packages=['carpisettings'],
      install_requires=[
          'carpi-commons',
          'wheel'
      ],
      extras_require={
          'redis': ['redis']
      },
      zip_safe=False,
      include_package_data=True)
