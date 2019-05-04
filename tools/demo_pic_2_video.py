#!/usr/bin/env python

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# --------------------------------------------------------

"""
Demo script showing detections in sample images.

See README.md for installation instructions before running.
"""

import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2
import argparse
import time

CLASSES = ('__background__',
           'car')

NETS = {'vgg16': ('VGG16',
                  'VGG16_faster_rcnn_final.caffemodel'),
        'zf': ('ZF',
               'ZF_faster_rcnn_final.caffemodel')}


def vis_detections_video(im, class_name, dets, thresh=0.5):
    """Draw detected bounding boxes."""

    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        return im

    for i in inds:
        bbox = dets[i, :4]
        # bbox[1] += 540
        # bbox[3] += 540
        score = dets[i, -1]
        cv2.rectangle(im, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
        # cv2.rectangle(im, (int(bbox[0]), int(bbox[1]) - 10), (int(bbox[0] + 80), int(bbox[1]) + 7), (10, 10, 10), -1)
        cv2.putText(im, '{:s} {:.3f}'.format(class_name, score), (int(bbox[0]), int(bbox[1] - 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 255, 255))  # ,cv2.CV_AA)
    return im


def demo_video(net, im):
    """Detect object classes in an image using pre-computed object proposals."""
    timer = Timer()
    timer.tic()
    scores, boxes, im_scale = im_detect(net, im)
    timer.toc()
    # print(('Detection took {:.3f}s for '
    #        '{:d} object proposals').format(timer.total_time, boxes.shape[0]))

    # Visualize detections for each class
    CONF_THRESH = 0.75

    NMS_THRESH = 0.2
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1  # because we skipped background
        cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]

        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
        im = vis_detections_video(im, cls, dets, thresh=CONF_THRESH)
    # cv2.imwrite(os.path.join('output', str(time.time()) + '.jpg'), im)
    # cv2.imshow('ret', im)
    return im


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        choices=NETS.keys(), default='vgg16')

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()
    cv2.namedWindow('ret', cv2.WINDOW_FULLSCREEN)

    prototxt = '/media/yangshun/0008EB70000B0B9F/PycharmProjects/faster_rcnn_final/models/kitti/VGG16/' \
               'multi_scales_ctx/test.prototxt'
    caffemodel = '/media/yangshun/0008EB70000B0B9F/roi_roi_new/kitti/multi_scale_ctx_all/kittivoc_train/' \
                 'vgg16_faster_rcnn_iter_80000.caffemodel'

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print('\n\nLoaded network {:s}'.format(caffemodel))

    # Load Video File

    pic_root = '/media/yangshun/0008EB70000B0B9F/IMG_9037/'
    images = [pic_root + img for img in os.listdir(pic_root)]
    images = sorted(images)

    save_root = '/media/yangshun/0008EB70000B0B9F/Datasets/KITTI/data_tracking_image_2/result_test/'
    save_path = save_root + 'pic_avi'
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(save_path, fourcc, 20.0, (1280, 720))
    for img in images:
        im = cv2.imread(img)
        image = demo_video(net, im)
        cv2.imshow('ret', image)
        out.write(image)
        k = cv2.waitKey(5) & 0XFF
        if k == ord('q'):
            break
    out.release()
    cv2.destroyAllWindows()

