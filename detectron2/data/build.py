# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import bisect
import copy
import itertools
import logging
import numpy as np
import pickle
import torch.utils.data
from fvcore.common.file_io import PathManager
from tabulate import tabulate
from termcolor import colored

from detectron2.structures import BoxMode
from detectron2.utils.comm import get_world_size
from detectron2.utils.env import seed_all_rng
from detectron2.utils.logger import log_first_n

from . import samplers
from .catalog import DatasetCatalog, MetadataCatalog
from .common import DatasetFromList, MapDataset
from .dataset_mapper import DatasetMapper
from .detection_utils import check_metadata_consistency

"""
This file contains the default logic to build a dataloader for training or testing.
"""

__all__ = [
    "build_detection_train_loader",
    "build_detection_test_loader",
    "get_detection_dataset_dicts",
    "load_proposals_into_dataset",
    "print_instances_class_histogram",
]


def filter_images_with_only_crowd_annotations(dataset_dicts):
    """
    Filter out images with none annotations or only crowd annotations
    (i.e., images without non-crowd annotations).
    A common training-time preprocessing on COCO dataset.

    Args:
        dataset_dicts (list[dict]): annotations in Detectron2 Dataset format.

    Returns:
        list[dict]: the same format, but filtered.
    """
    num_before = len(dataset_dicts)

    def valid(anns):
        for ann in anns:
            if ann.get("iscrowd", 0) == 0:
                return True
        return False

    dataset_dicts = [x for x in dataset_dicts if valid(x["annotations"])]
    num_after = len(dataset_dicts)
    logger = logging.getLogger(__name__)
    logger.info(
        "Removed {} images with no usable annotations. {} images left.".format(
            num_before - num_after, num_after
        )
    )
    return dataset_dicts


def filter_images_with_few_keypoints(dataset_dicts, min_keypoints_per_image):
    """
    Filter out images with too few number of keypoints.

    Args:
        dataset_dicts (list[dict]): annotations in Detectron2 Dataset format.

    Returns:
        list[dict]: the same format as dataset_dicts, but filtered.
    """
    num_before = len(dataset_dicts)

    def visible_keypoints_in_image(dic):
        # Each keypoints field has the format [x1, y1, v1, ...], where v is visibility
        annotations = dic["annotations"]
        return sum(
            (np.array(ann["keypoints"][2::3]) > 0).sum()
            for ann in annotations
            if "keypoints" in ann
        )

    dataset_dicts = [
        x for x in dataset_dicts if visible_keypoints_in_image(x) >= min_keypoints_per_image
    ]
    num_after = len(dataset_dicts)
    logger = logging.getLogger(__name__)
    logger.info(
        "Removed {} images with fewer than {} keypoints.".format(
            num_before - num_after, min_keypoints_per_image
        )
    )
    return dataset_dicts


def load_proposals_into_dataset(dataset_dicts, proposal_file):
    """
    Load precomputed object proposals into the dataset.

    Args:
        dataset_dicts (list[dict]): annotations in Detectron2 Dataset format.
        proposal_file (str): file path of pre-computed proposals, in pkl format.

    Returns:
        list[dict]: the same format as dataset_dicts, but added proposal field.
    """
    logger = logging.getLogger(__name__)
    logger.info("Loading proposals from: {}".format(proposal_file))

    with PathManager.open(proposal_file, "rb") as f:
        proposals = pickle.load(f, encoding="latin1")

    # Rename the key names in D1 proposal files
    rename_keys = {"indexes": "ids", "scores": "objectness_logits"}
    for key in rename_keys:
        if key in proposals:
            proposals[rename_keys[key]] = proposals.pop(key)

    # Remove proposals whose ids are not in dataset
    img_ids = set({entry["image_id"] for entry in dataset_dicts})
    keep = [i for i, id in enumerate(proposals["ids"]) if id in img_ids]
    # Sort proposals by ids following the image order in dataset
    keep = sorted(keep)
    for key in ["boxes", "ids", "objectness_logits"]:
        proposals[key] = [proposals[key][i] for i in keep]
    # Assuming default bbox_mode of precomputed proposals are 'XYXY_ABS'
    bbox_mode = BoxMode(proposals["bbox_mode"]) if "bbox_mode" in proposals else BoxMode.XYXY_ABS

    for i, record in enumerate(dataset_dicts):
        # Sanity check that these proposals are for the correct image id
        assert record["image_id"] == proposals["ids"][i]

        boxes = proposals["boxes"][i]
        objectness_logits = proposals["objectness_logits"][i]
        # Sort the proposals in descending order of the scores
        inds = objectness_logits.argsort()[::-1]
        record["proposal_boxes"] = boxes[inds]
        record["proposal_objectness_logits"] = objectness_logits[inds]
        record["proposal_bbox_mode"] = bbox_mode

    return dataset_dicts


