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

import numpy as np
import cv2
import os


class Display:
    def __init__(self):
        '''Score Evaluation Variables'''
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        self.writer = cv2.VideoWriter("result.mp4", fourcc, 30, (1920, 890))
        self.wait_icon = cv2.imread(f'{os.getcwd()}/icon/wait.jpg',cv2.IMREAD_UNCHANGED)
        self.no_icon = cv2.imread(f'{os.getcwd()}/icon/no.jpg',cv2.IMREAD_UNCHANGED)
        self.done_icon = cv2.imread(f'{os.getcwd()}/icon/done.jpg',cv2.IMREAD_UNCHANGED)

    def draw_text(self,img, text,
          font=cv2.FONT_HERSHEY_TRIPLEX,
          pos=(0, 0),
          font_scale=1,
          font_thickness=1,
          text_color=(255,255,255),
          text_color_bg=(0, 0, 0),
          icon = None
          ):
        distance_text_and_icon = 30
        x, y = pos
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_w, text_h = text_size
        cv2.rectangle(img, (x-10-distance_text_and_icon,y-10), (x + 700, y + text_h+10), text_color_bg, -1)
        self.score_board[y:y+22,x-distance_text_and_icon:x+22-distance_text_and_icon] = cv2.resize(icon, (text_h,text_h), interpolation = cv2.INTER_AREA)
        cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)
        return text_size

    def draw_text_without_background(self,img, text,
          font=cv2.FONT_HERSHEY_TRIPLEX,
          pos=(0, 0),
          font_scale=1,
          font_thickness=2,
          text_color=(255,255,255),
          text_color_bg=(0, 0, 0)
          ):
        x, y = pos
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_w, text_h = text_size
        cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)
        return text_size

    def display_result(self, frame_top, frame_side, side_seg_results, top_seg_results, \
                       top_det_results, side_det_results, scoring, state, keyframe, frame_counter, fps, filename):

        if state == 'Initial':
            display_status = 'Setting Up ...'
            initial_text_color_bg = (255,0,0)
            measuring_text_color_bg = (128,128,128)
            initial_icon = self.wait_icon
            measuring_icon = self.no_icon
        elif state == 'Measuring':
            display_status = 'Set Up Done. Evaluating Measuring Phase...'
            initial_text_color_bg = (0,180,0)
            measuring_text_color_bg = (255,0,0)
            initial_icon = self.done_icon
            measuring_icon =self.wait_icon
        elif state == 'Finish':
            count = 0
            for item in scoring.values():
                if item == 1:
                    count += 1
            total_score_obtained = count
            display_status = f'Experiment completed. Total Score is {total_score_obtained}/8'
            initial_text_color_bg = (0,180,0)
            measuring_text_color_bg = (0,180,0)
            initial_icon = self.done_icon
            measuring_icon = self.done_icon

        # renew score board so that when put cv2.puttext text will not overlap
        self.score_board = np.zeros([350, 1920, 3], dtype=np.uint8)

        # add action name of each frame at middle top
        cv2.putText(frame_top, side_seg_results, (700, 80), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255), fontScale=1.5,
                    thickness=3)
        cv2.putText(frame_side, top_seg_results, (700, 80), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255), fontScale=1.5,
                    thickness=3)

        # display frame_number at top left corner
        cv2.putText(frame_top, f"frame{frame_counter: 6d}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255),
                    fontScale=1.5, thickness=3)
        cv2.putText(frame_side, f"frame{frame_counter: 6d}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255),
                    fontScale=1.5, thickness=3)

        # display FPS at top left corner
        cv2.putText(frame_top, f"FPS: {fps: .2f}", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255),
                    fontScale=1.5, thickness=3)
        cv2.putText(frame_side, f"FPS: {fps: .2f}", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255),
                    fontScale=1.5, thickness=3)

        # display obj detection result for both view
        for row, obj_cls in zip(top_det_results[0], top_det_results[2]):
            x_min = int(row[0])
            y_min = int(row[1])
            x_max = int(row[2])
            y_max = int(row[3])

            cv2.putText(frame_top, obj_cls, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255),
                        fontScale=0.9, thickness=2)
            frame_top = cv2.rectangle(frame_top, (x_min, y_min), (x_max, y_max), color=(255, 0, 0), thickness=2)

        for row, obj_cls in zip(side_det_results[0], side_det_results[2]):
            x_min = int(row[0])
            y_min = int(row[1])
            x_max = int(row[2])
            y_max = int(row[3])

            cv2.putText(frame_side, obj_cls, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, color=(0, 0, 255),
                        fontScale=0.9, thickness=2)
            frame_side = cv2.rectangle(frame_side, (x_min, y_min), (x_max, y_max), color=(255, 0, 0), thickness=2)

        # display scoring
        i_rider = scoring['initial_score_rider']
        i_balance = scoring['initial_score_balance']
        m_rider_tweezers = scoring['measuring_score_rider_tweezers']
        m_balance = scoring['measuring_score_balance']
        m_object_left = scoring['measuring_score_object_left']
        m_weights_right = scoring['measuring_score_weights_right']
        m_weights_tweezers = scoring['measuring_score_weights_tweezers']
        e_tidy = scoring['end_score_tidy']

        # display keyframe
        i_rider_k = keyframe['initial_score_rider']
        i_balance_k = keyframe['initial_score_balance']
        m_rider_tweezers_k = keyframe['measuring_score_rider_tweezers']
        m_balance_k = keyframe['measuring_score_balance']
        m_object_left_k = keyframe['measuring_score_object_left']
        m_weights_right_k = keyframe['measuring_score_weights_right']
        m_weights_tweezers_k = keyframe['measuring_score_weights_tweezers']
        e_tidy_k = keyframe['end_score_tidy']

        w1 = 150
        w2 = 950

        w, h = self.draw_text_without_background(self.score_board, f"SCORE - {display_status}",\
             pos=(w1,10),text_color_bg=initial_text_color_bg)
        w, h = self.draw_text(self.score_board, f"INITIALISE RIDER[{i_rider}]",\
             pos=(w1,70),text_color_bg=initial_text_color_bg,icon=initial_icon)
        w, h = self.draw_text(self.score_board, f"INITIALISE BALANCE[{i_balance}]",\
             pos=(w2,70),text_color_bg=initial_text_color_bg,icon=initial_icon)
        w, h = self.draw_text(self.score_board, f"PUT OBJECT ON LEFT TRAY[{m_object_left}]",\
             pos=(w1,130),text_color_bg=measuring_text_color_bg,icon=measuring_icon)
        w, h = self.draw_text(self.score_board, f"PUT WEIGHTS ON RIGHT TRAY[{m_weights_right}]",\
             pos=(w2,130),text_color_bg=measuring_text_color_bg,icon=measuring_icon)
        w, h = self.draw_text(self.score_board, f"MOVE WEIGHTS WITH TWEEZER[{m_weights_tweezers}]",\
             pos=(w1,190),text_color_bg=measuring_text_color_bg,icon=measuring_icon)
        w, h = self.draw_text(self.score_board, f"ADJUST RIDER WITH TWEEZER[{m_rider_tweezers}]",\
             pos=(w2,190),text_color_bg=measuring_text_color_bg,icon=measuring_icon)
        w, h = self.draw_text(self.score_board, f"SCALE IS BALANCED[{m_balance}]",\
             pos=(w1,250),text_color_bg=measuring_text_color_bg,icon=measuring_icon)
        w, h = self.draw_text(self.score_board, f"PUT EQUIPMENTS BACK[{e_tidy}]",\
             pos=(w2,250),text_color_bg=measuring_text_color_bg,icon=measuring_icon)

        # resize images and display them side by side, then concatenate with a scoring board to display marks
        frame_top = cv2.resize(
            frame_top, (int(frame_top.shape[1] / 2), int(frame_top.shape[0] / 2)))
        frame_side = cv2.resize(
            frame_side, (int(frame_side.shape[1] / 2), int(frame_side.shape[0] / 2)))
        result_image = np.concatenate((frame_top, frame_side), axis=1)
        result_image = np.concatenate((result_image, self.score_board), axis=0)
        self.writer.write(result_image)
        
        cv2.imshow("Smart Science Lab", result_image)
        # cv2.imshow(filename, result_image)
