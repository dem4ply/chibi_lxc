=========
chibi_lxc
=========


.. image:: https://img.shields.io/pypi/v/chibi_lxc.svg
        :target: https://pypi.python.org/pypi/chibi_lxc

.. image:: https://img.shields.io/travis/dem4ply/chibi_lxc.svg
        :target: https://travis-ci.org/dem4ply/chibi_lxc

.. image:: https://readthedocs.org/projects/chibi-lxc/badge/?version=latest
        :target: https://chibi-lxc.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

definition of lxc containers using python class and manage lxc
similar to vagrant


Example
-------

write a file with the container

.. sourcecode:: python

	from chibi_lxc import Container
	class Centos_8( Container ):
		name = 'centos_8'
		distribution = 'centos'
		arch = 'amd64'
		version = '8'
		provision_folders = { 'scripts': 'provision' }
		env_vars = { 'LC_ALL': 'es_MX.utf8' }
		scripts = ( 'install_python.sh', ( 'add_user.py', 'chibi', ) )

write a config.py

with the next conten

.. sourcecode:: python

	import sys
	from chibi.config import configuration
	from chibi.file import Chibi_path
	from chibi.module import import_

	sys.path.append( Chibi_path( '.' ).inflate )

	from containers.base import Centos_7


	configuration.chibi_lxc.containers.add( Centos_7 )


the scripts should be in the folder provision_folders[ 'scripts' ]


create the container

::
	chibi_lxc up Centos_8 # create the container
	chibi_lxc provision Centos_8 # not needed the first time
	chibi_lxc list # lista los container configurados
	chibi_lxc status # lista el status de los container
	chibi_lxc host # lista el estado y hosts de los container
	chibi_lxc stop Centos_8 # stop the container
	chibi_lxc destroy Centos_8 # destroy the container


* Free software: WTFPL
* Documentation: https://chibi-lxc.readthedocs.io.


Features
--------

* create container
* provision container
* destroy container
