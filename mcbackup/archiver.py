'''
Created on Jun 15, 2011

@author: AgmMaverick
'''

import zipfile
import tarfile

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
    
        