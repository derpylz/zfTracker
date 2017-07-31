#!python
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 2016

@author: Nils Jonathan Trost

Script that tracks adult fish in a narrow aquarium.
"""

import argparse
import os
from datetime import datetime

import errno
import imageio
import cv2
from collections import deque
import colorsys
import numpy as np
import shutil

from zftracking.external.runffmpeg import Ffmpeg
from zftracking.tracking.interactive_crop import Image
from zftracking.tracking.cv_tracking import Point
from zftracking.tracking.analyze_tracks import Analysis


def silent_remove(filename):
    """removes file without error on non existing file"""
    try:
        os.remove(filename)
    except OSError as err:
        if err.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


def main():
    """main function to track fish"""
    parser = argparse.ArgumentParser(description="Tracks adult fish")
    # add options for argument parser
    parser.add_argument("in_path",
                        help="Path to the video directory.")
    parser.add_argument("out_path",
                        help="Directory for results. Should be empty.")
    parser.add_argument("-x", "--keep_temp", action="store_true",
                        help="Keep temporary folder after execution.")
    parser.add_argument("--visual", action="store_true",
                        help="shows a visual representation of the tracking progress.")

    # parse arguments from command line
    args = parser.parse_args()
    # get all file names and directories ready
    out_dir, temp_dir, video_bases, videos = housekeeping(args)
    borders = []
    for i in range(len(videos)):
        v = videos[i]
        get_borders(borders, temp_dir, v)

    for i in range(len(videos)):
        vbn = video_bases[i]
        v = videos[i]
        scaled_video = "scaled_" + vbn + ".avi"
        ffmpeg = Ffmpeg(v, os.path.join(temp_dir, scaled_video))
        ffmpeg.f = "avi"
        ffmpeg.vcodec = "libx264rgb"
        ffmpeg.width = 480
        ffmpeg.run()

    for i in range(len(videos)):
        vbn = video_bases[i]
        pts = tracker(args, temp_dir, vbn)
        border = borders[i]
        tracks_lower, tracks_upper = split_tracks(border, pts)
        analysis = Analysis(tracks_lower, tracks_upper, px_size=0.06)
        analysis.analyze(os.path.join(out_dir, 'stats.txt'), vbn, vel=True)

    if not args.keep_temp:
        shutil.rmtree(temp_dir)


def housekeeping(args):
    in_dir = os.path.abspath(args.in_path)
    videos = []
    for f in os.listdir(in_dir):
        if os.path.isfile(os.path.join(in_dir, f)):
            videos.append(os.path.join(in_dir, f))
    video_names = []
    video_bases = []
    for v in videos:
        video_names.append(os.path.basename(v))
        video_bases.append(os.path.splitext(os.path.basename(v))[0])
    out_dir = os.path.abspath(args.out_path)
    with open(os.path.join(out_dir, 'stats.txt'), 'w') as out:
        out.write('video\t')
        out.write('time in lower region [s]\t')
        out.write('distance in lower region [cm]\t')
        out.write('time in upper region [s]\t')
        out.write(' distance in upper region [cm]\t')
        out.write(' average velocity [cm/s]\n')
    if not out_dir.endswith('/'):
        out_dir += '/'
    # make directory for temporary results
    temp_dir = os.path.join(out_dir, "temp/")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return out_dir, temp_dir, video_bases, videos


def get_borders(borders, temp_dir, v):
    thumb = 'thumb.tiff'
    thumb = os.path.join(temp_dir, thumb)
    silent_remove(thumb)
    ffmpeg = Ffmpeg(v, os.path.join(thumb))
    ffmpeg.pix_fmt = "gray8"
    ffmpeg.vframes = "1"
    ffmpeg.ss = "150"
    ffmpeg.run()
    image = Image(thumb, scaling=4)
    border = image.set_border()
    border = int(np.mean((border[0][1], border[1][1])))
    borders.append(border)


def split_tracks(border, pts):
    tracks_lower = []
    tracks_upper = []
    idx_l = -1
    idx_u = -1
    prev_l = None
    for pt in sorted(pts):
        if prev_l is None:
            if pts[pt].coords[1] < border:
                prev_l = False
                tracks_upper.append([pts[pt]])
                idx_u += 1
            else:
                prev_l = True
                tracks_lower.append([pts[pt]])
                idx_l += 1
        elif prev_l:
            if pts[pt].coords[1] < border:
                prev_l = False
                idx_u += 1
                tracks_upper.append([pts[pt]])
            else:
                tracks_lower[idx_l].append(pts[pt])
        else:
            if pts[pt].coords[1] < border:
                tracks_upper[idx_u].append(pts[pt])
            else:
                prev_l = True
                idx_l += 1
                tracks_lower.append([pts[pt]])
    return tracks_lower, tracks_upper


def tracker(args, temp_dir, vbn):
    scaled_video = "scaled_" + vbn + ".avi"
    vid = imageio.get_reader(os.path.join(temp_dir, scaled_video), 'ffmpeg')
    tot_frames = vid.get_meta_data()['nframes']
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fgbg = cv2.createBackgroundSubtractorMOG2()
    pts = {}
    previous_frame = False
    counter = 0
    skipped_frames = 0
    pt_buffer = deque(maxlen=100)
    for idx, frame in enumerate(vid):
        fgmask = fgbg.apply(frame)
        if args.visual:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        mask = cv2.inRange(fgmask, 128, 256)
        contours = cv2.findContours(mask.copy(),
                                    cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[-2]
        if len(contours) > 0:
            if not previous_frame:
                # for the first frame in the video, just find the largest contour in the mask
                c = max(contours, key=cv2.contourArea)
                # compute center point
                m = cv2.moments(c)
                try:
                    center = (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))
                except ZeroDivisionError:
                    continue
                # add point to the points dictionary
                pts[counter] = Point(center, cv2.contourArea(c), counter, norm_area=120, a_weight=2)
                if args.visual:
                    pt_buffer.append(pts[counter].coords)
                    cv2.circle(frame, pts[counter].coords, 15, (0, 0, 255), 1)
                previous_frame = counter
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
                                               counter,
                                               pts[previous_frame],
                                               norm_area=120,
                                               a_weight=2))
                if len(candidate_pts) >= 1:
                    # add the best spot to the points dictionary
                    c = sorted(candidate_pts)[-1]
                    pts[counter] = c
                    if args.visual:
                        pt_buffer.append(pts[counter].coords)
                        cv2.circle(frame, pts[counter].coords, 15, (0, 0, 255), 1)
                        for i in range(1, len(pt_buffer)):
                            b, g, r = get_colors(i, pt_buffer)
                            if pt_buffer[i - 1] is None or pt_buffer[i] is None:
                                continue
                            cv2.line(frame, pt_buffer[i - 1], pt_buffer[i], (b, g, r), 1, cv2.LINE_AA)
                    previous_frame = counter
                else:
                    skipped_frames += 1
        counter += 1
        status_bar(counter, tot_frames, vbn)
        if args.visual:
            cv2.imshow('frame', frame)
            k = cv2.waitKey(1) & 0xff
            if k == 27:
                cv2.destroyAllWindows()
                cv2.waitKey(1) & 0xff
                args.visual = False
    print('\n')
    return pts


def status_bar(counter, tot_frames, vbn):
    print('\r' + vbn + ' |' + int(counter / tot_frames * 40) * "=" + int(
        40 - (counter / tot_frames * 40)) * "_" + '| ' + str(counter), end='')


def get_colors(i, pt_buffer):
    color = colorsys.hsv_to_rgb(i / len(pt_buffer), 1.0, 1.0)
    r = int(color[0] * 255)
    g = int(color[1] * 255)
    b = int(color[2] * 255)
    return b, g, r


if __name__ == '__main__':
    start = datetime.now()
    main()
    end = datetime.now()
    print("\nExecuted in " + str(end - start))
