import os,sys,re,random,shutil
import collections
import numpy as np
import pickle

import pdb

#source_dir = sys.argv[1] #/raid/rll943/PinsByCategory/images
#dest_dir = sys.argv[2] #/raid/rll943/PinsByCategory/split_images
source_dir = '/raid/rll943/PinsByCategory/images'
dest_dir = '/raid/rll943/PinsByCategory/split_images'
broken_dir = '/raid/rll943/PinsByCategory/broken.txt'

if not os.path.exists(dest_dir+'/train'):
    os.mkdir(dest_dir+'/train/')
if not os.path.exists(dest_dir+'/val'):
    os.mkdir(dest_dir+'/val/')

max_cat = 999999 # no limit on maximum images in a class
min_cat = 16

label_dict = [o for o in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir,o))]

print "Found %d subdirectories at %s"%(len(label_dict),source_dir)

label_dict.remove('other')
label_dict.remove('unknown')

print "Use %d subdirectories as class labels"%len(label_dict)

with open(broken_dir,'r') as f:
    broken_filenames = f.readlines()


for k in label_dict:
    curr_path = os.path.join(source_dir,k)
    files = [f for f in os.listdir(curr_path) if os.path.isfile(os.path.join(curr_path, f))]
    
    if len(files) < min_cat:
        continue
    try:
        direct = "%s/train/%s" % ( dest_dir , k) 
        direcv = "%s/val/%s" % ( dest_dir , k) 
    except:
        print "no directory, skip"
        continue
    
    os.mkdir(direct)
    os.mkdir(direcv)
    has_file_in_train = False
    has_file_in_val = False

    for fname in files:
        if '%s/%s\n' % (k, fname) in broken_filenames:
            print 'Remove %s/%s' % (k,fname)
            files.remove(fname)
    for i in range(min(max_cat,len(files))):
        fname = files[i]
        src_file = "%s/%s/%s"%(source_dir,k,fname)
        dest_file = ""
        if i == 0:
            dest_file = "%s/%s"%(direct,fname)
        elif i == 1:
            dest_file = "%s/%s"%(direcv,fname)
        elif random.random()<0.9:
            dest_file = "%s/%s"%(direct,fname) # 9:1 split of train/valid
        else:
            dest_file = "%s/%s"%(direcv,fname)
            
        if os.path.isfile(src_file):
            shutil.copyfile(src_file,dest_file)
        else:
            print "not a file %s"%(src_file)
    
    tfiles = os.listdir(direct)
    vfiles = os.listdir(direcv)
    if (len(tfiles) ==0) or (len(vfiles) ==0):
        print "no jpg in %s"%(k)
    else:
        print "split of label %s finished. %d in train, %d in valid"%(k,len(tfiles),len(vfiles))

