import pandas as pd
import os
import os.path as osp
# from detectron2.structures import BoxMode

spath = osp.join('anno','particles.csv')
tpath = osp.join('anno', 'patches.csv')
usecols = ['_rlnCoordinateX', '_rlnCoordinateY', '_rlnMicrographName']
rstride, cstride = 371 * 4, 101 * 19# 7420,7676
max_nr,max_nc = 7420 // rstride, 7676 // cstride
radius = 200
def get_part_id(filename):
    parts = filename.split(os.path.sep)[-1].split('_')[:-1]
    particle_id = '_'.join(parts)+'.png'
    return particle_id
# how i generate the patches
# mode==0, evenly divide
# mode==1, col+radius
# mode==2, row+radius
def process_row(item, mode=0):
    x, y, path = item # center

    grid_c = x // cstride
    grid_r = y // rstride

    outs = list()
    ans = list()
    imgno = grid_r*max_nc + grid_c
    bl,bu,br,bd = grid_c*cstride, grid_r*rstride, (grid_c+1)*cstride, (grid_r+1)*rstride
    realname = path.split('.')[0]+f'_{str(int(imgno+mode*max_nr*max_nc))}.png'
    left,right = max(x-radius,bl),min(x+radius,br)
    up,down = max(y-radius,bu),min(y+radius,bd)
    ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
    outs.append((realname, left, up, right, down, ofl, ofu, ofr, ofd))

    dy,dx = y%rstride, x%cstride
    # grid_r +radius
    if dy>radius+0.5*radius:
        imgno = grid_r * max_nc + grid_c + 2*max_nc*max_nr

        bl, bu, br, bd = grid_c * cstride, grid_r * rstride+radius, (grid_c + 1) * cstride, (grid_r + 1) * rstride+radius
        realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
        left,right = max(x-radius,bl),min(x+radius,br)
        up,down = max(y-radius,bu),min(y+radius,bd)
        ofl,ofu,ofr,ofd = left-bl,up-bu, right-bl,down-bu
        outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))
    elif dy<=0.5*radius: # grid_r-1 +radius
        imgno = (grid_r-1) * max_nc + grid_c + 2*max_nc*max_nr

        bl, bu, br, bd = grid_c * cstride, (grid_r-1) * rstride+radius, (grid_c + 1) * cstride, (grid_r) * rstride+radius
        realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
        left,right = max(x-radius,bl),min(x+radius,br)
        up,down = max(y-radius,bu),min(y+radius,bd)
        ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
        outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))

    if dx>radius+0.5*radius:# the left margin is at least 100
        imgno = grid_r * max_nc + grid_c + 1*max_nc*max_nr

        bl, bu, br, bd = grid_c * cstride+radius, grid_r * rstride, (grid_c + 1) * cstride+radius, (grid_r + 1) * rstride
        realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
        left,right = max(x-radius,bl),min(x+radius,br)
        up,down = max(y-radius,bu),min(y+radius,bd)
        ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
        outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))
    elif dx<=0.5*radius: # grid_c-1 +radius, the right margin is at least 100
        imgno = grid_r * max_nc + grid_c -1 + 1*max_nc*max_nr

        bl, bu, br, bd = (grid_c-1) * cstride+radius, grid_r * rstride, (grid_c) * cstride+radius, (grid_r + 1) * rstride
        realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
        left,right = max(x-radius,bl),min(x+radius,br)
        up,down = max(y-radius,bu),min(y+radius,bd)
        ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
        outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))

    return pd.DataFrame(outs)

# df = pd.read_csv(spath,usecols=usecols)
# # df.columns = ['x','y','path']
# df = df.values
# # ndf = list()
# pd.DataFrame([['realname','left','up','right','down','ofl','ofu','ofr','ofd']]).to_csv(tpath, mode='w', index=False, header=False)
# for item in df:
#     print(item[-1])
#     ndf = process_row(item)
#     ndf.to_csv(tpath, mode='a', index=False, header=False)

df = pd.read_csv(tpath)
dicts = list()
allowed = os.listdir('odata_png')
cnt1 = 0
cnt2 = 0
for k,g in df.groupby('realname'):
    filename = osp.join(os.path.abspath('.'), k).replace('micrographs', 'data')
    cnt1 += 1
    if not get_part_id(filename) in allowed: continue
    cnt2 += 1
    h,w = rstride, cstride
    g = g[['ofl','ofu','ofr','ofd']].values.tolist()
    dicts.append(dict(filename=filename, height=h,width=w, annotations=g))

print(f'{cnt2}/{cnt1} patches are kept.')

import json
with open(osp.join('anno','patches.json'), 'w') as f:
    json.dump(dicts, f)

