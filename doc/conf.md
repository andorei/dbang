# Config Files Structure

Config-files for dbang utilities, except `hedwig`, have the same structure:

```
import os
import sys

from sources import sources

#
# SETTINGS USED BY utility
#
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
DEBUGGING = True
LOGGING = True
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

#
# SETTINGS USED IN specs
#
# ...

specs = {
    "<spec_1>": {
        "source": "<source_1>",
        ...
    },
    "<spec_2>": {
        "source": "<source_2>",
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

Config-files for `hedwig` do not import nor use data sources from `sources`. The rest is similar.

After `import` statements there goes a block of parameters used by utilities. All such parameters are defined in test config-files and while they might be useful they are not mandatory. If omited the utilities behave by default.

The block of utility parameters is followed by an optional block of user defined variables. If you have to repeatedly use the same expressions in specs then consider defining variables and using them instead.

The `specs` dict contains named specifications (which are dicts) and is the core of a config-file. Specs tell utilities what exactly to do. See test config-files for the commented specifications.

After `specs` dict there might be definitions of DB queries to be executed once upon establishing DB connection. If, for example, the utility or the config-file specs require a certain table in DB or specific session parameters then add necessary SQL statements to the `"setup"` list of the data source. To have SQL statements executed just before closing DB connection, add the statements to the `"upset"` list. See examples of `"setup"` and `"upset"` SQL statements in test config-files.
