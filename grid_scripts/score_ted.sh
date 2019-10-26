#!/bin/bash
#. /etc/profile.d/modules.sh
#
# 2019-10-16
#
# qsub -v PATH -S /bin/bash -b y -q gpu.q@@1080 -cwd -j y -N score \
#   -l num_proc=16,mem_free=32G,h_rt=48:00:00,gpu=1 \
#   /expscratch/detter/src/fairseq/fairseq_scripts/10000/score_ted.sh
#
#
#  Score translation model
#

module load cuda10.0/toolkit/10.0.130
module load cudnn/7.5.0_cuda10.0

if [ ! -z $SGE_HGR_gpu ]; then
    export CUDA_VISIBLE_DEVICES=$SGE_HGR_gpu
    sleep 3
fi

source activate /expscratch/detter/tools/py36

export LD_LIBRARY_PATH=/cm/local/apps/gcc/7.2.0/lib64:$LD_LIBRARY_PATH
echo $LD_LIBRARY_PATH
echo $PYTHONPATH
echo $CUDA_VISIBLE_DEVICES
nvidia-smi

SRC_LANG=de
TGT_LANG=en
FAIRSEQ_PATH=/expscratch/detter/src/fairseq/fairseq
DATA_DIR=/expscratch/detter/mt/multitarget-ted/$TGT_LANG-$SRC_LANG/10000/raw
CKPT_DIR=/expscratch/detter/mt/multitarget-ted/$TGT_LANG-$SRC_LANG/10000/exp/fairseq/visualtrans

echo $DATA_DIR
echo $FAIRSEQ_PATH
echo $SRC_LANG
echo $TGT_LANG
echo $CKPT_DIR

python $FAIRSEQ_PATH/generate.py \
$DATA_DIR \
--path=$CKPT_DIR/checkpoint_best.pt \
--user-dir=$FAIRSEQ_PATH \
--gen-subset=test \
--batch-size=32 \
--raw-text \
--beam=5 


#--remove-bpe




               