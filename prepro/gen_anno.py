import pandas as pd
import os
import os.path as osp
# from detectron2.structures import BoxMode

spath = osp.join('anno','particles.csv')
tpath = osp.join('anno', 'patches.csv')
usecols = ['_rlnCoordinateX', '_rlnCoordinateY', '_rlnMicrographName']
Y, X = 7676, 7420
ystride, xstride = 1919, 1484
max_yn, max_xn = Y // ystride, X // xstride
radius = 150
def get_part_id(filename):
    parts = filename.split(os.path.sep)[-1].split('_')[:-1]
    particle_id = '_'.join(parts)+'.png'
    return particle_id
# how i generate the patches
# mode==0, evenly divide
# mode==1, col+radius
# mode==2, row+radius
def process_row(item, mode=0):
    # note that the x,y from the star file originates from left bottom
    x, y, path = item # center
    # y = h-y # 原坐标是左下角为原点

    grid_x = x // xstride
    grid_y = y // ystride

    outs = list()
    ans = list()
    imgno = grid_y * max_xn + grid_x
    bl,bu,br,bd = grid_x * xstride, grid_y * ystride, (grid_x + 1) * xstride, (grid_y + 1) * ystride
    realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
    left,right = max(x-radius,bl),min(x+radius,br)
    up,down = max(y-radius,bu),min(y+radius,bd)
    ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
    outs.append((realname, left, up, right, down, ofl, ofu, ofr, ofd))

    dy,dx = y % ystride, x % xstride
    if dy > 2*radius:
        imgno = grid_y * max_xn + grid_x + 2 * max_xn * max_yn

        bl, bu, br, bd = grid_x * xstride, grid_y * ystride + 2*radius, (grid_x + 1) * xstride, (grid_y + 1) * ystride + 2*radius
        realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
        left,right = max(x-radius,bl),min(x+radius,br)
        up,down = max(y-radius,bu),min(y+radius,bd)
        ofl,ofu,ofr,ofd = left-bl,up-bu, right-bl,down-bu
        outs.append((realname, left, up, right, down, ofl, ofu, ofr, ofd))
    else:
        imgno = (grid_y-1) * max_xn + grid_x + 2 * max_xn * max_yn

        bl, bu, br, bd = grid_x * xstride, (grid_y-1) * ystride + 2 * radius, (grid_x + 1) * xstride, grid_y * ystride + 2 * radius

        realname = path.split('.')[0] + f'_{str(int(imgno))}.png'
        left, right = max(x - radius, bl), min(x + radius, br)
        up, down = max(y - radius, bu), min(y + radius, bd)
        ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
        outs.append((realname, left, up, right, down, ofl, ofu, ofr, ofd))

    if dx > 2*radius :
        imgno = grid_y * max_xn + grid_x + 1 * max_xn * max_yn

        bl, bu, br, bd = grid_x * xstride + 2*radius, grid_y * ystride, (grid_x + 1) * xstride + 2*radius, (grid_y + 1) * ystride
        realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
        left,right = max(x-radius,bl),min(x+radius,br)
        up,down = max(y-radius,bu),min(y+radius,bd)
        ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
        outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))
    else:
        imgno = grid_y * max_xn + grid_x -1 + 1 * max_xn * max_yn

        bl, bu, br, bd = (grid_x-1) * xstride + 2 * radius, grid_y * ystride, grid_x * xstride + 2 * radius, (grid_y + 1) * ystride
        realname = path.split('.')[0] + f'_{str(int(imgno))}.png'
        left, right = max(x - radius, bl), min(x + radius, br)
        up, down = max(y - radius, bu), min(y + radius, bd)
        ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
        outs.append((realname, left, up, right, down, ofl, ofu, ofr, ofd))

    # grid_r +radius
    # if dy>radius+0.5*radius:
    #     imgno = grid_y * max_xn + grid_x + 2 * max_xn * max_yn
    #
    #     bl, bu, br, bd = grid_x * xstride, grid_y * ystride + radius, (grid_x + 1) * xstride, (grid_y + 1) * ystride + radius
    #     realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
    #     left,right = max(x-radius,bl),min(x+radius,br)
    #     up,down = max(y-radius,bu),min(y+radius,bd)
    #     ofl,ofu,ofr,ofd = left-bl,up-bu, right-bl,down-bu
    #
    # elif dy<=0.5*radius: # grid_r-1 +radius
    #     imgno = (grid_y-1) * max_xn + grid_x + 2 * max_xn * max_yn
    #
    #     bl, bu, br, bd = grid_x * xstride, (grid_y - 1) * ystride + radius, (grid_x + 1) * xstride, (grid_y) * ystride + radius
    #     realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
    #     left,right = max(x-radius,bl),min(x+radius,br)
    #     up,down = max(y-radius,bu),min(y+radius,bd)
    #     ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
    #     outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))
    #
    # if dx>radius+0.5*radius:# the left margin is at least 100
    #     imgno = grid_y * max_xn + grid_x + 1 * max_xn * max_yn
    #
    #     bl, bu, br, bd = grid_x * xstride + radius, grid_y * ystride, (grid_x + 1) * xstride + radius, (grid_y + 1) * ystride
    #     realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
    #     left,right = max(x-radius,bl),min(x+radius,br)
    #     up,down = max(y-radius,bu),min(y+radius,bd)
    #     ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
    #     outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))
    # elif dx<=0.5*radius: # grid_c-1 +radius, the right margin is at least 100
    #     imgno = grid_y * max_xn + grid_x - 1 + 1 * max_xn * max_yn
    #
    #     bl, bu, br, bd = (grid_x-1) * xstride + radius, grid_y * ystride, (grid_x) * xstride + radius, (grid_y + 1) * ystride
    #     realname = path.split('.')[0]+f'_{str(int(imgno))}.png'
    #     left,right = max(x-radius,bl),min(x+radius,br)
    #     up,down = max(y-radius,bu),min(y+radius,bd)
    #     ofl, ofu, ofr, ofd = left - bl, up - bu, right - bl, down - bu
    #     outs.append((realname, left, up, right, down, ofl,ofu,ofr,ofd))

    return pd.DataFrame(outs)

df = pd.read_csv(spath,usecols=usecols)
# # df.columns = ['x','y','path']
df = df.values
# # ndf = list()
pd.DataFrame([['realname','left','up','right','down','ofl','ofu','ofr','ofd']]).to_csv(tpath, mode='w', index=False, header=False)
for item in df:
    print(item[-1])
    ndf = process_row(item)
    ndf.to_csv(tpath, mode='a', index=False, header=False)

df = pd.read_csv(tpath)
dicts = list()
allowed = os.listdir('odata_png')
cnt1 = 0
cnt2 = 0
for k,g in df.groupby('realname'):
    filename = osp.join(os.path.abspath('.'), k).replace('micrographs', 'data')
    cnt1 += 1
    partname = get_part_id(filename)
    if not partname in allowed:
        print(filename, partname)
        continue
    cnt2 += 1
    Y, X = ystride, xstride
    g = g[['ofl','ofu','ofr','ofd']].values.tolist()
    dicts.append(dict(filename=filename, height=Y, width=X, annotations=g))

print(f'{cnt2}/{cnt1} patches are kept.')

import json
with open(osp.join('anno','patches.json'), 'w') as f:
    json.dump(dicts, f)

