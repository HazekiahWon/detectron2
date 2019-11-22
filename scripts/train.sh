output_dir="./outputs"


## LR_SCHEDULER_NAME "WarmupMultiStepLR"， "WarmupPolyLR"

export CUDA_VISIBLE_DEVICES=0,1,2,3
python tools/train_ref.py --num-gpus 4 --config-file configs/COCO-Detection/faster_rcnn_R_50_C4_3x.yaml \
       OUTPUT_DIR "$output_dir"\
       SOLVER.OPTIMIZER 'Adam' \
       SOLVER.IMS_PER_BATCH 16 \
       SOLVER.BASE_LR 0.0005 \
#       SOLVER.FIX_BACKBONE "True" \
#       SOLVER.FIX_BACKBONE_BN "True" \
#       SOLVER.BACKBONE_LR_FACTOR 1.0 \
#       SOLVER.LR_SCHEDULER_NAME "WarmupPolyLR" \
       SOLVER.MAX_ITER 300 \
#       MODEL.REF.PHRASE_SELECT_TYPE 'Sum' \
       MODEL.WEIGHTS "../model_weights/COCO-Detection/faster_rcnn_R_50_C4_3x/model_final_f97cb7.pkl" \
       DATALOADER.NUM_WORKERS 8 \
#       DATALOADER.ASPECT_RATIO_GROUPING "False" \
#       TEST.EVAL_PERIOD 4000
