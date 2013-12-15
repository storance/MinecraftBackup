import os
import datetime
from dateutil.tz import tzlocal, tzutc
from .archiver import DEFINITIONS
from . import meta

__all__ = ['WorldBackup', 'backup']

class WorldBackup(object):
    @staticmethod
    def get_all_worlds(world_dir):
        worlds = []
        for world in os.listdir(world_dir):
            full_path = os.path.join(world_dir, world)
            
            if os.path.isdir(full_path):
                level_dat_file = os.path.join(full_path, "level.dat")
                if os.path.exists(level_dat_file):
                    worlds.append(world)
                    
        return worlds
    
    def __init__(self, world_path, archiver, output_file):
        if not os.path.exists(world_path):
            raise ValueError("The world {} does not exists".format(world_path))

        if not os.path.isdir(world_path):
            raise ValueError("The world {} is not a directory".format(world_path))

        self.world_path = world_path
        self.archiver = archiver
        self.output_file = output_file
        
    def run(self):
        world_dir = os.path.dirname(self.world_path)

        with self.archiver.open(self.output_file) as file_archiver:
            for (dirpath, _, files) in os.walk(self.world_path):
                for file in files:
                    full_path = os.path.join(dirpath, file)
                    relative_path = os.path.relpath(full_path, world_dir)
                    
                    file_archiver.add(full_path, relative_path)
        
def backup(world_dir, worlds, backup_dir, filename_format, archive_format, retention_policy):
    archiver = DEFINITIONS[archive_format]
    worlds = worlds if worlds else WorldBackup.get_all_worlds(world_dir)

    meta_data = meta.load_meta(backup_dir)
    worlds_meta = []
    for world in worlds:
        world_path = os.path.join(world_dir, world)
        output_file = create_output_file(filename_format, backup_dir, world, archiver)

        print ("Backing up {} to {}".format(world, output_file))
        backup_task = WorldBackup(world_path, archiver, output_file)
        backup_task.run()
        worlds_meta.append(meta.WorldMeta(world, os.path.relpath(output_file, backup_dir)))

    meta_data.append(meta.BackupMeta(archive_format=archiver.format, worlds=worlds_meta))

    try:
        (meta_data, purge) = retention_policy.apply(meta_data)
        delete_backups(backup_dir, purge)
    finally:
        meta.save_meta(backup_dir, meta_data)

def create_output_file(filename_format, backup_dir, world_name, archiver):
    current_date = datetime.datetime.now(tzlocal())
    current_date_utc = datetime.datetime.now(tzutc())
            
    relative_path = filename_format.format(now=current_date, utcnow=current_date_utc, world=world_name,
                                           ext=archiver.default_ext)
    output_file = os.path.join(backup_dir, relative_path)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    return output_file    

def delete_backups(backup_dir, backups):
    for backup_meta in backups:
        for world_meta in backup_meta.worlds:
            world_path = os.path.join(backup_dir, world_meta.path)
            print ("Deleting old backup {}".format(world_path))
            os.unlink(world_path)

