# Config Files Structure

	version 0.3

Config files for **dbang** utilities, except `hedwig`, have the same structure:

```
import os
import sys

from sources import sources

#
# SETTINGS USED BY <utility>
#
# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to current working directory
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
# defaults to current working directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# data source
SOURCE = "<source_1>"

#
# SETTINGS USED IN specs
#
# ...

specs = {
    "<spec_1>": {
	    "tags": ["one"],
        ...
    },
    "<spec_2>": {
        "source": "<source_2>",
        ...
    },
    "--<spec_3>": {
	    "tags": ["one", "XXX"],
        ...
    },
}

sources['source_1']['setup'] = sources['source_1'].get('setup', []) + [
    "<SQL statement>"
]

sources['source_2']['setup'] = sources['source_2'].get('setup', []) + [
    "<SQL statement>"
]
```

Config files for `hedwig` do not import nor use data sources from `sources`. The rest is similar.

After `import` statements there goes a block of parameters used by utilities. All the parameters are described in the documentation on each utility and in the test config files. All but a few parameters are optional which means they have default values.

The block of utility parameters is followed by an optional block of user defined variables. If you repeatedly use the same expressions in specs then consider defining variables and using them instead.

The `specs` dict contains named specifications (which are Python dictionaries) and is the core of a config file. Specs tell utilities what exactly to do. See specs' details in the documentation on each utility and in the test config files.

After `specs` dict there might be definitions of DB queries to be executed once upon establishing DB connection. If, for example, the utility or the config file specs require a certain table in DB or specific session parameters then add necessary SQL statements to the `"setup"` list of the data source. To have SQL statements executed just before closing DB connection, add the statements to the `"upset"` list. See examples of `"setup"` and `"upset"` SQL statements in test config files.

## Running specs

All `dbang` utilities have optional command line argument `spec` that goes after `cfg_file`. With this argument you either specify the name of spec found in config file or one of the tags defined in spec parameter `"tags"`. By assigning the same tag to several specs in a config file you group these specs and make it possible to run them with one launch of the utility.

A spec in config file may be commented out with `--` at the beginning of spec name. Commented out specs do not run.

## Spec Startup and Completion

This section relates to config files of all `dbang` utilities except `hedwig`.

Sometimes at spec startup it is necessary to do some preparatory work, for example, aggregate data in a temporary table that will be used in the spec queries. In this case just put required SQL statements or procedure calls in spec parameter `"setup"`. See an example below.

Likewise, sometimes it is necessary to do a finalization at the end of spec execution. In this case just put required SQL statements or procedure calls in spec parameter `"upset"`. See an example below.

```
specs = {
    "<spec_1>": {
	    "setup": "create view myvw as select 3.14 pi",
        ...
	    "upset": "drop view myvw",
    },
    "<spec_2>": {
	    "setup": [
	        "call prepare_data()",
	        """
	        create view my_data as
	        select
	        ...
	        """
	    ],
        ...
	    "upset": [
		    "drop view my_data",
		    "call dismiss_data()"
		],
    },
}
```

As it is seen from the example, parameters `"setup"` and `"upset"` may be either a string containing a single SQL statement or a list of strings with SQL statements to be executed in the order they occur in the list.
