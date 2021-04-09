#!/bin/bash

#$ -cwd -S /bin/bash -V
#$ -j y -o logs/
#$ -l gpu=1 -q gpu.q@@v100 -l h_rt=48:00:00

source /opt/anaconda3/etc/profile.d/conda.sh
conda deactivate
conda activate fairseq

trainscript=$1
modeldir=$2
shift
shift

[[ ! -d $modeldir ]] && mkdir -p $modeldir

# Now we're on a GPU
bash $trainscript $modeldir "$@" > $modeldir/log 2>&1
