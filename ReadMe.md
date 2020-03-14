
# Introduduction

Fairseq for Visual Machine Translation

### What's New:

Mar 14, 2020:  
- pretrain embeddings  
Finished pretrain code and renamed folder (pretrain folder)  
Load pretrain embeddings (image_dataset.py line 702)  
- write image training samples  
Write sample images when args.image_verbose is enabled (train.py line 160)  
- train time cache generation  
Added train time cache generation (image_dataset.py line 734)  
New flag for preload cache (visualmt.py 283 --image-preload-cache)  
- Add embedding concat 
Visual line and token concat (visual_transformer.py line 578)  

### Features:
- Pretrain


### Scripts:
- pretrain 
train zh - pretrain/scripts/sentence/vismt/train_zh.sh  
extract zh -  pretrain/scripts/sentence/vismt/train_zh.sh 
- train vismt 
concat with pretrain embedding - grid_scripts/dave_scripts/train_pretrain_concat.sh
visonly with pretrain embedding - grid_scripts/dave_scripts/train_pretrain_visonly.sh

### To do:

- Auxillary loss (CTC)  
Add auxillary CTC loss for visual embeddings  
