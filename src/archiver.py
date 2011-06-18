'''
Created on Jun 15, 2011

@author: AgmMaverick
'''

import zipfile
import tarfile

class Archiver(object):
    def add(self, file, archiveName):
        pass
    
    def close(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()
    
class ZipArchiver(Archiver):
    def __init__(self, outputFile):
        self.zip = zipfile.ZipFile(outputFile, 'w')
        
    def add(self, file, archiveName):
        self.zip.write(file, archiveName)
    
    def close(self):
        self.zip.close()

class TarArchiver(Archiver):
    def __init__(self, outputFile, compression='gz'):
        self.tar = tarfile.open(outputFile, mode='w:' + compression)
        
    def add(self, file, archiveName):
        self.tar.add(file, archiveName)
        
    def close(self):
        self.tar.close()
    
        