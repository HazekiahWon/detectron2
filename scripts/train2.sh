output_dir="./outputs"


## LR_SCHEDULER_NAME "WarmupMultiStepLR"， "WarmupPolyLR"

export CUDA_VISIBLE_DEVICES=0,1,2,3
python tools/train_net2.py --num-gpus 4 --config-file configs/PART-Detection/particle-faster-rcnn-c4.yaml \
       OUTPUT_DIR "$output_dir" \
       SOLVER.OPTIMIZER 'Adam' \
       SOLVER.IMS_PER_BATCH 8 \
       SOLVER.BASE_LR 0.0005 \
       SOLVER.MAX_ITER 300 \
       DATALOADER.NUM_WORKERS 8 \
       TEST.EVAL_PERIOD 10
