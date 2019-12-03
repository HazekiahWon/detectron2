import os.path as osp
import os
from PIL import Image
sfolder = osp.join('odata_png')
tfolder = osp.join('data')
os.makedirs(tfolder, exist_ok=True)
h,w = 7676,7420
patch_w,patch_h = 1484,1919#371*4,101*19# 7420,7676
max_hn,max_wn = h//patch_h, w//patch_w
imglist = os.listdir(sfolder)
radius = 200
for imname in imglist:
    newname = imname.split('.')[0]
    imgpath = osp.join(sfolder, imname)
    img = Image.open(imgpath)
    for ri in range(max_hn):
        # print(f'=========== row {ri}')
        for cj in range(max_wn):
            # print(f'========== col {cj}')
            imgno = ri*max_wn+cj
            timgpath = osp.join(tfolder, f'{newname}_{imgno}.png')
            if os.path.exists(timgpath):
                print(f'{timgpath} already exists, skip.')
                continue
            right, up = cj*patch_w,ri*patch_h
            left,down = right+patch_w,up+patch_h
            bbox = right, up, left, down
            slic = img.crop(bbox)
            slic.save(timgpath)
            if cj!=max_wn:
                bbox = right+2*radius, up, left+2*radius, down
                slic = img.crop(bbox)
                slic.save(osp.join(tfolder, f'{newname}_{imgno+max_hn*max_wn}.png'))
            if ri!=max_hn:
                bbox = right, up+2*radius, left, down+2*radius
                slic = img.crop(bbox)
                slic.save(osp.join(tfolder, f'{newname}_{imgno+2*max_hn*max_wn}.png'))
            print(timgpath, imgno, imgno+max_hn*max_wn)