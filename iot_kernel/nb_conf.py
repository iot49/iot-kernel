from iot_device import Env
import ipynbname, os
import json

"""Store per notebook configuration as a dict. 
    Keys: "device", "cwd"
"""

class NbConf:

    @staticmethod
    def get(key, default=None):
        """Return configuration parameter for active notebook"""
        config = NbConf._load_config()
        return config.get(key, default)

    @staticmethod
    def set(key, uid_or_name_or_path):
        """Set configuration parameter for active notebook"""
        config = NbConf._load_config()
        config[key] = uid_or_name_or_path
        NbConf._store_config(config)


    _DB = Env.expand_path(os.path.join('~', ".iot49_connect_rc"))

    @staticmethod
    def _store_config(config):
        """Store config dict for active notebook"""
        try:
            with open(NbConf._DB) as f:
                db = json.loads(f.read())
        except FileNotFoundError:
            db = {}
        db[str(ipynbname.path())] = config
        with open(NbConf._DB, 'w') as f:
            json.dump(db, f, indent=4, sort_keys=True)

    @staticmethod
    def _load_config():
        """Load config dict for active notebook"""
        try:
            with open(NbConf._DB) as f:
                db = json.load(f)
                return db.get(str(ipynbname.path()), {})
        except FileNotFoundError:
            return {}

