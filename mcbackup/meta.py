import json
import datetime
import importlib
import uuid
import re
import os
from dateutil.parser import parse
from dateutil.tz import tzutc

__all__ = ['TAG_SNAPSHOT', 'TAG_HOURLY', 'TAG_DAILY', 'TAG_WEEKLY', 'TAG_MONTHLY', 'TAG_YEARLY', 'BackupMeta',
           'WorldMeta', 'load_meta', 'save_meta']

TAG_SNAPSHOT = 'snapshot'
TAG_HOURLY = 'hourly'
TAG_DAILY = 'daily'
TAG_WEEKLY = 'weekly'
TAG_MONTHLY = 'monthly'
TAG_YEARLY = 'yearly'

class BackupMeta(object):
    def __init__(self, backup_id=None, time=None, archive_format=None, worlds=[], tag=TAG_SNAPSHOT):
        self.id = backup_id if backup_id else str(uuid.uuid4())
        self.time = time if time else datetime.datetime.now(tzutc())
        self.archive_format = archive_format
        self.worlds = worlds if worlds else []
        self.tag = tag

    def retag(self, new_tag):
        return BackupMeta(self.id, self.time, self.archive_format, self.worlds, new_tag)

    def __eq__(self, other):
        if isinstance(other, BackupMeta):
            return self.id == other.id

        return False

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return "BackupMeta{{{}}}".format(
            self.id, self.time.isoformat(), self.worlds, self.tag)

class WorldMeta(object):
    def __init__(self, name=None, path=None):
        self.name = name
        self.path = path

    def __eq__(self, other):
        if isinstance(other, WorldMeta):
            return self.name == other.name

        return False

def load_meta(backup_dir):
    meta_path = _get_meta_path(backup_dir)

    if os.path.exists(meta_path):
        with open(meta_path, 'r') as file:
            return MetaDataJSONDecoder().decode(file.read())
    else:
        return []

def save_meta(backup_dir, meta_data):
    meta_path = _get_meta_path(backup_dir)
    with open(meta_path, 'w') as file:
        file.write(MetaDataJSONEncoder().encode(meta_data))

def _get_meta_path(backup_dir):
    return os.path.join(backup_dir, "meta.json")

class MetaDataJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            value = obj.astimezone(tzutc()).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            # strip off the microseconds part leaving on milliseconds
            return value[:23] + value[26:]
        else:
            obj_as_dict = {"__type__" : "{}.{}".format(obj.__class__.__module__, obj.__class__.__name__)}
            obj_as_dict.update(obj.__dict__)
            return obj_as_dict

class MetaDataJSONDecoder(json.JSONDecoder):
    def __init__(self, parse_float=None, parse_int=None, parse_constant=None, strict=True):
        super(MetaDataJSONDecoder, self).__init__(_object_hook, parse_float, parse_int, parse_constant, strict)

    def decode(self, s, *args, **kwargs):
        result = super(MetaDataJSONDecoder, self).decode(s, *args, **kwargs)
        return _parse_value(result)

def _object_hook(data):
    if "__type__" in data:
        clz = _load_class(data["__type__"])
        obj = clz()
        for (key, value) in data.items():
            if key == "__type__":
                continue

            setattr(obj, key, _parse_value(value))

        return obj
    else:
        for (key, value) in data.items():
            data[key] = _parse_value(value)

        return data

def _parse_value(value):
    if type(value) == str:
        return _handle_string(value)
    elif type(value) == list:
        return [_parse_value(element) for element in value]
    else:
        return value

def _handle_string(value):
    if re.match(r'\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\.\d\d\dZ', value):
        try:
            return parse(value)
        except ValueError:
            return value
    else:
        return value

def _load_class(full_class_name):
    (modulename, classname) = full_class_name.rsplit('.', 1)

    module = importlib.import_module(modulename)
    return getattr(module, classname)
