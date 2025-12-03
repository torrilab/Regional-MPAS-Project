import fnmatch
import os

#PATH = '/glade/p/nsc/ncgd0048/mpas_35-1.5km/'
#
#matches = []
#for root, dirnames, filenames in os.walk(PATH):
#    for filename in fnmatch.filter(filenames, 'diag_mom6*'):
#        #print(root+'/'+filename)
#        os.system('ncdump -h '+root+'/'+filename)
#        #matches.append(os.path.join(root, filename))



#------------------------------------- python > 3.5
import glob

PATH = '/glade/derecho/scratch/aroseman'
files = [file for file in glob.glob(PATH + '/**/*.nc', recursive=True)]

for f in files:
   os.system("ncdump -h "+f)
