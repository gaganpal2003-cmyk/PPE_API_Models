from collections import deque
import numpy as np
import cv2
import os
import ast
from Modules.ObjectDetectionModel.ObjectDetection import *
from datetime import datetime
import re
import requests
import torch
from Modules.Live.tracker import Tracker



def is_inside_drawing_box(obj_box, drawing_box):
    """
    Check if the center of an object's bounding box lies inside the drawing box.
    obj_box: (x1, y1, x2, y2)
    drawing_box: (rx, ry, rw, rh) where (rx, ry) is top-left, rw=width, rh=height
    """
    (x1, y1, x2, y2) = obj_box
    (rx, ry, rw, rh) = drawing_box

    # Find center of obj_box
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    # Return True if center lies inside drawing_box, else False
    return (rx <= cx <= rx + rw) and (ry <= cy <= ry + rh)

class Camera(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal()
    startRecog = pyqtSignal(np.ndarray)

    def __init__(self, id, cam_Name, camUrl, camLocation, configData, mainWidgt, db, lineCoordinate=None, deque_size=1):
        super(Camera, self).__init__()
        try:
            self.camIndex = id
            self.dbr = db
            self.cName = cam_Name
            self.camUrl = camUrl
            self.camLocation = camLocation
            self.mainWidgt = mainWidgt
            self.configData = configData
            self.personModel = self.configData.get_person_model_path()
            self.ppeModel = self.configData.get_ppe_model_path()
            self.coco_file = self.configData.get_coco_path()
            self.object_list = self.configData.get_object_list().split(',')
            self.imp_ppe_obj_target = self.configData.get_imp_ppe_name().split(',')
            self.threshold = float(self.configData.get_threshold())
            self.ppe_threshold = float(self.configData.get_ppe_threshold())
            self.detectedFramePath = self.configData.get_detected_frame_path()
            self.skip_frame = int(self.configData.get_skip_handle_frame())
            self.telegramTokenId = self.configData.get_telegram_token_id()
            self.telegramChatId = self.configData.get_telegram_chat_id()
            print("detected frame path:- ", self.detectedFramePath)
            self.max_len_for_frame = int(self.configData.get_max_len_for_previous_frame())
            self.time_duration_video_record = int(self.configData.get_time_duration_video_record())
            self.record_video_res = float(self.configData.get_record_video_resolution())
            self.chunkTimeToSaveImage = self.configData.get_time_chunks()
            self.lineCoordinate = lineCoordinate
            self.image_out_path = self.outImagePath()
            self.online = False
            self.capture = None
            self.inPregress = False
            self.deque = deque(maxlen=deque_size)
            self.dequeLabelFrame = deque(maxlen=deque_size)
            self.uniquePersonFrame = deque(maxlen=deque_size)
            self.materialFrame = deque(maxlen=deque_size)
            self.everyTenSecondFrame = deque(maxlen=deque_size)
            self.dequeLabelAllFrame = deque(maxlen=deque_size)
            self.objName = deque(maxlen=deque_size)
            self.FaceRecog = FaceRecog()
            self.orgFrame = None
            self.objectCount = 0
            self.unique_material = ["truck"]
            self.exit_truck_count = 0
            self.prev_obj_x1 = 0
            self.curr_obj_x1 = 0
            self.prev_truck = 0
            self.curr_truck = 0
            self.missingObject = deque(maxlen=deque_size)
            self.prev_obj_name = None
            self.ppe_img = 1
            
            self.tracker = Tracker()
            self.alerted_violations = set() # Stores (person_id, ppe_class)

            ## Started Updated code - 29-07-2026
            self.record_video_started = False
            self.record_video_start_time = 0
            self.video_writer = None
            self.video_start_time = None
            self.previous_frames = deque(maxlen=self.max_len_for_frame)
            self.record_video_url = deque(maxlen=deque_size)
            ## End
        except Exception as e:
            print(e)

    def is_line_cross(self, line_corrds, obj_coords, frame):
        line_corrds = line_corrds[0]
        x, y, x1, y1 = eval(line_corrds)
        obj_x, obj_y, obj_x1, obj_y1 = obj_coords[0], obj_coords[1], obj_coords[2], obj_coords[3]
        obj_center_x = (obj_x + obj_x1) // 2
        obj_center_y = (obj_y + obj_y1) // 2
        object_center = (obj_center_x, obj_center_y)
        cv2.circle(frame, object_center, 5, (255, 0, 0), -1)
        self.prev_obj_x1 = self.curr_obj_x1
        self.curr_obj_x1 = obj_x1

        return obj_x1 > x1 > self.prev_obj_x1

    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""
        cap = cv2.VideoCapture(link, cv2.CAP_ANY, [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
        if not cap.isOpened():
            return False
        cap.release()
        return True

    def outImagePath(self):
        cwd = os.getcwd()
        today = datetime.today()
        current_date = today.strftime("%d%m%Y")
        dirPath = fr"{cwd}\Training\{current_date}"
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        return dirPath

    def PPEImagePath(self, cropped_img):
        cwd = os.getcwd()
        cn = re.sub(r'(?<=[A-Za-z]) (?=\d)|(?<=\d) (?=[A-Za-z])', '_', self.cName)
        cn = cn.strip()
        dirPath = fr"{cwd}\PpeMissingPicture\{cn}"
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        temp_img_path = fr"{cwd}\PpeMissingPicture\{cn}\temp_cropped.jpg"
        self.ppe_img += 1
        # cv2.imwrite(temp_img_path, cropped_img)
        cv2.imwrite(temp_img_path, cropped_img, [cv2.IMWRITE_JPEG_QUALITY, 30])  # quality range: 0–100

    def croppedImagePath(self, cropped_img):
        cwd = os.getcwd()
        cn = re.sub(r'(?<=[A-Za-z]) (?=\d)|(?<=\d) (?=[A-Za-z])', '_', self.cName)
        cn = cn.strip()
        dirPath = fr"{cwd}\CroppedImage\{cn}"
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        temp_img_path = fr"{cwd}\CroppedImage\{cn}\temp_cropped.jpg"
        cv2.imwrite(temp_img_path, cropped_img)

    def create_storage_folder_for_video_record(self, cur_date, cur_time):
        cwd = os.getcwd()
        cn = re.sub(r'(?<=[A-Za-z]) (?=\d)|(?<=\d) (?=[A-Za-z])', '_', self.cName)
        cn = cn.strip()
        dirPath = fr"{cwd}\results_video\{cn}\{cur_date}"
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)

    # def save_previous_frames(self, current_date, current_time):
    #     """
    #     This function will save the previous frame whenever the detection will happened
    #     :param current_date:
    #     :param current_time:
    #     :return:
    #     """
    #     cwd = os.getcwd()
    #     cn = re.sub(r'(?<=[A-Za-z]) (?=\d)|(?<=\d) (?=[A-Za-z])', '_', self.cName)
    #     cn = cn.strip()
    #     dirPath = fr"{cwd}\results_video\{cn}\{current_date}"
    #     ##
    #     video_name = f"{dirPath}\\{current_time}.mp4"
    #     prev_frm = self.previous_frames[0]
    #     h, w = prev_frm.shape[:2]
    #     fps = 20  # Set according to your camera FPS
    #
    #     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    #     self.video_writer = cv2.VideoWriter(video_name, fourcc, fps, (w, h))
    #
    #     len_of_previous_frame = len(self.previous_frames)
    #     for i in range(1, len_of_previous_frame):
    #         frms = self.previous_frames[i]
    #         self.video_writer.write(frms)
    #     self.previous_frames.clear()
    #     return video_name

    def save_previous_frames(self, current_date, current_time):
        """
        Save the previous frames as a compressed video.
        Reduces video resolution and uses a lower FPS to reduce file size.

        :param current_date:
        :param current_time:
        :return:
        """
        cwd = os.getcwd()

        cn = re.sub(
            r'(?<=[A-Za-z]) (?=\d)|(?<=\d) (?=[A-Za-z])',
            '_',
            self.cName
        )
        cn = cn.strip()

        dirPath = fr"{cwd}\results_video\{cn}\{current_date}"

        # Create directory if it does not exist
        os.makedirs(dirPath, exist_ok=True)

        video_name = f"{dirPath}\\{current_time}.mp4"

        if not self.previous_frames:
            return None

        prev_frm = self.previous_frames[0]

        # Original resolution
        h, w = prev_frm.shape[:2]

        # ---------------------------------------------------------
        # Reduce resolution
        # Example:
        # 1920x1080 -> 960x540
        # 1280x720  -> 640x360
        # ---------------------------------------------------------
        scale = self.record_video_res

        new_w = int(w * scale)
        new_h = int(h * scale)

        # Keep dimensions even
        new_w = new_w - (new_w % 2)
        new_h = new_h - (new_h % 2)

        # Reduce FPS
        fps = 10

        # Try H.264 first
        fourcc = cv2.VideoWriter_fourcc(*'avc1')

        self.video_writer = cv2.VideoWriter(
            video_name,
            fourcc,
            fps,
            (new_w, new_h)
        )

        # If H.264 is not supported, fall back to mp4v
        if not self.video_writer.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            self.video_writer = cv2.VideoWriter(
                video_name,
                fourcc,
                fps,
                (new_w, new_h)
            )

        len_of_previous_frame = len(self.previous_frames)

        for i in range(len_of_previous_frame):
            frms = self.previous_frames[i]

            # Resize frame
            frms = cv2.resize(
                frms,
                (new_w, new_h),
                interpolation=cv2.INTER_AREA
            )

            self.video_writer.write(frms)


        self.previous_frames.clear()
        return video_name

    def load_network_stream(self):
        device, model, dataset, dt = self.FaceRecog.ExtractDeviceModelDataset(self.camUrl, self.personModel,
                                                                              self.coco_file)
        self.device = device
        self.model = model
        self.dataset = dataset
        self.dt = dt

        ##
        ppe_device, ppe_model, ppe_dataset, ppe_dt = self.FaceRecog.ExtractDeviceModelDataset(self.camUrl,
                                                                                              self.ppeModel,
                                                                                              self.coco_file)
        self.ppe_device = ppe_device
        self.ppe_model = ppe_model
        self.ppe_dataset = ppe_dataset
        self.ppe_dt = ppe_dt
        #

        if self.verify_network_stream(self.camUrl):
            self.online = True
            start_time = datetime.now()
            time_chunk = int(self.chunkTimeToSaveImage)
            all_ppe = list(self.ppe_model.names.values())
            frame_cnt = 0
            for path, im, im0s, vid_cap, s in self.dataset:
                    frame_cnt += 1  ### added by AAdi

                    ### added by AAdi
                    if self.skip_frame > 1:
                        if frame_cnt % self.skip_frame != 0:
                            continue
                    ##END
                    if not self.online:
                        break
                    self.orgFrame = im0s.copy()
                    if self.mainWidgt and self.mainWidgt.newCoordinate:
                        current_camera = self.mainWidgt.camList.currentText()
                        if current_camera == self.cName:
                            currentCamereaXY = self.dbr.select(
                                f"select xy, x1y1  from camera_frame_coordinates where cameName='{self.cName}'")
                            if currentCamereaXY and len(currentCamereaXY) > 0 and currentCamereaXY[0][0] and currentCamereaXY[0][1]:
                                try:
                                    camera_with_coordinates = [ast.literal_eval(currentCamereaXY[0][0]),
                                                               ast.literal_eval(currentCamereaXY[0][1])]
                                    self.lineCoordinate = camera_with_coordinates
                                except Exception:
                                    pass
                            self.mainWidgt.newCoordinate = False
                    imgData = self.FaceRecog.getFinalLabelImage(self.model, self.model.names, self.dt, im, im0s,
                                                                self.object_list, self.threshold, self.lineCoordinate)

                    try:
                        final_image, person_found, list_of_detections = imgData[0], imgData[1], imgData[2]
                    except:
                        continue

                    try:
                        self.previous_frames.append(final_image)
                        
                        if self.record_video_started and self.video_writer is not None:
                            self.video_writer.write(final_image)
                            end_time = datetime.now()
                            check_differance_to_save_video = (end_time - self.video_start_time).total_seconds()
                            if check_differance_to_save_video >= self.time_duration_video_record:
                                self.record_video_started = False
                                self.video_writer.release()
                                self.video_writer = None
                                print(f"{self.time_duration_video_record}-second video saved.")

                        ppe_image_det = final_image
                        new_missing_ppe = []
                        objName = ""

                        if person_found and list_of_detections:
                            # Update tracker with person bboxes
                            bboxes = [det['bbox'] for det in list_of_detections]
                            tracker_inputs = []
                            for bbox in bboxes:
                                x1, y1, x2, y2 = bbox
                                tracker_inputs.append([x1, y1, x2 - x1, y2 - y1])
                            
                            tracked_objects = self.tracker.update(tracker_inputs)
                            
                            # Clean up old alerted violations for persons no longer tracked
                            current_person_ids = set(self.tracker.center_points.keys())
                            self.alerted_violations = {av for av in self.alerted_violations if av[0] in current_person_ids}

                            # Run PPE detection on full frame in memory instead of using disk I/O
                            stride, names, pt = self.ppe_model.stride, self.ppe_model.names, self.ppe_model.pt
                            imgsz = self.FaceRecog.ExtractImageSize(stride)
                            dataset = self.FaceRecog.ExtractOcrDataset(final_image, imgsz, stride, pt)
                            
                            ocr_im, ocr_im0s = dataset.finalIm, dataset.finalIm0
                            with self.ppe_dt[0]:
                                ocr_im = torch.from_numpy(ocr_im).to(self.ppe_model.device)
                                ocr_im = ocr_im.half() if self.ppe_model.fp16 else ocr_im.float()
                                ocr_im /= 255
                                if len(ocr_im.shape) == 3:
                                    ocr_im = ocr_im[None]
                            with self.ppe_dt[1]:
                                ocr_pred = self.ppe_model(ocr_im, augment=False, visualize=False)
                            with self.ppe_dt[2]:
                                ocr_pred = self.FaceRecog.getNonMaxSuppresion(ocr_pred, self.ppe_threshold)

                            annotator = self.FaceRecog.getOcrAnnotator(ocr_im0s.copy(), names)
                            
                            for i, det in enumerate(ocr_pred):
                                if len(det):
                                    det[:, :4] = self.FaceRecog.getOCRScaleBoxes(ocr_im, det, ocr_im0s)
                                    for *xyxy, conf, cls in reversed(det):
                                        class_name = str(names[int(cls)])
                                        if class_name not in self.imp_ppe_obj_target:
                                            continue
                                            
                                        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                                        ppe_cx = (x1 + x2) // 2
                                        ppe_cy = (y1 + y2) // 2
                                        
                                        # Check if inside drawing box
                                        if self.lineCoordinate:
                                            try:
                                                lx, ly = self.lineCoordinate[0][0], self.lineCoordinate[0][1]
                                                lw, lh = self.lineCoordinate[1][0], self.lineCoordinate[1][1]
                                                if not (lx <= ppe_cx <= lx + lw and ly <= ppe_cy <= ly + lh):
                                                    continue
                                            except:
                                                pass
                                                
                                        # Find which person this PPE belongs to
                                        best_person_id = None
                                        min_dist = float('inf')
                                        for obj in tracked_objects:
                                            px, py, pw, ph, p_id, _ = obj
                                            # Check if PPE center is inside person bbox
                                            if px <= ppe_cx <= px + pw and py <= ppe_cy <= py + ph:
                                                p_cx = px + pw // 2
                                                p_cy = py + ph // 2
                                                dist = (ppe_cx - p_cx)**2 + (ppe_cy - p_cy)**2
                                                if dist < min_dist:
                                                    min_dist = dist
                                                    best_person_id = p_id
                                                    
                                        if best_person_id is not None:
                                            if (best_person_id, class_name) not in self.alerted_violations:
                                                self.alerted_violations.add((best_person_id, class_name))
                                                new_missing_ppe.append(class_name)
                                                objName = list_of_detections[0]['name'] # just taking the first one as fallback
                                                
                                        # Always draw the bbox if it's an important PPE target
                                        object_box_color = self.FaceRecog.getOcrColors(int(cls))
                                        annotator.box_label([x1, y1, x2, y2], f"{class_name} {conf:.2f}", color=object_box_color)

                            self.PPEImagePath(annotator.result())
                            ppe_image_det = annotator.result()

                        if len(new_missing_ppe) > 0:
                            # Start video recording
                            self.record_video_started = True
                            self.video_start_time = datetime.now()
                            current_date = datetime.now().strftime('%d_%m_%Y')
                            current_time = datetime.now().strftime('%H_%M_%S')
                            self.create_storage_folder_for_video_record(current_date, current_time)
                            if not self.video_writer:
                                video_path = self.save_previous_frames(current_date, current_time)
                                self.record_video_url.append(video_path)
                                
                            self.materialFrame.append(ppe_image_det)
                            self.deque.append(ppe_image_det)
                            self.dequeLabelAllFrame.append(ppe_image_det)
                            self.objName.append(objName)
                            self.missingObject.append(new_missing_ppe)
                            self.progress.emit()
                        else:
                            self.deque.append(ppe_image_det)
                            self.dequeLabelAllFrame.append(ppe_image_det)
                            self.objName.append(objName)
                            if person_found and list_of_detections:
                                self.missingObject.append([])
                            self.progress.emit()

                    except Exception as e:
                        print(f"Error in load_network_stream: {e}")
                        pass

    @pyqtSlot(np.ndarray)
    def get_frame(self):
        """get video frame"""
        if self.deque and self.online:
            # Grab latest frame
            return self.deque.pop()
        else:
            return None

    def get_new_truck(self):
        """get labelled frame"""
        if self.uniquePersonFrame:
            return self.uniquePersonFrame.pop()
        else:
            return None

    def get_material_img(self):
        """Get current detect image"""
        if self.materialFrame:
            return self.materialFrame.pop()
        else:
            return None

    def get_every_ten_second_frame(self):
        """get labelled frame"""
        if self.everyTenSecondFrame:
            # Grab latest frame
            return self.everyTenSecondFrame.pop()
        else:
            return None

    def get_all_frame_label(self):
        if self.dequeLabelAllFrame:
            # Grab latest frame
            return self.dequeLabelAllFrame.pop()
        else:
            return None

    def get_object_name(self):
        if self.objName:
            return self.objName.pop()
        else:
            return None

    def get_missing_ppe_list(self):
        if self.missingObject:
            return self.missingObject.pop()
        else:
            return None

    def get_record_video_path(self):
        if self.record_video_url:
            return self.record_video_url.pop()
        else:
            return None