#===================
#### self defined dataset
import os.path as osp
import numpy as np
import json
from detectron2.structures import BoxMode
dump_jname = 'patches.json'  # all data anno3.json
spath = osp.join('anno', dump_jname)
with open(spath) as f:
    dicts = json.load(f)
all_ind = np.arange(len(dicts))
test_ind = np.random.choice(all_ind, size=int(.1 * len(all_ind)), replace=False)
trn_ind = np.array(list(set(all_ind) - set(test_ind)))
np.save(osp.join('anno', 'train_ind.npy'), trn_ind)
np.save(osp.join('anno', 'test_ind.npy'), test_ind)

if __name__ == '__main__':

    from detectron2.data.datasets.particle import get_dicts, gen_json
    splits = dict(train=trn_ind, test=test_ind)
    for split, ind in splits.items():
        ret_dicts = get_dicts(dicts, ind) # this is for generating coco-json used for validation
        gen_json(ret_dicts, split)