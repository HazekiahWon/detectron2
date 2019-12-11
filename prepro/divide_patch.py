import os.path as osp
import os
from PIL import Image
sfolder = osp.join('odata_png')
tfolder = osp.join('data')
os.makedirs(tfolder, exist_ok=True)
X,Y = 7420, 7676 # Image read as shape 7420,7676
patch_y, patch_x = 1919, 1484#371*4,101*19# 7420,7676
max_xn, max_yn = X // patch_x, Y // patch_y
imglist = os.listdir(sfolder)
radius = 150
# Image.crop starts from the left up corner, but simply
for imname in imglist:
    newname = imname.split('.')[0]
    imgpath = osp.join(sfolder, imname)
    img = Image.open(imgpath)
    for yj in range(max_yn):
        for xi in range(max_xn):
            imgno = xi + max_xn * yj
            timgpath = osp.join(tfolder, f'{newname}_{imgno}.png')
            if os.path.exists(timgpath):
                print(f'{timgpath} already exists, skip.')
                continue
            # right, up = yj * patch_y, xi * patch_x
            # left,down = right + patch_y, up + patch_x
            x0, x1 = xi*patch_x, (xi+1)*patch_x
            y0, y1 = yj*patch_y, (yj+1)*patch_y
            bbox = x0, y0, x1, y1

            slic = img.crop(bbox)
            slic.save(timgpath)
            saved = list()
            if yj!=max_yn:
                bbox = x0+2*radius, y0, x1+2*radius, y1
                slic = img.crop(bbox)
                slic.save(osp.join(tfolder, f'{newname}_{imgno + max_xn * max_yn}.png'))
                saved.append(imgno + max_xn * max_yn)
            if xi!=max_xn:
                bbox = x0, y0+2*radius, x1, y1+2*radius
                slic = img.crop(bbox)
                slic.save(osp.join(tfolder, f'{newname}_{imgno + 2 * max_xn * max_yn}.png'))
                saved.append(imgno + 2*max_xn * max_yn)
            print(timgpath, saved)