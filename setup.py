from setuptools import setup, Extension, find_packages
import versioneer

classifiers = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Framework :: Twisted',	
    'Topic :: Communications',
    'Topic :: Internet',
    'Development Status :: 3 - Alpha',
]


setup(name             = 'twisted-mqtt',
      version          = versioneer.get_version(),
      cmdclass         = versioneer.get_cmdclass(),
      author           = 'Rafael Gonzalez',
      author_email     = 'astrorafael@yahoo.es',
      description      = 'MQTT client protocol package for Twisted',
      long_description = open('README.md').read(),
      license          = 'MIT',
      keywords         = 'Python Twisted',
      url              = 'http://github.com/astrorafael/twisted-mqtt/',
      classifiers      = classifiers,
      packages         = find_packages(exclude=['mqtt.test', 'mqtt.client.test']),
      install_requires = ['twisted >= 15.4.0'],
  )
