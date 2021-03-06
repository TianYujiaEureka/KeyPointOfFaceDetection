# -*- coding:utf-8 -*-
# Author: xzq
# Date: 2019-12-04 15:49

import torch
from torchvision import transforms
import numpy as np
from torch.utils.data import Dataset
from PIL import Image
import cv2
import random

train_boarder = 112


def channel_norm(img):
    """
    将图像进行通道归一化
    :param img: ndarray, float32
    :return:
    """
    mean = np.mean(img)
    std = np.std(img)
    pixels = (img - mean) / (std + 0.0000001)
    return pixels


def parse_line(line):
    """
    解析从txt文件中读取的每一行
    :param line:
    :return:
    """
    line_parts = line.strip().split()
    img_name = line_parts[0]
    rect = list(map(int, list(map(float, line_parts[1:5]))))
    landmarks = list(map(float, line_parts[5:len(line_parts)]))
    return img_name, rect, landmarks


class Normalize(object):
    """
    重新缩放尺寸并进行通道归一化(image - mean) / std_variation
    """
    def __call__(self, sample):
        image, landmarks = sample['image'], sample['landmarks']
        image_resize = np.asarray(image.resize((train_boarder, train_boarder), Image.BILINEAR), dtype=np.float32)
        image = channel_norm(image_resize)
        return {'image': image, 'landmarks': landmarks}


class ToTensor(object):
    """
    将ndarrays转换为张量Tensor
    张量通道序列: N x C x H x W
    """
    def __call__(self, sample):
        image, landmarks = sample['image'], sample['landmarks']
        image = np.expand_dims(image, axis=2)
        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        image = image.transpose((2, 0, 1))
        # image = np.expand_dims(image, axis=0)
        return {'image': torch.from_numpy(image), 'landmarks': torch.from_numpy(landmarks)}


class FaceLandmarksDataset(Dataset):
    """
    自定义数据集
    """
    def __init__(self, src_lines, phase, transform=None):
        """
        :param src_lines: src_lines
        :param phase: whether we are training or not
        :param transform: data transform
        """
        self.lines = src_lines
        self.phase = phase
        self.transform = transform

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, idx):
        img_name, rect, landmarks = parse_line(self.lines[idx])
        # image
        img = Image.open(img_name).convert('L')
        img_crop = img.crop(tuple(rect))
        landmarks = np.array(landmarks).astype(np.float32)

        # you should let your landmarks fit to the train_boarder(112)
        # please complete your code under this blank
        # your code:
        origin_width = rect[2] - rect[0]
        origin_height = rect[3] - rect[1]
        w_ratios = train_boarder / origin_width
        h_ratios = train_boarder / origin_height
        for k in range(0, len(landmarks), 2):
            landmarks[k] = round(landmarks[k] * w_ratios)
            landmarks[k + 1] = round(landmarks[k + 1] * h_ratios)

        sample = {'image': img_crop, 'landmarks': landmarks}
        sample = self.transform(sample)
        return sample


def load_data(phase):
    data_file = phase + '.txt'
    with open(data_file) as f:
        lines = f.readlines()
    if phase == 'Train' or phase == 'train':
        tsfm = transforms.Compose([
            Normalize(),                # do channel normalization
            ToTensor()]                 # convert to torch type: NxCxHxW
        )
    else:
        tsfm = transforms.Compose([
            Normalize(),
            ToTensor()
        ])
    data_set = FaceLandmarksDataset(lines, phase, transform=tsfm)
    return data_set


def get_train_test_set():
    train_set = load_data('train')
    valid_set = load_data('test')
    return train_set, valid_set


if __name__ == '__main__':
    train_sets = load_data('train')
    idx_test = random.randint(0, len(train_sets))
    sample_test = train_sets[idx_test]
    img_test = sample_test['image']
    # 将Tensor格式转换成OpenCV的图像格式
    img_test = img_test.numpy()
    # img_test = np.squeeze(img_test, axis=(1,))
    img_test = img_test.transpose((1, 2, 0))
    # 调用下面的cv2.circle时
    # 由于这里对img_test有数据操作，当传入circle函img_copy数是不连续的内存数据，
    # 而该函数输出的内存是连续的
    # 为了保证输入输出一致，这里调用copy()方法获取连续的内存数据img_copy
    img_copy = img_test.copy()
    landmarks_test = sample_test['landmarks']
    # 请画出人脸crop以及对应的landmarks
    # please complete your code under this blank
    for i in range(0, len(landmarks_test), 2):
        # 由于关键点坐标是相对于人脸矩形框的，绘制时需要调整
        center = (int(landmarks_test[i]), int(landmarks_test[i + 1]))
        cv2.circle(img_copy, center, 1, (255, 0, 0), -1)
    cv2.imshow("image", img_copy)
    cv2.waitKey(0)
