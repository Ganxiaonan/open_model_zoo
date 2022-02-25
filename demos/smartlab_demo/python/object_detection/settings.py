# Copyright (c) Megvii, Inc. and its affiliates.
"""
 Copyright (C) 2021-2022 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from copy import deepcopy

# class maps
mw_glb1cls10 = [
    "balance",
    "weights",
    "tweezers",
    "box",
    "battery",
    "tray",
    "ruler",
    "rider",
    "scale",
    "hand"]

mw_ruler1cls3 = [
    "ruler",
    "rider",
    "roundscrew1"]

mw_scale1cls4 = [
    'scale',
    "roundscrew2",
    "pointerhead",
    "pointer"]

# global setting of obj-det
class MwGlobalExp:
    def __init__(self, ie, device, num_classes, model_path,
        nms_thresh, conf_thresh, parent_obj=''):

        self.parent_cat = parent_obj
        self.is_cascaded_det = len(parent_obj) > 0
        self.input_size = (416, 416)

        if num_classes == 10:
            self.mw_classes = mw_glb1cls10
        elif num_classes == 4:
            self.mw_classes = mw_scale1cls4
        elif num_classes == 3:
            self.mw_classes = mw_ruler1cls3
        else:
            raise ValueError(f'num_classes={num_classes} is not supported, use 10 or 3')

        # create reverse map of cls -> category_id
        self.cls2id = {name: i + 1 for i, name in enumerate(self.mw_classes)}
        # define children objects if necessary
        if self.is_cascaded_det:
            self.children_cats = deepcopy(self.mw_classes)
            self.children_cats.remove(parent_obj)

        # define model file
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh
        self.num_classes = num_classes
        self.ie = ie
        self.device = device

    def get_openvino_model(self):
        net = self.ie.read_network(self.model_path)
        input_name = next(iter(net.input_info))
        output_name = next(iter(net.outputs))
        net.input_info[input_name].precision = 'FP32'
        _, _, h, w = net.input_info[input_name].input_data.shape
        net.outputs[output_name].precision = 'FP32'

        return (
            input_name,
            output_name,
            (h, w),
            self.ie.load_network(network = net, device_name = self.device))
