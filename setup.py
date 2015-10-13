from setuptools import setup

from guano import __version__


setup(
    name='guano',
    version=__version__,
    description='GUANO, the "Grand Unified" bat acoustics metadata format',
    long_description=open('README.md').read(),
    url='https://github.com/riggsd/guano-py',
    license='MIT',
    author='David A. Riggs',
    author_email='driggs@myotisoft.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='bats acoustics metadata',
    py_modules=['guano'],
    scripts=['bin/sb2guano.py'],
)
