
import os
import struct

import numpy as np
import torch

from fairseq.tokenizer import Tokenizer, tokenize_line
from fairseq.data.image_generator import ImageGenerator
import pdb


def read_longs(f, n):
    a = np.empty(n, dtype=np.int64)
    f.readinto(a)
    return a


def write_longs(f, a):
    f.write(np.array(a, dtype=np.int64))


dtypes = {
    1: np.uint8,
    2: np.int8,
    3: np.int16,
    4: np.int32,
    5: np.int64,
    6: np.float,
    7: np.double,
}


def code(dtype):
    for k in dtypes.keys():
        if dtypes[k] == dtype:
            return k


def index_file_path(prefix_path):
    return prefix_path + '.idx'


def data_file_path(prefix_path):
    return prefix_path + '.bin'


class IndexedImageWordDataset(torch.utils.data.Dataset):

    def __init__(self, path, dictionary, image_verbose=False,
                 image_font_path=None, image_font_size=16,
                 image_width=150, image_height=30,
                 word_encoder=True, append_eos=True, reverse_order=False):
        print('...loading IndexedImageWordDataset')
        self.tokens_list = []
        self.word_list = []
        self.lines = []
        self.sizes = []
        self.append_eos = append_eos
        self.reverse_order = reverse_order
        self.read_data(path, dictionary)
        self.size = len(self.tokens_list)
        self.word_encoder = word_encoder
        self.image_verbose = image_verbose
        self.image_generator = ImageGenerator(image_font_path, image_font_size,
                                              image_width, image_height)

    def read_data(self, path, dictionary):
        print('IndexedImageWordDataset loading data %s' % (path))
        drop_cnt = 0
        with open(path, 'r', encoding='utf-8') as f:
            for line_ctr, line in enumerate(f):
                self.lines.append(line.strip('\n'))

                words = tokenize_line(line)
                if line_ctr % 10000 == 0:
                    print(line_ctr, len(words), line.strip('\n'))

                self.word_list.append(words)

#                 tokens = Tokenizer.tokenize(
#                     line, dictionary, add_if_not_exist=False,
#                     append_eos=self.append_eos, reverse_order=self.reverse_order,
#                 ).long()
                tokens = dictionary.encode_line(
                    line, add_if_not_exist=False,
                    append_eos=self.append_eos, reverse_order=self.reverse_order,
                ).long()

                self.tokens_list.append(tokens)
                self.sizes.append(len(tokens))

        self.sizes = np.array(self.sizes)
        print('...data load complete, total lines %d, dropped %d' % (len(self.lines), drop_cnt))

    def check_index(self, i):
        if i < 0 or i >= self.size:
            raise IndexError('index out of range')

    def __getitem__(self, i):
        self.check_index(i)

        img_data_list = []
        for word in self.word_list[i]:
            img_data, img_data_width = self.image_generator.get_default_image(word)
            img_data_list.append(img_data)

        return self.tokens_list[i], img_data_list
        
    def get_original_text(self, i):
        self.check_index(i)
        return self.lines[i]

    def __del__(self):
        pass

    def __len__(self):
        return self.size

    @staticmethod
    def exists(path):
        return os.path.exists(path)


class IndexedImageDataset(torch.utils.data.Dataset):
    """Loader for TorchNet IndexedDataset"""

    def __init__(self, path, dictionary, image_verbose=False,
                 image_font_path=None, image_font_size=16,
                 image_width=150, image_height=30,
                 word_encoder=True, append_eos=True, reverse_order=False):
        super().__init__()
        print('init IndexedImageDataset')
        # self.fix_lua_indexing = fix_lua_indexing
        self.read_index(path)
        self.data_file = None

        self.path = path
        self.dictionary = dictionary
        print('dict len', self.dictionary.__len__())
        self.image_verbose = image_verbose
        self.image_generator = ImageGenerator(image_font_path, image_font_size,
                                              image_width, image_height)
        self.word_encoder = word_encoder
        self.append_eos = append_eos
        self.reverse_order = reverse_order

    def read_index(self, path):
        with open(index_file_path(path), 'rb') as f:
            magic = f.read(8)
            assert magic == b'TNTIDX\x00\x00'
            version = f.read(8)
            assert struct.unpack('<Q', version) == (1,)
            code, self.element_size = struct.unpack('<QQ', f.read(16))
            self.dtype = dtypes[code]
            self.size, self.s = struct.unpack('<QQ', f.read(16))
            print('read index self size', self.size)
            self.dim_offsets = read_longs(f, self.size + 1)
            self.data_offsets = read_longs(f, self.size + 1)
            self.sizes = read_longs(f, self.s)

    def read_data(self, path):
        self.data_file = open(data_file_path(path), 'rb', buffering=0)

    def check_index(self, i):
        if i < 0 or i >= self.size:
            raise IndexError('index out of range')

    def __del__(self):
        if self.data_file:
            self.data_file.close()

    def __getitem__(self, i):
        if not self.data_file:
            self.read_data(self.path)
        self.check_index(i)
        tensor_size = int(self.sizes[self.dim_offsets[i]:self.dim_offsets[i + 1]])
        a = np.empty(tensor_size, dtype=self.dtype)
        self.data_file.seek(self.data_offsets[i] * self.element_size)
        self.data_file.readinto(a)
        item = torch.from_numpy(a).long()

        img_data_list = []
        token_list = [len(a)]
        for idx, id in enumerate(a):
            img_data, img_data_width = self.image_generator.get_default_image(self.dictionary[id])
            img_data_list.append(img_data)

        return item, img_data_list

    def __len__(self):
        return self.size

    @staticmethod
    def exists(path):
        return (
            os.path.exists(index_file_path(path)) and
            os.path.exists(data_file_path(path))
        )

    @property
    def supports_prefetch(self):
        return False  # avoid prefetching to save memory


