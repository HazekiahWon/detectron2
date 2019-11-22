import json
# import pandas as pd
import os
import os.path as osp
from detectron2.structures import BoxMode
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.config import get_cfg
from detectron2.engine import DefaultTrainer
import time
def get_dicts():
    imgdir = osp.join('..','data')
    return_dicts = list()
    mapping = dict(filename='file_name',height='height',width='width',annotations='annotations')
    global dicts
    for d in dicts:
        tmp = {mapping[k]:v for k,v in d.items()}
        tmp['annotations'] = [dict(bbox=bbox,
                                       bbox_mode=BoxMode.XYXY_ABS,
#                                        segmentation=list(),
                                       category_id=0,is_crowd=0) for bbox in tmp['annotations']]
        return_dicts.append(tmp)
    return return_dicts
# load data: particles
dump_jname = 'anno4.json' # all data anno3.json
spath = osp.join('prepro',dump_jname)
with open(spath) as f:
    dicts = json.load(f)
print('number of samples: ', len(dicts))
# register dataset with the converter get_dicts()
DatasetCatalog.register('particle', get_dicts) # register a dataset
MetadataCatalog.get('particle').set(thing_classes=['positive']) # register the categories for the dataset
particle_meta = MetadataCatalog.get('particle')
curtime = time.strftime(r'%y%m%d_%H%M%S', time.localtime())
os.environ['CUDA_VISIBLE_DEVICES'] = "2"
# configs/COCO-Detection/faster_rcnn_R_50_C4_3x.yaml
cfg = get_cfg()
cfg.merge_from_file(osp.join('configs/COCO-Detection/faster_rcnn_R_50_C4_3x.yaml'))
cfg.DATASETS.TRAIN = ('particle',)
cfg.DATASETS.TEST = ()
cfg.OUTPUT_DIR = osp.join(cfg.OUTPUT_DIR, curtime)
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

cfg.DATALOADER.NUM_WORKERS = 1
cfg.MODEL.WEIGHTS = "model_weights/COCO-Detection/faster_rcnn_R_50_C4_3x/model_final_f97cb7.pkl"  # initialize from model zoo
cfg.SOLVER.IMS_PER_BATCH = 2
cfg.SOLVER.BASE_LR = 0.00025
cfg.SOLVER.MAX_ITER = 300    # 300 iterations seems good enough, but you can certainly train longer
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # faster, and good enough for this toy dataset
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  # only has one class (ballon)



trainer = DefaultTrainer(cfg)
trainer.resume_or_load(resume=False)
trainer.train()