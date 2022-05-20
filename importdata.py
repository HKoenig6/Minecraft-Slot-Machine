# AUTHOR: Hans Koenig
#
# This class contains the methods required to import slot machine image
# data to an SQL server using cv2 and mysql.connector. The data was imported in these
# three steps:
#   1- split raw image files into individual blocks for image parsing
#   2- implement and test method that identifies label using cv2
#   3- import all data to local MySQL server
# Quantifying this data allows for further statistical analysis on a sample of
# 1000 spins from the slot machine.

import cv2 as cv
import csv
import numpy as np
import os
import mysql.connector
from PIL import Image

# Workspace path
root_dir = 'path/to/Minecraft-Slot-Machine'

# mysql connection
mydb = mysql.connector.connect(
    host='localhost',
    user='<user>',
    password='<password>'
)

# input: mysql cursor
# output: N/A
#
# initializes a database and table to import the slot machine
# spins.
def init_database(dbcursor):
    dbcursor.execute('CREATE DATABASE slots_data')
    dbcursor.execute('USE slots_data')
    dbcursor.execute('CREATE TABLE spins (s INT(4), b1 INT(4), b2 INT(4), b3 INT(4), b4 INT(4), b5 INT(4), b6 INT(4), b7 INT(4), b8 INT(4), b9 INT(4))')
    dbcursor.execute('SHOW TABLES')
    for test in dbcursor:
        print(test)

# input: raw image path, cropped images path
# output: N/A
#
# Takes each raw image from minecraft's screenshots folder and
# splits it into nine images of each respective block in the spin. The convention
# used to index blocks is left-to-right, starting with the top left block.
def split_image(img_num, path):

    #format raw image
    raw_img = Image.open('raw_images/spin (' + str(img_num) + ").png")
    cropped_img = raw_img.crop((632, 12, 1933, 1370)) # these values differ over other resolutions

    #create unique dir for sample
    spin_path = os.path.join(path, 's' + str(img_num))
    os.mkdir(spin_path)

    #save new elements, partitioned into 9 blocks
    w, h = cropped_img.size
    for i in range(3):
        for j in range(3):
            block = cropped_img.crop((j*w/3 + 100, i*h/3 + 100, j*w/3 + 200, i*h/3 + 200))
            block.save(spin_path + "/b" + str(3*i + j + 1) + '.png')

# this structure defines the lower and upper bounds of RGB values for each block, organized
# by their abstraction in the slot machine. I found these values by colorpicking in paint.net 
# since minecraft block colors are simple.
ranges = np.array([([62,37,107],[107,82,153]), # amethyst (A)
([154,154,154],[180,180,180]), # iron (I)
([121,74,23],[184,147,40]), # raw gold (R)
([180,152,40],[190,188,109]), # gold (G)
([12,138,44],[99,183,130]), # emerald (E)
([68,172,159],[119,189,175]), # diamond (D)
([43,41,43],[61,58,61]), # netherite (N)
([59,111,12],[128,174,78])]) # clover (C)

# input: image path
# output: indexed label in range [0,7]
#
# Masks each image from the dataset for each block and returns
# the index of the correct label.
def label_image(path):

    # read image and convert to rgb
    img = cv.imread(path)
    rgbimg = cv.cvtColor(img, cv.COLOR_BGR2RGB)

    max = 0 # min average = 0 if no pixels land in specified threshold
    label = -1
    for index in range(8):
        # mask image and compute average over all channels
        mask = cv.inRange(rgbimg, ranges[index][0],ranges[index][1])
        average = np.mean(np.array(cv.mean(mask)))
        
        # record index of masked image with highest average (most white pixels)
        if average > max:
            label = index
            max = average

    return label 

# input: N/A
# output: N/A
#
# I manually wrote down labels for the first 100 spins in this
# sample, and this method compares those values with the labels
# returned from label_image.
def test_correctness():
    errors = 0
    for spin in range(100):
        filepath = root_dir + '/dataset/s' + str(spin + 1)
        with open(filepath + '/labels.csv', 'r', encoding='utf-8') as csvFile:
            reader = csv.DictReader(csvFile)
            for row in reader:
                label = int(label_image(filepath + '/b' + str(row['Block']) + '.png'))
                error = 0

                #switch case to compare index with CSV label
                if label == 0 and row[' Label'] != ' A':
                    error = 1
                elif label == 1 and row[' Label'] != ' I':
                    error = 1
                elif label == 2 and row[' Label'] != ' R':
                    error = 1
                elif label == 3 and row[' Label'] != ' G':
                    error = 1
                elif label == 4 and row[' Label'] != ' E':
                    error = 1
                elif label == 5 and row[' Label'] != ' D':
                    error = 1
                elif label == 6 and row[' Label'] != ' N':
                    error = 1
                elif label == 7 and row[' Label'] != ' C':
                    error = 1
                if error:
                    print('ERROR (spin ' + str(spin + 1) + ', block ' + str(row['Block']) + ')')
                    print(row)
                    print(label)
                    errors = errors + 1
    
    accuracy = float(900-errors) / float(900)
    return accuracy

# input: mysql cursor
# output: N/A
# 
# Uses label_image for all blocks to organize and import all data
# into an SQL server. Each block is labelled by the decimal value of its binary
# representation in the game.
def import_spins(dbcursor):
    dbcursor.execute('USE slots_data')
    entry = {'s': 0, 'b1':-1, 'b2':-1, 'b3':-1, 'b4':-1, 'b5':-1, 'b6':-1, 'b7':-1, 'b8':-1, 'b9':-1}

    #iterate over all spins
    for s in range(1000):
        entry['s'] = s + 1
        for b in range(9):
            path = root_dir + '/dataset/s' + str(s + 1) + '/b' + str(b+1) + '.png'
            key = 'b' + str(b+1)
            entry[key] = label_image(path)
        
        cmd = 'INSERT INTO spins (s, b1, b2, b3, b4, b5, b6, b7, b8, b9) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        dbcursor.execute(cmd, (entry['s'], entry['b1'], entry['b2'], entry['b3'], entry['b4'], entry['b5'], entry['b6'], entry['b7'], entry['b8'], entry['b9']))
        mydb.commit()

# main driver; I used this interchangeably with the
# interpreter for debugging
if __name__ == '__main__':
    for img_num in range(1000):
        split_image(img_num + 1, os.path.join(root_dir, 'dataset'))
    accuracy = test_correctness()
    print(accuracy)
    init_database(mydb.cursor())
    import_spins(mydb.cursor())