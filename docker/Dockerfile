FROM nvcr.io/nvidia/pytorch:21.12-py3

RUN apt-get update && apt-get install -yq python-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python-numpy subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev libfreetype6-dev


COPY . visrep

WORKDIR visrep

RUN pip install --editable ./ && \
    pip install -r examples/visual_text/requirements.txt

# bug on nvcr
RUN pip install opencv-python==4.6.0.66 && \
    pip install opencv-python==4.5.5.64

RUN pip install sentencepiece


RUN wget https://zenodo.org/record/5770933/files/de-en.zip && \
	unzip de-en.zip

#RUN pip install zenodo-get
#RUN zenodo_get https://zenodo.org/record/5770933#.Y-gs6RxBxkg
#RUN unzip WMT_de-en.zip

RUN python setup.py build_ext --inplace
