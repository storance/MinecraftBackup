import zipfile
import tarfile
from functools import partial

__all__ = ['Archiver', 'ZipArchiver', 'TarArchiver', 'ArchiverDefinition', 'DEFINITIONS']

class Archiver(object):
    def add(self, file, archive_name):
        raise NotImplementedError()
    
    def close(self):
        raise NotImplementedError()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exec_type, exec_value, exec_traceback):
        self.close()
    
class ZipArchiver(Archiver):
    def __init__(self, output_file, compression=zipfile.ZIP_DEFLATED):
        self.zip = zipfile.ZipFile(output_file, 'w', compression=compression)
        
    def add(self, file, archive_name):
        self.zip.write(file, archive_name)
    
    def close(self):
        self.zip.close()

class TarArchiver(Archiver):
    def __init__(self, output_file, compression='gz'):
        self.compression = compression
        self.tar = tarfile.open(output_file, mode='w:' + compression)
        
    def add(self, file, archive_name):
        self.tar.add(file, archive_name)
        
    def close(self):
        self.tar.close()
    

class ArchiverDefinition(object):
    def __init__(self, archive_format, archiver_class, default_ext):
        self.format = archive_format
        self.archiver_class = archiver_class
        self.default_ext = default_ext


    def open(self, output_file):
        return self.archiver_class(output_file)
        
DEFINITIONS = {}
def _define_archive_format(archive_format, archiver_class, default_ext):
    DEFINITIONS[archive_format] = ArchiverDefinition(archive_format, archiver_class, default_ext)

_define_archive_format('zip',           partial(ZipArchiver, compression=zipfile.ZIP_DEFLATED), 'zip')
_define_archive_format('zip|deflate',   partial(ZipArchiver, compression=zipfile.ZIP_DEFLATED), 'zip')
_define_archive_format('zip|bz2',       partial(ZipArchiver, compression=zipfile.ZIP_BZIP2),    'zip')
_define_archive_format('tar',           partial(TarArchiver, compression=''),                   'tar')
_define_archive_format('tar|gz',        partial(TarArchiver, compression='gz'),                 'tar.gz')
_define_archive_format('tar|bz2',       partial(TarArchiver, compression='bz2'),                'tar.bz2')
_define_archive_format('tar|xz',        partial(TarArchiver, compression='xz'),                 'tar.xz')
