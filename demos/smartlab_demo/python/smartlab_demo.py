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
import sys
import cv2
import time
from threading import Thread
from collections import deque
from argparse import ArgumentParser, SUPPRESS
from object_detection.detector import Detector
from segmentor import Segmentor, SegmentorMstcn
from evaluator import Evaluator
from display import Display
from openvino.inference_engine import IECore


def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS,
                    help='Show this help message and exit.')
    args.add_argument('-tv', '--topview', required=True,
                    help='Required. Topview stream to be processed. The input must be a single image, '
                    'a folder of images, video file or camera id.')
    args.add_argument('-fv', '--frontview', required=True,
                    help='Required. FrontView to be processed. The input must be a single image, '
                    'a folder of images, video file or camera id.')
    args.add_argument('-m_ta', '--m_topall', help='Required. Path to topview all class model.', required=True, type=str)
    args.add_argument('-m_tm', '--m_topmove', help='Required. Path to topview moving class model.', required=True, type=str)
    args.add_argument('-m_fa', '--m_frontall', help='Required. Path to frontview all class model.', required=True, type=str)
    args.add_argument('-m_fm', '--m_frontmove', help='Required. Path to frontview moving class model.', required=True, type=str)
    
    subparsers = parser.add_subparsers(help='sub-command help')
    args_mutiview = subparsers.add_parser('multiview', help='multiview help')
    args_mutiview.add_argument('-m_en', '--m_encoder', help='Required. Path to encoder model.', required=True, type=str)
    args_mutiview.add_argument('-m_de', '--m_decoder', help='Required. Path to decoder model.', required=True, type=str)
    args_mutiview.add_argument('--mode', default='multiview', help='Option. Path to decoder model.', type=str)
    args_mstcn = subparsers.add_parser('mstcn', help='mstcm help')
    args_mstcn.add_argument('-m_i3d', '--m_i3d', help='Required. Path to i3d model.', required=True, type=str)
    args_mstcn.add_argument('-m_mstcn', '--m_mstcn', help='Required. Path to mstcn model.', required=True, type=str)
    args_mstcn.add_argument('--mode', default='mstcn', help='Option. Path to decoder model.', type=str)

    return parser

# custom threading module
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
    
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def main():
    args = build_argparser().parse_args()

    frame_counter = 0 # Frame index counter
    buffer1 = deque(maxlen=1000)  # Array buffer
    buffer2 = deque(maxlen=1000)
    ie = IECore()
    
    ''' Object Detection Variables'''
    detector = Detector(
            ie,
            [args.m_topall, args.m_topmove],
            [args.m_frontall, args.m_frontmove],
            False)

    '''Video Segmentation Variables'''
    if(args.mode == "multiview"):
        segmentor = Segmentor(ie, args.m_encoder, args.m_decoder)
    elif(args.mode == "mstcn"):
        segmentor = SegmentorMstcn(ie, args.m_i3d, args.m_mstcn)

    '''Score Evaluation Variables'''
    evaluator = Evaluator()

    '''Display Obj Detection, Action Segmentation and Score Evaluation Result'''
    display = Display()

    """
        Process the video.
    """
    cap_top = cv2.VideoCapture(args.topview)
    cap_front = cv2.VideoCapture(args.frontview)

    old_time = time.time()
    fps = 0.0
    interval_second = 1
    interval_start_frame = 0
    total_frame_processed_in_interval = 0.0
    while cap_top.isOpened() and cap_front.isOpened():
        ret_top, frame_top = cap_top.read()  # frame:480 x 640 x 3
        ret_front, frame_front = cap_front.read()

        frame_counter += 1
        if ret_top and ret_front:

            # creat detector thread and segmentor thread
            tdetector = ThreadWithReturnValue(
                target=detector.inference_async_api, args=(frame_top, frame_front,))
            tsegmentor = ThreadWithReturnValue(
                target=segmentor.inference_async_api, args=(frame_top, frame_front, frame_counter,))
            # start()
            tdetector.start()
            tsegmentor.start()
            # join()
            detector_result = tdetector.join()
            top_det_results, front_det_results = detector_result[0], detector_result[1]
            segmentor_result = tsegmentor.join()
            top_seg_results, front_seg_results = segmentor_result[0], segmentor_result[1]

            # ''' The object detection module need to generate detection results(for the current frame) '''
            # top_det_results, front_det_results = detector.inference_async(
            #         img_top=frame_top, img_front=frame_front)

            # ''' The temporal segmentation module need to self judge and generate segmentation results for all historical frames '''

            # if(args.mode == "multiview"):
            #     # top_seg_results, front_seg_results = segmentor.inference(
            #     #         buffer_top=frame_top,
            #     #         buffer_front=frame_front,
            #     #         frame_index=frame_counter)

            #     top_seg_results, front_seg_results = segmentor.inference_async(
            #             buffer_top=frame_top,
            #             buffer_front=frame_front,
            #             frame_index=frame_counter)

            # elif(args.mode == "mstcn"):
            #     buffer1.append(cv2.cvtColor(frame_top, cv2.COLOR_BGR2RGB))
            #     buffer2.append(cv2.cvtColor(frame_front, cv2.COLOR_BGR2RGB))

            #     frame_predictions = segmentor.inference(
            #             buffer_top=buffer1,
            #             buffer_front=buffer2,
            #             frame_index=frame_counter)
            #     top_seg_results = frame_predictions
            #     front_seg_results = frame_predictions
            #     if(len(top_seg_results) == 0):
            #         continue

            ''' The score evaluation module need to merge the results of the two modules and generate the scores '''
            state, scoring, keyframe = evaluator.inference(
                    top_det_results=top_det_results,
                    front_det_results=front_det_results,
                    action_seg_results=top_seg_results,
                    frame_top=frame_top,
                    frame_front=frame_front,
                    frame_counter=frame_counter)

            current_time=time.time()
            current_frame = frame_counter
            if (current_time - old_time > interval_second):
                total_frame_processed_in_interval = current_frame - interval_start_frame
                fps = total_frame_processed_in_interval / (current_time - old_time)
                interval_start_frame = current_frame
                old_time = current_time
            print(fps)

            display.display_result(
                    frame_top=frame_top,
                    frame_front=frame_front,
                    front_seg_results=front_seg_results,
                    top_seg_results=top_seg_results,
                    top_det_results=top_det_results,
                    front_det_results=front_det_results,
                    scoring=scoring,
                    state=state,
                    frame_counter=frame_counter,
                    fps=fps)


        if cv2.waitKey(1) in {ord('q'), ord('Q'), 27}: # Esc
            break

if __name__ == "__main__":
    main()
