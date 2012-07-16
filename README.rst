Getting started
===============

Mturk-Tracker is a Django web application and it is setup within python
virtualenv and requires a working python environment, PostgreSQL database and
Solr search engine.

Project setup
-------------

Currently deployment scripts should cover everything you need to setup the 
project. Only basic system configuration is required. First, create an user 
account which will have ownership to the project files and run ssh-server 
deamon.

Most things in the project are parametrized. The project configuration is based 
on json files that contain these parameters. Code responsible for deployment 
process exists in ``path/to/Mturk-Tracker/deployment/`` subdirectory. There is 
a fabric script responsible for most of deployment logic and templates of 
configuration files that are filled with deployment parameters. 

Two major files that contains deployment parameters: 

#. ``default.json`` - contains settings common across all project instances, 
   such as the repository URL.
#. ``site-name.json`` - contains settings specific for certain project. It also 
   contains sensitive data thus it does not exist in the repository.

Data from this files is used for generation of resultant configuration files
and scripts on the destination machine.

The structure of ``default.json`` file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file exists in the repository. It contains parameters common for all 
project instances. Only several parameters are usually overriden by 
``site-name.json`` that is described in the next section.

The structure of ``site-name.json`` file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file should contain instance-specyfic deployment parameters:

* ``projects_dir`` - path to the destination directory where the project files
  are to be stored;
* ``settings_name`` - name of the resultant settings file, that will be created 
  from settings template.
* ``locals_path`` - path to the additional custom Django settings file that you
  want to upload on the destination machine;
* ``db_name`` - name of the database;
* ``db_user`` - name of the database user used by crawler;
* ``db_password`` - password for the crawler database user;
* ``solr_db_user`` - name of the database user used by Solr during data import;
* ``sorl_db_password`` - password for the Solr database user;
* ``pip_requirements`` - list files that contanins set of Python packages to be 
  installed by pip;
* ``system_requirements`` - files that constains lists of system packages to be 
  installed by system package manager;
* ``branch`` - name of the repository branch;
* ``pip_cache`` - path to the directory where pip packages are cached on the
  destination machine;

Example ``site-name.json`` file:

::

	{
		"projects_dir": "/data/projects",
		"settings_name": "site-name",
		"db_name": "db",
		"db_user": "db_user",
		"db_password": "****",
		"solr_db_user": "db_solr_user",
		"solr_db_password": "*****",
		"pip_requirements": ["base.txt", "devel.txt", "production.txt", "tests.txt"],
		"system_requirements": ["system_requirements.txt"],
		"locals_path": /path/to/your/requirements/on/local/machine/local.py",
		"branch": "master"
	}

The structure of custom Django settings file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For better customization there is possibility to upload the file called
``local.py`` that can override some project parameters (for example in this
way you can disable page caching).
This file is uploaded during each deployment to the settings directory. It is 
imported to the main Django settings file.

Example local settings file may look like the following:

::

	import os
	from defaults import DATABASES, PROJECT_PATH, ROOT_PATH

	MEDIA_ROOT = os.path.join(ROOT_PATH, 'media')
	STATIC_ROOT = os.path.join(PROJECT_PATH, 'collected_static')
	STATIC_URL = '/static/'

	TIME_ZONE = 'UTC'
	CACHE_BACKEND = 'dummy:///'

	DB = DATABASES['default']
	DATABASE_NAME = DB['NAME']
	DATABASE_USER = DB['USER']
	DATABASE_PASSWORD = DB['PASSWORD']

	MTURK_AUTH_EMAIL = 'user@email.com'
	MTURK_AUTH_PASSWORD = '******'

	USE_CACHE = True

Running the deployment script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If all is already properly configured go to the deployment subdirectory:

::

	$ cd path/to/Mturk-Tracker/deployment/

and run the fabric script. The following command will install all requirements 
(including Python and system packages):

::

	$ fab deploy:conf_file="path/to/site-name.json",setup_environment=True -H 127.0.0.1 -u user

or you may want to update only project source (for example in order to apply 
changes from the repository):

::

	$ fab deploy:conf_file="path/to/site-name.json",requirements=False -H 127.0.0.1 -u user

For more information:

::

	$ fab help
