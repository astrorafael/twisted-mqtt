from setuptools import setup, Extension, find_packages
import versioneer

# Default description in markdown
long_description = open('README.md').read()
 
# Converts from makrdown to rst using pandoc
# and its python binding.
# Docunetation is uploaded in PyPi when registering
# by issuing `python setup.py register`

try:
    import subprocess
    import pandoc
 
    process = subprocess.Popen(
        ['which pandoc'],
        shell=True,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
 
    pandoc_path = process.communicate()[0]
    pandoc_path = pandoc_path.strip('\n')
 
    pandoc.core.PANDOC_PATH = pandoc_path
 
    doc = pandoc.Document()
    doc.markdown = long_description
 
    long_description = doc.rst
 
except:
    pass
   


classifiers = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.4',
    'Framework :: Twisted',	
    'Topic :: Communications',
    'Topic :: Internet',
    'Development Status :: 4 - Beta',
]


setup(name             = 'twisted-mqtt',
      version          = versioneer.get_version(),
      cmdclass         = versioneer.get_cmdclass(),
      author           = 'Rafael Gonzalez',
      author_email     = 'astrorafael@yahoo.es',
      description      = 'MQTT client protocol package for Twisted',
      long_description = long_description,
      license          = 'MIT',
      keywords         = 'Python Twisted',
      url              = 'http://github.com/astrorafael/twisted-mqtt/',
      classifiers      = classifiers,
      packages         = find_packages(exclude=['mqtt.test', 'mqtt.client.test']),
      install_requires = ['twisted >= 16.2.0'],
  )
