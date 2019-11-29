#===================
#### self defined dataset
import os.path as osp
import numpy as np
import json
from detectron2.structures import BoxMode
bfolder = 'anno'
def get_dicts(dicts, trn_ind):
    # imgdir = osp.join('..','data')
    return_dicts = list()
    mapping = dict(filename='file_name',height='height',width='width',annotations='annotations')
    # global dicts
    tmp_dicts = (dicts[i] for i in trn_ind)
    for idx, d in enumerate(tmp_dicts):
        tmp = {mapping[k]:v for k,v in d.items()}
        tmp['image_id'] = idx
        tmp['annotations'] = [dict(bbox=bbox,
                                       bbox_mode=BoxMode.XYXY_ABS,
#                                        segmentation=list(),
                                       category_id=0,is_crowd=0) for bbox in tmp['annotations']]
        return_dicts.append(tmp)
    return return_dicts

def gen_json(dicts, split):
    folder = r'external'
    with open(osp.join(folder, 'instances_val2014.json')) as f:
        x = json.load(f)
    paste = dict()
    for k in ['info','licenses']:
        paste[k] = x[k]
    paste['categories'] = [dict(supercategory='particle', id=0, name='particle')]
    images = list()
    annos = list()
    anno_cnt = 0
    for d in dicts:
        filename,height,width,anno,idx = [d[k] for k in ['file_name','height','width','annotations','image_id']]
        imgdict = dict(file_name=filename, height=height, width=width, id=idx)
        images.append(imgdict)
        for bboxdict in anno:
            bbox,catid,iscrowd = [bboxdict[k] for k in ['bbox','category_id','is_crowd']]
            x,y,xx,yy = bbox
            area = abs(xx-x)*abs(yy-y)
            annodict = dict(segmentation=None, area=area, iscrowd=iscrowd, image_id=idx,category_id=catid, bbox=bbox,
                            id=anno_cnt)
            annos.append(annodict)
            anno_cnt += 1
    paste['images'] = images
    paste['annotations'] = annos

    savepath = osp.join(bfolder, f'{split}_coco_anno.json')
    with open(savepath, 'w') as f:
        json.dump(paste, f)

    print(f'saved to {savepath}.')

def get_particle_dicts(trn_ind):
    dump_jname = 'patches.json'  # all data anno3.json
    spath = osp.join(bfolder, dump_jname)
    with open(spath) as f:
        dicts = json.load(f)
    # trn_ind = np.load(osp.join('prepro', 'train_ind.npy'))
    ret_dicts = get_dicts(dicts, trn_ind)
    return ret_dicts
