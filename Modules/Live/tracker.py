import math


class Tracker:
    def __init__(self, max_age=15, max_distance=50):
        self.center_points = {}
        self.id_count = 0
        self.crossed_ids = set()  # New set to keep track of objects that crossed the line
        self.bag_count = 0
        self.same_object_detected = False
        self.max_age = max_age
        self.max_distance = max_distance
        
        # Keep track of how many consecutive frames an object has been missing
        self.missing_frames = {}

    def update(self, objects_rect):
        objects_bbs_ids = []
        
        # Set all existing tracked objects as missing initially
        for id in list(self.center_points.keys()):
            self.missing_frames[id] += 1

        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + w) // 2
            cy = (y + h) // 2

            self.same_object_detected = False
            
            # Find closest center point within max_distance
            closest_id = None
            min_dist = float('inf')
            
            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])
                if dist < self.max_distance and dist < min_dist:
                    min_dist = dist
                    closest_id = id

            if closest_id is not None:
                self.center_points[closest_id] = (cx, cy)
                self.missing_frames[closest_id] = 0
                objects_bbs_ids.append([x, y, w, h, closest_id, True])
                self.same_object_detected = True
            else:
                self.center_points[self.id_count] = (cx, cy)
                self.missing_frames[self.id_count] = 0
                objects_bbs_ids.append([x, y, w, h, self.id_count, False])
                self.id_count += 1

        # Clean up center points for objects that have been missing for too long
        for id in list(self.center_points.keys()):
            if self.missing_frames[id] > self.max_age:
                del self.center_points[id]
                del self.missing_frames[id]

        return objects_bbs_ids

#
# import math
#
# class Tracker:
#     def __init__(self):
#         self.center_points = {}
#         self.id_count = 0
#         self.crossed_ids = set()  # Keep track of crossed objects
#
#     def update(self, objects_rect):
#         objects_bbs_ids = []
#
#         for rect in objects_rect:
#             x, y, w, h = rect
#             cx = (x + w) // 2
#             cy = (y + h) // 2
#
#             same_object_detected = False
#             for object_id, pt in self.center_points.items():
#                 dist = math.hypot(cx - pt[0], cy - pt[1])
#
#                 if dist < 35:  # Match with an existing object
#                     self.center_points[object_id] = (cx, cy)
#                     objects_bbs_ids.append([x, y, w, h, object_id])
#                     same_object_detected = True
#                     break
#
#             if not same_object_detected:  # Assign new ID for a new object
#                 self.center_points[self.id_count] = (cx, cy)
#                 objects_bbs_ids.append([x, y, w, h, self.id_count])
#                 self.id_count += 1
#
#         # Clean up center points for objects no longer detected
#         new_center_points = {obj_id: self.center_points[obj_id] for _, _, _, _, obj_id in objects_bbs_ids}
#         self.center_points = new_center_points
#
#         return objects_bbs_ids
