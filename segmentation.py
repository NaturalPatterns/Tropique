#!/usr/bin/env python
import freenect
import matplotlib.pyplot as mp
import signal
#import frame_convert
from calibkinect import depth2xyzuv

mp.ion()
image_depth = None
keep_running = True

import numpy as np

depth_shape=(640,480)
N_hist = 2**8 
max_depth = 3.5 # in meters
matname = 'depth_map.npy'
#try :
#    depth_hist = np.load(matname)    
#    learn = False
#except:
#    learn = True
##    depth_hist = np.zeros((depth_shape[0], depth_shape[1], N_hist))
#    depth_hist = np.zeros((depth_shape[1], depth_shape[0], 2))
depth_hist = np.zeros((depth_shape[1], depth_shape[0], 2)) + 1e-10
        
#from threading import Semaphore
#lock = Semaphore()
mean_depth = 0
i_frame = 0

def pretty_depth(depth):
    """Converts depth into a 'nicer' format for display

    This is abstracted to allow for experimentation with normalization

    Args:
        depth: A numpy array with 2 bytes per pixel

    Returns:
        A numpy array that has been processed whos datatype is unspecified
    """
    np.clip(depth, 0, 2**10 - 1, depth)
    depth >>= 2
    depth = depth.astype(np.uint8)
    return depth

#def zscore(depth, depth_hist):
#    """ Converts depth into a z-score value
#    
#    """
#    
#
#    return depth

def gaussian(x, m, var):
    return 1./np.sqrt(2.*np.pi)/np.sqrt(var)*np.exp(-.5*(x-m)**2/var)

def display_depth(dev, data, timestamp, display=True):
    """
    
    Args:
    index: Kinect device index (default: 0)
    format: Depth format (default: DEPTH_11BIT)
    
    Returns:
    (depth, timestamp) or None on error
    depth: A numpy array, shape:(640,480) dtype:np.uint16
    timestamp: int representing the time

    """
    global image_depth, i_frame, depth_hist
#    print timestamp
    if True: # learn :
        data = pretty_depth(data) # on 8-bits
#        data = data / 255. #data.max()
        xyz, uv = depth2xyzuv(data)
#        print xyz.shape, uv.shape
        data = xyz[:,2].reshape((480,640))
#        data = data * (data >0)
        print data.shape, data.min(), data.max()
#        print timestamp, i_frame, data.shape, depth_hist.shape
        
        depth_hist[:, :, 0] = (1-1./(i_frame+1))* depth_hist[:, :, 0] + 1./(i_frame+1) * data
        if i_frame>0:
            depth_hist[:, :, 1] = (1-1./(i_frame+1))* depth_hist[:, :, 1] + 1./i_frame * (data-depth_hist[:, :, 0])**2
        i_frame += 1
#        print np.log(depth_hist[:, :, 1]).min(), np.log(depth_hist[:, :, 1]).max()
#        if display:
##            data = pretty_depth(data)
#            mp.gray()
#            mp.figure(1)
#            if image_depth:
#                image_depth.set_data(depth_hist[:, :, 0])
##                image_depth.set_alpha(depth_hist[:, :, 1]/depth_hist[:, :, 1].max())
#            else:
#                image_depth = mp.imshow(depth_hist[:, :, 0], interpolation='nearest', animated=True, vmin=0, vmax=255)
#                mp.colorbar() 
#                
#            mp.draw()        
#    else:
#        data = pretty_depth(data)
#        proba = gaussian(data, depth_hist[:, :, 0], depth_hist[:, :, 1])
##        smoothed = ndimage.gaussian(np.log(proba), 5.)
#        print np.log(proba).min(), np.log(proba).max()
        score = (depth_hist[:, :, 0] - data) / (np.sqrt(depth_hist[:, :, 1]) + 1e-5) # * (depth_hist[:, :, 1] < 1e-3)
#        smoothed = ndimage.gaussian(np.log(proba), 5.)
        print score.min(), score.max()

        if display:
#            mp.gray()
            mp.figure(1)
            if image_depth:
                image_depth.set_data(data)
            else:
                image_depth = mp.imshow(data, interpolation='nearest', animated=True, vmin=-5, vmax=5)
                mp.colorbar()        
            mp.draw()
#        else:
#            global mean_depth
#            mean_depth = (1-1./(i_frame+1))* mean_depth + 1./(i_frame+1) * data.mean()
#            i_frame += 1
#            print data.min(), data.max()
#            print timestamp, mean_depth
    

def handler(signum, frame):
    global keep_running
    keep_running = False

#def display_rgb(dev, data, timestamp):
#    global keep_running
#    cv.ShowImage('RGB', frame_convert.video_cv(data))
#    if cv.WaitKey(10) == 27:
#        keep_running = False

def body(*args):
#    global image_depth

    if not keep_running:
        raise freenect.Kill    
    
def main():
    global depth_hist
    print('Press Ctrl-C in terminal to stop')
    signal.signal(signal.SIGINT, handler)
    freenect.runloop(depth=display_depth,
                     body=body)
    
#    see https://gist.github.com/717060
#    freenect.runloop(lambda *x: depth_callback(*freenect.depth_cb_np(*x)))
#    
#    def depth_callback(dev, data, timestamp):
#        
#        """libfreenect will call this func once per frame"""
#
#        global lock
#        global notes_on
#
#        lock.acquire()
#        # do some computing
#
#        lock.release()
#
#    if learn == True:
#        np.load(matname, depth_hist) 
if __name__ == "__main__":
    main()

