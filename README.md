# visrep

This repository is an extension of [fairseq](https://github.com/pytorch/fairseq) to enable training with visual text representations. 

For further information, please see:
- [Salesky et al. (2021): Robust Open-Vocabulary Translation from Visual Text Representations.](https://arxiv.org/abs/2104.08211)  
  In *Proceedings of EMNLP 2021*.

## Overview 

Our approach replaces the source embedding matrix with visual text representations, computed from rendered text with (optional) convolutions. 
This creates a 'continuous' vocabulary, in place of the fixed-size embedding matrix, which takes into account visual similarity, which together improve model robustness. 
There is no preprocessing before rendering text: on the source side, we directly render raw text, which we slice into overlapping, fixed-width image tokens. 

![Model diagram showing rendered text input at the sentence-level, which is sliced into overlapping, fixed-width image tokens, from which source representations for translation are computed via a convolutional block, before being passed to a traditional encoder-decoder model for translation.](https://user-images.githubusercontent.com/4117932/133522748-9fd1858d-c40f-4018-8bd7-b9e9c5f4e302.png)

Given typical parallel text, the data loader renders a complete source sentence and then creates strided slices according to the values of `--image-window` (width) and `--image-stride` (stride). 
Image height is determined automatically from the font size (`--font-size`), and slices are created using the full image height. 
This creates a set of image 'tokens' for each sentence, one per slice, with size 'window width' x 'image height.'

Because the image tokens are generated completely in the data loader, to train and evaluate typical fairseq code remains largely unchanged. 
Our VisualTextTransformer (enabled with `--task visual_text`) produces the source representations for training from the rendered text (one per image token). 
After that, everything proceeds as per normal fairseq.


## Installation

The installation is the same as [fairseq](https://github.com/pytorch/fairseq), plus additional requirements specific to visual text.

**Requirements:**
* [PyTorch](http://pytorch.org/) version >= 1.5.0
* Python version >= 3.6
* For training new models, you'll also need an NVIDIA GPU and [NCCL](https://github.com/NVIDIA/nccl)

**To install and develop locally:**
``` bash
git clone https://github.com/esalesky/visrep
cd visrep
pip install --editable ./
pip install -r examples/visual_text/requirements.txt
```

## Training 

The code is implemented via the following files:

* grid_scripts/train.sh
* grid_scripts/train_wrapper.sh

  These two scripts are used to run jobs. You basicall have to pass in
  a few arguments:

  --task visual_text --arch visual_text_transformer \
  --image-window --image stride
  --image-font-path

  There are some other parameters leftover that I am not sure whether they
  are used.

  You can have samples written to the MODELDIR/samples/ subdirectory
  using --image-samples-path (directory to write to) and
  --image-samples-interval N (write every Nth image)

* fairseq/tasks/visual_text.py

  The visual text task. Does data loading,
  instantiates the model for training, and creates the data for inference.

* fairseq/data/visual_text_dataset.py
* fairseq/data/image_generator.py

  Loads the raw data, and generates images from text. This should be extended
  to permit preprocessing of images, and to do word-level ("aligned") image
  generation.

* fairseq/models/visual/visual_transformer.py
  (Note: fairseq/models/visual_transformer.py is UNUSED)

  Creates the VisualTextTransformerModel. This has a
  VisualTextTransformerEncoder and a normal decoder. The only thing different
  the encoder does is call self.cnn_embedder, which is an instance of
  AlignOcrEncoder

* fairseq/modules/vis_align_ocr.py

  The aligned encoder, which takes a (batch x slices x width x height)
  object and generates (batch x slices x embed_size) encodings using the
  OCR code. The kernel used is a 3x3 kernel with a stride of 1.

## Inducing noise

We induced five types of noise, as below:
- **swap**: swaps two adjacent characters per token. applies to words of length >=2 *(Arabic, French, German, Korean, Russian)*
- **cmabrigde**: permutes word-internal characters with first and last character unchanged. applies to words of length >=4 *(Arabic, French, German, Korean, Russian)*
- **diacritization**: diacritization, applied via [camel-tools](https://github.com/CAMeL-Lab/camel_tools) *(Arabic)*
- **unicode**: substitutes visually similar Latin characters for Cyrillic characters *(Russian)*
- **l33tspeak**: substitutes numbers or other visually similar characters for Latin characters *(French, German)*

The scripts to induce noise are in [scripts/visual_text](https://github.com/esalesky/visrep/tree/main/scripts/visual_text), where -p is the probability of inducing noise per-token, and can be run as below. In our paper we use p from 0.1 to 1.0, in intervals of 0.1.

```
cat test.de-en.de | python3 scripts/visual_text/swap.py -p 0.1 > visual/test-sets/swap_10.de-en.de
cat test.ko-en.ko | python3 scripts/visual_text/cmabrigde.py -p 0.1 > visual/test-sets/cam_10.ko-en.ko
cat test.ar-en.ar | python3 scripts/visual_text/diacritization.py -p 0.1 > visual/test-sets/dia_10.ar-en.ar
cat test.ru-en.ru | python3 scripts/visual_text/cyrillic_noise.py -p 0.1 > visual/test-sets/cyr_10.ru-en.ru
cat test.fr-en.fr | python3 scripts/visual_text/l33t.py -p 0.1 > visual/test-sets/l33t_10.fr-en.fr
```

## License

fairseq(-py) is MIT-licensed.

## Citation

Please cite as:

``` bibtex
@inproceedings{salesky-etal-2021-robust,
    title = "Robust Open-Vocabulary Translation from Visual Text Representations",
    author = "Salesky, Elizabeth  and
      Etter, David  and
      Post, Matt",
    booktitle = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
    month = nov,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/2104.08211",
}

@inproceedings{ott2019fairseq,
  title = {fairseq: A Fast, Extensible Toolkit for Sequence Modeling},
  author = {Myle Ott and Sergey Edunov and Alexei Baevski and Angela Fan and Sam Gross and Nathan Ng and David Grangier and Michael Auli},
  booktitle = {Proceedings of NAACL-HLT 2019: Demonstrations},
  year = {2019},
}
```