class IndexedImageCachedDataset(IndexedImageDataset):

    def __init__(self, path, dictionary, image_verbose=False,
                 image_font_path=None, image_font_size=16,
                 image_width=150, image_height=30,
                 word_encoder=True, append_eos=True, reverse_order=False):

        super().__init__(path, dictionary, image_verbose,
                 image_font_path, image_font_size,
                 image_width, image_height,
                 word_encoder, append_eos, reverse_order)

        print('init IndexedImageCachedDataset')
        self.cache = None
        self.cache_index = {}

    @property
    def supports_prefetch(self):
        return True

    def prefetch(self, indices):
        if all(i in self.cache_index for i in indices):
            return
        if not self.data_file:
            self.read_data(self.path)
        indices = sorted(set(indices))
        total_size = 0
        for i in indices:
            total_size += self.data_offsets[i + 1] - self.data_offsets[i]
        self.cache = np.empty(total_size, dtype=self.dtype)
        ptx = 0
        self.cache_index.clear()
        for i in indices:
            self.cache_index[i] = ptx
            size = self.data_offsets[i + 1] - self.data_offsets[i]
            a = self.cache[ptx : ptx + size]
            self.data_file.seek(self.data_offsets[i] * self.element_size)
            self.data_file.readinto(a)
            ptx += size

    def __getitem__(self, i):
        # print('getitme', i)
        self.check_index(i)
        tensor_size = self.sizes[self.dim_offsets[i]:self.dim_offsets[i + 1]]
        a = np.empty(tensor_size, dtype=self.dtype)
        ptx = self.cache_index[i]
        np.copyto(a, self.cache[ptx: ptx + a.size].reshape(a.shape))
        item = torch.from_numpy(a).long()

        img_data_list = []
        token_list = [len(a)]
        for idx, id in enumerate(a):
            img_data, img_data_width = self.image_generator.get_default_image(self.dictionary[id])
            img_data_list.append(img_data)

        return item, img_data_list


class IndexedImageLineDataset(torch.utils.data.Dataset):
    """Takes a text file as input and binarizes it in memory at instantiation.
    Original lines are also kept in memory"""

    def __init__(self, path, dictionary, font_file_path, font_size=16,
                 word_encoder=True, append_eos=True, reverse_order=False):
        self.tokens_list = []
        self.word_list = []
        self.lines = []
        self.sizes = []
        self.append_eos = append_eos
        self.reverse_order = reverse_order
        self.read_data(path, dictionary)
        self.size = len(self.tokens_list)
        self.word_encoder = word_encoder
        self.image_generator = ImageGenerator(font_file_path, font_size)

    def read_data(self, path, dictionary):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                self.lines.append(line.strip('\n'))
 
                words = tokenize_line(line)
                self.word_list.append(words)

                tokens = Tokenizer.tokenize(
                    line, dictionary, add_if_not_exist=False,
                    append_eos=self.append_eos, reverse_order=self.reverse_order,
                ).long()
 
                self.tokens_list.append(tokens)
                self.sizes.append(len(tokens))
        self.sizes = np.array(self.sizes)

    def check_index(self, i):
        if i < 0 or i >= self.size:
            raise IndexError('index out of range')

    def __getitem__(self, i):
        self.check_index(i)

        img_data, img_data_width = self.image_generator.get_default_image(
            self.lines[i])

        return self.tokens_list[i], self.lines[i], img_data, img_data_width

    def get_original_text(self, i):
        self.check_index(i)
        return self.lines[i]

    def __del__(self):
        pass

    def __len__(self):
        return self.size

    @staticmethod
    def exists(path):
        return os.path.exists(path)

