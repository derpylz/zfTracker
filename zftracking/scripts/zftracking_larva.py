#!python
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 2 2016

@author: Nils Jonathan Trost

Script that tracks larvae in circular arenas.

Needs ffmpeg and FIJI to run.
"""

import argparse
import os
from datetime import datetime

import errno

import shutil

from zftracking.tracking.interactive_crop import Image
from zftracking.external.runffmpeg import Ffmpeg
from zftracking.tracking.analyze_tracks import Analysis
from zftracking.tracking.analyze_tracks import distance
from zftracking.tracking.cv_tracking import Video


def silent_remove(filename):
    """removes file without error on non existing file"""
    try:
        os.remove(filename)
    except OSError as err:
        if err.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


def crop_and_mask(infile, temp_dir, thumb, prev_crop=False, prev_mask=False):
    """initiates the interactive cropping and masking of the video"""
    image = Image(thumb, prev_crop=prev_crop)
    crop = image.crop()
    silent_remove(os.path.join(temp_dir, "crop.tiff"))
    ffmpeg = Ffmpeg(infile, os.path.join(temp_dir, "crop.tiff"))
    ffmpeg.pix_fmt = "gray8"
    ffmpeg.vframes = "1"
    ffmpeg.ss = "150"
    ffmpeg.filter = "crop=" + crop
    ffmpeg.run()
    image = Image(os.path.join(temp_dir, "crop.tiff"), prev_mask=prev_mask)
    mask = image.mask()
    return crop, mask


def prepare_vid(cropped_video, infile, temp_dir, crop):
    """get FIJI compatible avi from video"""
    ffmpeg = Ffmpeg(infile, temp_dir + cropped_video)
    ffmpeg.pix_fmt = "nv12"
    ffmpeg.f = "avi"
    ffmpeg.vcodec = "rawvideo"
    ffmpeg.filter = "crop=" + crop
    ffmpeg.run()


def main():
    """main function to track larvae"""
    args = get_arguments()
    # get all file names and directories ready
    infile = os.path.abspath(args.in_path)
    video_name = os.path.basename(infile)
    video_name_base = os.path.splitext(video_name)[0]
    out_dir = os.path.abspath(args.out_path)
    prep_outfile(out_dir)
    if not out_dir.endswith('/'):
        out_dir += '/'
    # make directory for temporary results
    temp_dirs = []
    seg_paths = []
    for i in range(args.number):
        temp_dirs.append(os.path.join(out_dir, "temp_" + str(i) + "/"))
        # segmentation path does not include file extension,
        # it will be appended in FIJI macro
        seg_paths.append(os.path.join(out_dir, "SEG_" + str(i) + '_' + video_name_base))
    cropped_video = "cropped_" + video_name_base + ".avi"
    thumb = 'thumb.tiff'
    start_frame = None
    end_frame = None
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    crops = []
    masks = []
    silent_remove(os.path.join(temp_dirs[0], "thumb.tiff"))
    ffmpeg = Ffmpeg(infile, os.path.join(temp_dirs[0], thumb))
    ffmpeg.pix_fmt = "gray8"
    ffmpeg.vframes = "1"
    ffmpeg.ss = "150"
    ffmpeg.run()

    thumb = os.path.join(temp_dirs[0], thumb)
    if not args.manual_crop and args.number == 24:
        # crop the image into 24 parts
        # let the user choose the region in which the wells are.
        image = Image(thumb)
        crops = image.auto_crop()
        prev_mask = False
        for i in range(len(crops)):
            crop = crops[i]
            temp_dir = temp_dirs[i]
            silent_remove(os.path.join(temp_dir, "crop.tiff"))
            ffmpeg = Ffmpeg(infile, os.path.join(temp_dir, "crop.tiff"))
            ffmpeg.pix_fmt = "gray8"
            ffmpeg.vframes = "1"
            ffmpeg.ss = "150"
            ffmpeg.filter = "crop=" + crop
            ffmpeg.run()
            image = Image(os.path.join(temp_dir, "crop.tiff"), prev_mask=prev_mask)
            prev_mask = image.mask()
            masks.append(prev_mask)
    else:
        m = (0, 0)
        for i in range(len(temp_dirs)):
            # prepare cropping and masking
            temp_dir = temp_dirs[i]
            if len(crops) == 0:
                c, m = crop_and_mask(infile, temp_dir, thumb)
                crops.append(c)
                masks.append(m)
            else:
                c, m = crop_and_mask(infile, temp_dir, thumb, crops[-1], m)
                crops.append(c)
                masks.append(m)

    for i in range(len(temp_dirs)):
        temp_dir = temp_dirs[i]
        crop = crops[i]
        prepare_vid(cropped_video, infile, temp_dir, crop)

    for i in range(len(temp_dirs)):
        # track the segmented video
        temp_dir = temp_dirs[i]
        mask = masks[i]
        vid = Video(temp_dir + cropped_video)
        tracks = vid.track()
        outer_tracks = []
        inner_tracks = []
        for track in tracks:
            outer_track, inner_track = (split_tracks(mask, track))
            outer_tracks += outer_track
            inner_tracks += inner_track
        analysis = Analysis(outer_tracks, inner_tracks)
        analysis.analyze(out_dir + 'stats.txt', i)
        if args.save_track_image:
            analysis.save_track_image(temp_dirs[i], out_dir, i)
        if args.save_track:
            # save track points to file
            analysis.save_track(out_dir, i)

    if not args.keep_temp:
        for temp_dir in temp_dirs:
            shutil.rmtree(temp_dir)


def prep_outfile(out_dir):
    with open(os.path.join(out_dir, 'stats.txt'), 'w') as out:
        out.write('well\t')
        out.write('time in outer region\t')
        out.write('distance in outer region\t')
        out.write('time in inner region\t')
        out.write(' distance in inner region\t')
        out.write(' % of time in outer region\t')
        out.write(' % of distance in outer region\n')


def get_arguments():
    parser = argparse.ArgumentParser(description="Tracks larvae for thigmotaxis experiment")
    # add options for argument parser
    parser.add_argument("in_path",
                        help="Path to the video.")
    parser.add_argument("out_path",
                        help="Directory for results. Should be empty.")
    parser.add_argument("-x", "--keep_temp", action="store_true",
                        help="Keep temporary folder after execution.")
    parser.add_argument("-n", "--number", type=int, default=24,
                        help="Number of wells to track, default is 24")
    parser.add_argument("-i", "--save_track_image", action="store_true",
                        help="Save images of tracked paths.")
    parser.add_argument("-m", "--manual_crop", action="store_true",
                        help="Manually select the wells to be tracked.")
    parser.add_argument("-s", "--save_track", action="store_true",
                        help="Save track points to file.")
    parser.add_argument("--median", action="store_true",
                        help="Use median intensity projection for segmentation.")
    # parse arguments from command line
    args = parser.parse_args()
    return args


def isinside(center, radius, point) -> bool:
    dist = distance([center, point.coords])
    if dist > radius:
        return False
    else:
        return True


def split_tracks(mask, pts):
    center = mask[0]
    radius = mask[1]
    tracks_outer = []
    tracks_inner = []
    idx_o = -1
    idx_i = -1
    prev_o = None
    for pt in pts:
        if prev_o is None:
            if isinside(center, radius, pt):
                prev_o = False
                tracks_inner.append([pt])
                idx_i += 1
            else:
                prev_o = True
                tracks_outer.append([pt])
                idx_o += 1
        elif prev_o:
            if isinside(center, radius, pt):
                prev_o = False
                idx_i += 1
                tracks_inner.append([pt])
            else:
                tracks_outer[idx_o].append(pt)
        else:
            if isinside(center, radius, pt):
                tracks_inner[idx_i].append(pt)
            else:
                prev_o = True
                idx_o += 1
                tracks_outer.append([pt])
    return tracks_outer, tracks_inner


if __name__ == '__main__':
    start = datetime.now()
    main()
    end = datetime.now()
    print("\nExecuted in " + str(end - start))