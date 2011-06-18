'''
Created on Jun 15, 2011

@author: Steven Torance
'''
import argparse
import archiver
import os
import datetime

FORMAT_CHOICES = ('zip', 'tar.gz', 'tar.bz2')

class WorldBackup(object):
    @staticmethod
    def get_all_worlds(worldDir):
        worlds = []
        for dir in os.listdir(worldDir):
            fullPath = os.path.join(worldDir, dir)
            
            if os.path.isdir(fullPath):
                levelDatFile = os.path.join(fullPath, "level.dat")
                if os.path.exists(levelDatFile):
                    worlds.append(dir)
                    
        return worlds
    
    def __init__(self, worldDir, worldName, archiveFormat, backupDir, filenameFormat):
        self.worldDir = worldDir
        self.worldName = worldName
        self.archiveFormat = archiveFormat
        self.backupDir = backupDir
        self.filenameFormat = filenameFormat
        
    def run(self):
        outputFile = self.createOutputFile()
        
        if self.archiveFormat == 'zip':
            fileArchiver = archiver.ZipArchiver(outputFile)
        elif self.archiveFormat == 'tar.gz':
            fileArchiver = archiver.TarArchiver(outputFile, 'gz')
        elif self.archiveFormat == 'tar.bz2':
            fileArchiver = archiver.TarArchiver(outputFile, 'bz2')
        else:
            raise Exception("Invalid archive format " + self.archiveFormat)
            
            
        worldPath = os.path.join(self.worldDir, self.worldName)
        
        for (dirpath, dirs, files) in os.walk(worldPath):
            for file in files:
                fullPath = os.path.join(dirpath, file)
                relativePath = os.path.relpath(fullPath, self.worldDir)
                
                fileArchiver.add(fullPath, relativePath)
        
        fileArchiver.close()    
        
    def createOutputFile(self):
        currentDate = datetime.datetime.now()
                
        relativePath = self.filenameFormat.format(currentDate, self.worldName, self.archiveFormat)
        outputFile = os.path.join(self.backupDir, relativePath)
        os.makedirs(os.path.dirname(outputFile), exist_ok=True)
        
        return outputFile


def main():
    parser = argparse.ArgumentParser(description='Utility to backup Minecraft worlds.')
    
    parser.add_argument('-a', '--archive-format',
                        dest='archiveFormat',
                        metavar='FORMAT',
                        choices=FORMAT_CHOICES,
                        default='tar.gz',
                        help='The archive format to use.  Supported formats are zip, tar.gz, and tar.bz2.  ' + \
                            'Default is tar.gz')
    parser.add_argument('-f', '--filename-format',
                        dest='filenameFormat',
                        metavar='FORMAT',
                        default="{0:%Y}/{0:%B}-{0:%d}/{1}-{0:%H%M%S}.{2}",
                        help='The format of the backup world which may be a relative path to backupDir.  ' + \
                            '{0} is the current time, {1} is the world name, and {2} is the archive format extension. ' + \
                            'Default is {0:%%Y}/{0:%%B}-{0:%%d}/{1}-{0:%%H%%M%%S}.{2}')
    
    parser.add_argument('worldDir', help="The path to the directory containing the worlds.")
    parser.add_argument('backupDir', help="The path to the directory where the backups will be written.")
    parser.add_argument('worlds',
                        metavar='worldName',
                        default=[],
                        nargs='*',
                        help="The worlds to backup.  If no worlds are specified, all worlds in worldDir are backed up.")
    args = parser.parse_args()
        
    worlds = args.worlds
    if len(worlds) == 0:
        worlds = WorldBackup.get_all_worlds(args.worldDir)
        
    for world in worlds:
        print ("Backing up " + world)
        backup = WorldBackup(args.worldDir, world, args.archiveFormat, args.backupDir, args.filenameFormat)
        backup.run()

if __name__ == '__main__':
    main()
