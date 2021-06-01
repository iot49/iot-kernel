from iot_device import Env
import ipynbname, os

_DB = os.path.join(Env.iot_dir(), ".iot49_connect_rc")

def _load_db():
    try:
        with open(_DB) as f:
            return eval(f.read())
    except FileNotFoundError:
        return {}

def _store_db(db):
    with open(_DB, 'w') as f:
        f.write(repr(db))

def _notebook_path():
    return str(ipynbname.path())

def default_uid():
    """Return 'default' uid for currently active notebook"""
    db = _load_db()
    return db.get(_notebook_path())

def store_default_uid(uid):
    """Store uid as 'default' for currently active notebook"""
    db = _load_db()
    db[_notebook_path()] = uid
    _store_db(db)
