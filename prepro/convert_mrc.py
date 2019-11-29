import mrcfile
import os
import os.path as osp
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
mrclist = os.listdir('data')
import mrcfile
import os
import os.path as osp
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
# folder = osp.join('..', 'mrc')
# mrclist = os.listdir(folder)

def mrcread(fpath): # osp.join('data',mrclist[10])
    with mrcfile.mmap(fpath, permissive=True, mode='r') as mrc:
        return mrc.data

## preprocessing
def bin_2d(body_2d, bin_size):
    """Do the bin process to the 2D array.

    This function can make bin the image based on the bin_size.
    bin_size is a int value. if it was set to 2, then the 4 points in a small patch 2x2 of the body_2d
           are summed to one value. It likes an average pooling operation.

    Args:
        body_2d: numpy.array, it is a 2d array, the dim is 2.
        bin_size: int value.

    Returns:
        return pool_result
        pool_result: numpy.array, the shape of it is (body_2d.shape[0]/bin_size, body_2d.shape[1]/bin_size)

    """
    """
    # using the tensorflow pooling operation to do the bin preprocess
    # memory cost, out of memory
    col = body_2d.shape[0]
    row = body_2d.shape[1]
    body_2d = body_2d.reshape(1, col, row, 1)
    body_node = tf.constant(body_2d)
    body_pool = tf.nn.avg_pool(body_node, ksize=[1, bin_size, bin_size, 1], strides=[1, bin_size, bin_size, 1], padding='VALID')
    with tf.Session(config=tf.ConfigProto(log_device_placement=False)) as sess:
        pool_result = sess.run(body_pool)
        pool_result = pool_result.reshape((pool_result.shape[1], pool_result.shape[2]))
    return pool_result
    """
    # based on the numpy operation to do the bin process
    col = body_2d.shape[0]
    row = body_2d.shape[1]
    scale_col = col//bin_size
    scale_row = row//bin_size
    patch = np.copy(body_2d[0:scale_col*bin_size, 0:scale_row*bin_size])
    patch_view = patch.reshape(scale_col, bin_size, scale_row, bin_size)
    body_2d_bin = patch_view.mean(axis=3).mean(axis=1)
    return body_2d_bin
def low_pass(micrograph, sigma=0.1): return ndi.filters.gaussian_filter(micrograph, sigma)
def binning(micrograph, poolsize=3): return bin_2d(micrograph, poolsize)
def prepro(micrograph):
# lowpass
    micrograph = ndi.filters.gaussian_filter(micrograph, 0.1)
    # do the bin process
    pooling_size = 3
    micrograph = bin_2d(micrograph, pooling_size)

    # low pass the micrograph
    #micrograph_lowpass = scipy.ndimage.filters.gaussian_filter(micrograph, 0.1)
    #f = np.fft.fft2(micrograph)
    #fshift = np.fft.fftshift(f)
    #magnitude_spectrum = 20*np.log(np.abs(fshift))

    #plt.subplot(121),plt.imshow(micrograph, cmap = 'gray')
    #plt.title('Input Image'), plt.xticks([]), plt.yticks([])
    #plt.subplot(122),plt.imshow(micrograph_lowpass, cmap = 'gray')
    #plt.title('Magnitude Spectrum'), plt.xticks([]), plt.yticks([])
    #plt.show()

    # nomalize the patch
    max_value = micrograph.max()
    min_value = micrograph.min()
    particle = (micrograph - min_value)/(max_value - min_value)
    mean_value = micrograph.mean()
    std_value = micrograph.std()
    micrograph = (micrograph - mean_value)/std_value
    #
    return micrograph, pooling_size

def whiten(img2):
    img3 = (img2-img2.mean())/(img2.std())
    return img3

def rescale(x):
    x = x.astype(np.float)
    return (x-x.min())*255./(x.max()-x.min())

def stat(x):
    return x.mean(),x.max(),x.min()

def stretch_contrast(im, p1, p2, ratio):
    im = im.copy()
    mi, ma = im.min(), im.max()
    mid_len = 255. * ratio
    #     k2 = (p2-p1)/mid_len
    side_len = 255 * (1 - ratio) * .5
    #     k1 = (p1-mi)/side_len
    #     k3 = (ma-p2)/side_len
    part1, part2, part3 = im < p1, (im >= p1) & (im < p2), im >= p2
    im[part1] = side_len / (p1 - mi) * (im[part1] - mi)
    im[part2] = mid_len / (p2 - p1) * (im[part2] - p1) + side_len
    im[part3] = side_len / (ma - p2) * (im[part3] - p2) + side_len + mid_len
    return im

def correction(img, ratio=0.6, nsig=1.): # the 1sigma length ratio in [0,255] range
    # rescale first
    img2 = rescale(img)
    # compute the std
    mean,std = img2.mean(),img2.std()
    amp = nsig/2
    lo,hi = mean+amp*std,mean-amp*std
    img3 = stretch_contrast(img2, lo, hi, ratio)
    return img3

def save_im(arr, name):
    Image.fromarray(arr).convert('L').save(name)

def proc_im(imgp, sigma=1., ratio=.99, nsig=1.):
    # the full pipeline
    img = mrcread(imgp)
    # do correction
    # low pass
    img = low_pass(img, sigma) # can tune this param
    img2 = correction(img,ratio, nsig)
#     img2 = low_pass(img2, sigma)
    # img = bin_2d(img, 2)
    return img2.astype(np.uint8)

if __name__ == '__main__':
    opath = osp.join('odata_mrc')
    tpath = osp.join('odata_png')
    os.makedirs(tpath, exist_ok=True)

    for m in os.listdir(opath):
        name = m.split('.')[0]
        if os.path.exists(osp.join(tpath, f'{name}.png')):
            print(f'{m} already processed, skip.')
            continue
        mrcpath = osp.join(opath, m)
        print(f'processing {m}')
        out = proc_im(mrcpath, sigma=1.5, ratio=0.6, nsig=1)
        save_im(out, osp.join(tpath, f'{name}.png'))
    # impath = osp.join(opath, 'BGal_000433.mrc')
    # img = mrcread(impath)
    # print('done loading')
    # # method1
    # img1 = low_pass(img, 1)
    # img1 = correction(img1, .99)
    # print('done method1')
    # # method2
    # img2 = ndi.gaussian_filter(img, sigma=3)
    # print('done method2')
    # # save
    # save_im(img, osp.join(tpath, 'original.png'))
    # save_im(img1, osp.join(tpath, 'method1.png'))
    # save_im(img2, osp.join(tpath, 'method2.png'))
    # print('done saving')

