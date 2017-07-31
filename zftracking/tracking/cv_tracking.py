"""tracks larvae on previously segmented video"""

from collections import deque

import numpy as np
import imageio
import colorsys

import cv2


def get_colors(i, pt_buffer):
    color = colorsys.hsv_to_rgb(i / len(pt_buffer), 1.0, 1.0)
    r = int(color[0] * 255)
    g = int(color[1] * 255)
    b = int(color[2] * 255)
    return b, g, r


class Point:
    """class to store points on tracks,
    keeps track of the last detected point to calculate distance"""
    def __init__(self, coords, area, frame, prev=None, norm_area=80, a_weight=1, d_weight=2):
        # coordinates of the center of the detected spot
        self.coords = coords
        # area of the detected spot
        self.area = area
        # standard area for score calculation
        self.norm_area = norm_area
        # frame in video
        self.frame = frame
        self.a_weight = a_weight
        self.d_weight = d_weight
        # if point is first on track, skip distance calculation
        if not prev:
            self.score = 0
            self.distance = 0
        else:
            x_dist = self.coords[0] - prev.coords[0]
            y_dist = self.coords[1] - prev.coords[1]
            self.distance = np.sqrt(x_dist**2 + y_dist**2)
            # score is calculated from area of spot and distance to previous point
            self.score = (self.a_weight * (1 - abs(self.norm_area - self.area)))+(1 - self.d_weight * self.distance)

    # functions to make sorting of spots by score possible
    def __repr__(self):
        return "Point at %i:%i" % self.coords

    def __lt__(self, other):
        return self.score < other.score

    def __le__(self, other):
        return self.score <= other.score

    def __gt__(self, other):
        return self.score > other.score

    def __ge__(self, other):
        return self.score >= other.score

    def __eq__(self, other):
        return self.score == other.score

    def __ne__(self, other):
        return self.score != other.score


class Video:
    """stores the video file and contains tracking method"""
    def __init__(self, path):
        # path to the video file
        self.path = path
        # dictionary for points on the track
        # 'key' is the frame of the video; 'value' is a Point object
        self.pts = {}
        # counts the frame in the video
        self.counter = 0
        # bool for special case on first frame
        self.previous_frame = None
        # read the multi-page tiff file
        self.video = imageio.get_reader(self.path, 'ffmpeg')
        # tracks is a list with lists for the individual track points
        self.tracks = [[]]
        self.skipped_frames = 0

    def track(self):
        """method to track spots in the video"""
        empty = None
        #pt_buffer = deque(maxlen=1000)
        for i, frame in enumerate(self.video):
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            if empty is None:
                empty = np.zeros(frame.shape, np.uint8)
            # iterate over frames in video
            if np.array_equal(empty, frame):
                # skip empty frames
                self.counter += 1
                self.skipped_frames += 1
                continue
            # create mask with the detected spots from the frame
            mask = cv2.inRange(frame, 128, 256)
            mask = cv2.dilate(mask, None, iterations=2)
            mask = cv2.erode(mask, None, iterations=2)
            # find contours in the video
            contours = cv2.findContours(mask.copy(),
                                        cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)[-2]
            if len(contours) > 0:
                if self.previous_frame is None:
                    # for the first frame in the video, just find the largest contour in the mask
                    c = max(contours, key=cv2.contourArea)
                    # compute center point
                    m = cv2.moments(c)
                    try:
                        center = (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))
                    except ZeroDivisionError:
                        continue
                    # add point to the points dictionary
                    self.pts[self.counter] = Point(center, cv2.contourArea(c), self.counter)
                    #pt_buffer.append(self.pts[self.counter].coords)
                    #cv2.circle(frame, self.pts[self.counter].coords, 15, (255, 255, 255), 1)
                    self.previous_frame = self.counter
                else:
                    # make a list of possible spots and choose the one with the highest score
                    candidate_pts = []
                    for c in contours:
                        m = cv2.moments(c)
                        try:
                            center = (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))
                        except ZeroDivisionError:
                            continue
                        candidate_pts.append(Point(center,
                                                   cv2.contourArea(c),
                                                   self.counter,
                                                   self.pts[self.previous_frame]))
                    if len(candidate_pts) >= 1:
                        # add the best spot to the points dictionary
                        c = sorted(candidate_pts)[-1]
                        self.pts[self.counter] = c
                        #pt_buffer.append(self.pts[self.counter].coords)
                        #cv2.circle(frame, self.pts[self.counter].coords, 15, (0, 0, 255), 1)
                        #for j in range(1, len(pt_buffer)):
                        #    b, g, r = get_colors(j, pt_buffer)
                        #    if pt_buffer[j - 1] is None or pt_buffer[j] is None:
                        #        continue
                        #    cv2.line(frame, pt_buffer[j - 1], pt_buffer[j], (b, g, r), 1, cv2.LINE_AA)
                        self.previous_frame = self.counter
                    else:
                        self.skipped_frames += 1
            self.counter += 1
            #cv2.imshow('frame', frame)
            #k = cv2.waitKey(1) & 0xff
            #if k == 27:
            #    cv2.destroyAllWindows()
            #    cv2.waitKey(1) & 0xff

        # after finding all spots, split tracks with gaps of more than 25 frames
        prev_key = 0
        curr_track = 0
        for key in sorted(self.pts):
            if (key - prev_key) > 25:
                self.tracks.append([])
                curr_track += 1
            self.tracks[curr_track].append(self.pts[key])
            prev_key = key

        # delete tracks with less than 10 points
        tracks = [t for t in self.tracks if len(t) >= 10]
        self.tracks = tracks

        return self.tracks
