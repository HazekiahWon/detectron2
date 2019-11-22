import os.path as osp
import os
from PIL import Image
sfolder = osp.join('odata')
tfolder = osp.join('data')
os.makedirs(tfolder, exist_ok=True)

patch_h,patch_w = 371*4,101*19# 7420,7676
max_hn,max_wn = 7420//patch_h, 7676//patch_w
imglist = os.listdir(sfolder)
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
            right, up = cj*patch_w,ri*patch_h
            left,down = right+patch_w,up+patch_h
            bbox = right, up, left, down
            slic = img.crop(bbox)
            slic.save(timgpath)
            if cj!=max_wn:
                bbox = right+200, up, left+200, down
                slic = img.crop(bbox)
                slic.save(osp.join(tfolder, f'{newname}_{imgno+max_hn*max_wn}.png'))
            if ri!=max_hn:
                bbox = right, up+200, left, down+200
                slic = img.crop(bbox)
                slic.save(osp.join(tfolder, f'{newname}_{imgno+2*max_hn*max_wn}.png'))
            print(timgpath, imgno, imgno+max_hn*max_wn)