def _quantize(x, bin_edges):
    bin_edges = copy.copy(bin_edges)
    bin_edges = sorted(bin_edges)
    quantized = list(map(lambda y: bisect.bisect_right(bin_edges, y), x))
    return quantized


def print_instances_class_histogram(dataset_dicts, class_names):
    """
    Args:
        dataset_dicts (list[dict]): list of dataset dicts.
        class_names (list[str]): list of class names (zero-indexed).
    """
    num_classes = len(class_names)
    hist_bins = np.arange(num_classes + 1)
    histogram = np.zeros((num_classes,), dtype=np.int)
    for entry in dataset_dicts:
        annos = entry["annotations"]
        classes = [x["category_id"] for x in annos if not x.get("iscrowd", 0)]
        histogram += np.histogram(classes, bins=hist_bins)[0]

    N_COLS = min(6, len(class_names) * 2)

    def short_name(x):
        # make long class names shorter. useful for lvis
        if len(x) > 13:
            return x[:11] + ".."
        return x

    data = list(
        itertools.chain(*[[short_name(class_names[i]), int(v)] for i, v in enumerate(histogram)])
    )
    total_num_instances = sum(data[1::2])
    data.extend([None] * (N_COLS - (len(data) % N_COLS)))
    if num_classes > 1:
        data.extend(["total", total_num_instances])
    data = itertools.zip_longest(*[data[i::N_COLS] for i in range(N_COLS)])
    table = tabulate(
        data,
        headers=["category", "#instances"] * (N_COLS // 2),
        tablefmt="pipe",
        numalign="left",
        stralign="center",
    )
    log_first_n(
        logging.INFO,
        "Distribution of training instances among all {} categories:\n".format(num_classes)
        + colored(table, "cyan"),
        key="message",
    )


def build_batch_data_sampler(
    sampler, images_per_batch, group_bin_edges=None, grouping_features=None
):
    """
    Return a dataset index sampler that batches dataset indices possibly with
    grouping to improve training efficiency.

    Args:
        sampler (torch.utils.data.sampler.Sampler): any subclass of
            :class:`torch.utils.data.sampler.Sampler`.
        images_per_batch (int): the batch size. Note that the sampler may return
            batches that have between 1 and images_per_batch (inclusive) elements
            because the underlying index set (and grouping partitions, if grouping
            is used) may not be divisible by images_per_batch.
        group_bin_edges (None, list[number], tuple[number]): If None, then grouping
            is disabled. If a list or tuple is given, the values are used as bin
            edges for defining len(group_bin_edges) + 1 groups. When batches are
            sampled, only elements from the same group are returned together.
        grouping_features (None, list[number], tuple[number]): If None, then grouping
            is disabled. If a list or tuple is given, it must specify for each index
            in the underlying dataset the value to be used for placing that dataset
            index into one of the grouping bins.

    Returns:
        A BatchSampler or subclass of BatchSampler.
    """
    if group_bin_edges and grouping_features:
        assert isinstance(group_bin_edges, (list, tuple))
        assert isinstance(grouping_features, (list, tuple))
        group_ids = _quantize(grouping_features, group_bin_edges)
        batch_sampler = samplers.GroupedBatchSampler(sampler, group_ids, images_per_batch)
    else:
        batch_sampler = torch.utils.data.sampler.BatchSampler(
            sampler, images_per_batch, drop_last=True
        )  # drop last so the batch always have the same size
        # NOTE when we add batch inference support, make sure not to use this.
    return batch_sampler


def get_detection_dataset_dicts(
    dataset_names, filter_empty=True, min_keypoints=0, proposal_files=None
):
    """
    Load and prepare dataset dicts for instance detection/segmentation and semantic segmentation.

    Args:
        dataset_names (list[str]): a list of dataset names
        filter_empty (bool): whether to filter out images without instance annotations
        min_keypoints (int): filter out images with fewer keypoints than
            `min_keypoints`. Set to 0 to do nothing.
        proposal_files (list[str]): if given, a list of object proposal files
            that match each dataset in `dataset_names`.
    """
    assert len(dataset_names)
    dataset_dicts = [DatasetCatalog.get(dataset_name) for dataset_name in dataset_names]

    if proposal_files is not None:
        assert len(dataset_names) == len(proposal_files)
        # load precomputed proposals from proposal files
        dataset_dicts = [
            load_proposals_into_dataset(dataset_i_dicts, proposal_file)
            for dataset_i_dicts, proposal_file in zip(dataset_dicts, proposal_files)
        ]

    dataset_dicts = list(itertools.chain.from_iterable(dataset_dicts))

    has_instances = "annotations" in dataset_dicts[0]
    # Keep images without instance-level GT if the dataset has semantic labels.
    if filter_empty and has_instances and "sem_seg_file_name" not in dataset_dicts[0]:
        dataset_dicts = filter_images_with_only_crowd_annotations(dataset_dicts)

    if min_keypoints > 0 and has_instances:
        dataset_dicts = filter_images_with_few_keypoints(dataset_dicts, min_keypoints)

    if has_instances:
        try:
            class_names = MetadataCatalog.get(dataset_names[0]).thing_classes
            check_metadata_consistency("thing_classes", dataset_names)
            print_instances_class_histogram(dataset_dicts, class_names)
        except AttributeError:  # class names are not available for this dataset
            pass
    return dataset_dicts


def build_detection_train_loader(cfg, mapper=None):
    """
    A data loader is created by the following steps:

    1. Use the dataset names in config to query :class:`DatasetCatalog`, and obtain a list of dicts.
    2. Start workers to work on the dicts. Each worker will:
      * Map each metadata dict into another format to be consumed by the model.
      * Batch them by simply putting dicts into a list.
    The batched ``list[mapped_dict]`` is what this dataloader will return.

    Args:
        cfg (CfgNode): the config
        mapper (callable): a callable which takes a sample (dict) from dataset and
            returns the format to be consumed by the model.
            By default it will be `DatasetMapper(cfg, True)`.

    Returns:
        a torch DataLoader object
    """
    num_workers = get_world_size()
    images_per_batch = cfg.SOLVER.IMS_PER_BATCH
    assert (
        images_per_batch % num_workers == 0
    ), "SOLVER.IMS_PER_BATCH ({}) must be divisible by the number of workers ({}).".format(
        images_per_batch, num_workers
    )
    assert (
        images_per_batch >= num_workers
    ), "SOLVER.IMS_PER_BATCH ({}) must be larger than the number of workers ({}).".format(
        images_per_batch, num_workers
    )
    images_per_worker = images_per_batch // num_workers

    dataset_dicts = get_detection_dataset_dicts(
        cfg.DATASETS.TRAIN,
        filter_empty=True,
        min_keypoints=cfg.MODEL.ROI_KEYPOINT_HEAD.MIN_KEYPOINTS_PER_IMAGE
        if cfg.MODEL.KEYPOINT_ON
        else 0,
        proposal_files=cfg.DATASETS.PROPOSAL_FILES_TRAIN if cfg.MODEL.LOAD_PROPOSALS else None,
    ) # list of dict(file_name, height, width, annotations), from get_dicts() defined in datasets\buitin.py
    dataset = DatasetFromList(dataset_dicts, copy=False)

    # Bin edges for batching images with similar aspect ratios. If ASPECT_RATIO_GROUPING
    # is enabled, we define two bins with an edge at height / width = 1.
    group_bin_edges = [1] if cfg.DATALOADER.ASPECT_RATIO_GROUPING else []
    aspect_ratios = [float(img["height"]) / float(img["width"]) for img in dataset]

    if mapper is None:
        mapper = DatasetMapper(cfg, True)

    dataset = MapDataset(dataset, mapper) # read in the image: list of dict(file_name, height, width, image::tensor, instances::Instances)

    sampler_name = cfg.DATALOADER.SAMPLER_TRAIN
    logger = logging.getLogger(__name__)
    logger.info("Using training sampler {}".format(sampler_name))
    if sampler_name == "TrainingSampler":
        sampler = samplers.TrainingSampler(len(dataset))
    elif sampler_name == "RepeatFactorTrainingSampler":
        sampler = samplers.RepeatFactorTrainingSampler(
            dataset_dicts, cfg.DATALOADER.REPEAT_THRESHOLD
        )
    else:
        raise ValueError("Unknown training sampler: {}".format(sampler_name))
    batch_sampler = build_batch_data_sampler(
        sampler, images_per_worker, group_bin_edges, aspect_ratios
    )

    data_loader = torch.utils.data.DataLoader(
        dataset,
        num_workers=cfg.DATALOADER.NUM_WORKERS,
        batch_sampler=batch_sampler,
        collate_fn=trivial_batch_collator,
        worker_init_fn=worker_init_reset_seed,
    )
    return data_loader


def build_detection_test_loader(cfg, dataset_name, mapper=None):
    """
    Similar to `build_detection_train_loader`.
    But this function uses the given `dataset_name` argument (instead of the names in cfg),
    and uses batch size 1.

    Args:
        cfg: a detectron2 CfgNode
        dataset_name (str): a name of the dataset that's available in the DatasetCatalog
        mapper (callable): a callable which takes a sample (dict) from dataset
           and returns the format to be consumed by the model.
           By default it will be `DatasetMapper(cfg, False)`.

    Returns:
        DataLoader: a torch DataLoader, that loads the given detection
        dataset, with test-time transformation and batching.
    """
    dataset_dicts = get_detection_dataset_dicts(
        [dataset_name],
        filter_empty=False,
        proposal_files=[
            cfg.DATASETS.PROPOSAL_FILES_TEST[list(cfg.DATASETS.TEST).index(dataset_name)]
        ]
        if cfg.MODEL.LOAD_PROPOSALS
        else None,
    )

    dataset = DatasetFromList(dataset_dicts)
    if mapper is None:
        mapper = DatasetMapper(cfg, False)
    dataset = MapDataset(dataset, mapper)

    sampler = samplers.InferenceSampler(len(dataset))
    # Always use 1 image per worker during inference since this is the
    # standard when reporting inference time in papers.
    batch_sampler = torch.utils.data.sampler.BatchSampler(sampler, 1, drop_last=False)

    data_loader = torch.utils.data.DataLoader(
        dataset,
        num_workers=cfg.DATALOADER.NUM_WORKERS,
        batch_sampler=batch_sampler,
        collate_fn=trivial_batch_collator,
    )
    return data_loader


def trivial_batch_collator(batch):
    """
    A batch collator that does nothing.
    """
    return batch


def worker_init_reset_seed(worker_id):
    seed_all_rng(np.random.randint(2 ** 31) + worker_id)
