#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
    Script de test de la Kinect pour extraire la position 3D
    
"""
# paramètres variables #
display=True
record  = None #'position.mpg'
depth_min, depth_max= 0., 4.5
N_frame = 500 # time to learn the depth map
#max_depth = 3.5 # in meters
N_hist = 2**8 
threshold = 1.5
downscale = 4
smoothing = 1.5
noise_level = .5
# paramètres fixes #
depth_shape=(640,480)
matname = 'depth_map.npy'
i_frame = 0
record_list = []
image_depth = None
keep_running = True
start = True
#################################################
import freenect
import signal
#import frame_convert
from calibkinect import depth2xyzuv, xyz_matrix
import os
import numpy as np
depth_hist = np.load(matname)    
if display:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    #import pylab
    plt.ion()
#################################################
def display_depth(dev, data, timestamp, threshold, display=display):
    """
    
    Args:
    index: Kinect device index (default: 0)
    format: Depth format (default: DEPTH_11BIT)
    
    Returns:
    (depth, timestamp) or None on error
    depth: A numpy array, shape:(640,480) dtype:np.uint16
    timestamp: int representing the time

    """
    global image_depth, i_frame, depth_hist, record_list
    # low-level segmentation
    # from http://nicolas.burrus.name/index.php/Research/KinectCalibration
    Z = 1.0 / (data * -0.0030711016 + 3.3309495161)
    shadows = Z > depth_max # irrelevant calculations
    shadows += Z < depth_min # irrelevant calculations
    Z = Z * (1-shadows) + depth_max * shadows
    score = (depth_hist[:, :, 0] - Z) / (np.sqrt(depth_hist[:, :, 1]) + .5*np.sqrt(depth_hist[:, :, 1]).mean()) 
    score = score * (1-shadows)  - 10. * shadows
    attention = np.argwhere(score.ravel() > threshold)
    print score.min(), score.max(), score.mean()
    # computing positions
    U, V = np.mgrid[:480,:640]
    U_, V_ = U.ravel(), V.ravel()
    data_ = data.ravel()
#    print V_.shape
#    print  data_[attention], U_[attention],
    xyz, uv = depth2xyzuv(data_[attention], u=U_[attention], v=V_[attention])

    if display:
#            plt.gray()
        fig = plt.figure(1)
        ax = fig.add_subplot(111, projection='3d' , animated=True)#
        
#        if image_depth:
#            image_depth.set_data(attention)
#        else:
        sc = ax.plot(-xyz[:,2], -xyz[:,0], -xyz[:,1], 'r.')
#        plt.axis('off')
#        cbar = fig.colorbar(sc,shrink=0.9,extend='both')
        ax.set_xlabel('X')
        ax.set_xlim3d(0, 3.2)
        ax.set_ylabel('Y')
        ax.set_ylim3d(-2, 2)
        ax.set_zlabel('Z')
        ax.set_zlim3d(-1, 1)
        plt.draw()

        if not(record == None):
            figname = '_frame%03d.png' % i_frame
            print figname
            fig.savefig(figname, dpi = 72)
            record_list.append(figname)
        plt.close()
    i_frame += 1
    
    
    
def handler(signum, frame):
    global keep_running
    keep_running = False

def body(*args):
    if not keep_running:
        raise freenect.Kill    
    
def main():
    global depth_hist, record_list, record
    print('Press Ctrl-C in terminal to stop')
    signal.signal(signal.SIGINT, handler)
    freenect.runloop(depth=display_depth,
                     body=body)
    
    if record:
        os.system('ffmpeg -v 0 -y  -f image2  -sameq -i _frame%03d.png  ' + record + ' 2>/dev/null')
        for fname in record_list: os.remove(fname)

if __name__ == "__main__":
    main()

