from setuptools import setup
from glob import glob

from guano import __version__


setup(
    name='guano',
    version=__version__,
    description='GUANO, the "Grand Unified" bat acoustics metadata format',
    long_description=open('README.rst').read(),
    url='https://github.com/riggsd/guano-py',
    license='MIT',
    author='David A. Riggs',
    author_email='driggs@myotisoft.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    keywords='bats acoustics metadata guano',
    py_modules=['guano'],
    scripts=glob('bin/*.py'),
)
