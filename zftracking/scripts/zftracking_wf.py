#!python
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 2016

@author: Nils Jonathan Trost

Script that tracks larvae in circular arenas.

Needs ffmpeg and FIJI to run.
"""

import argparse
import errno
import os
import shutil
from datetime import datetime
from threading import Thread

from zftracking.external.runffmpeg import Ffmpeg
from zftracking.external.runfiji import ImageJMacro
from zftracking.tracking.analyze_tracks import Analysis
from zftracking.tracking.cv_tracking import Video
from zftracking.tracking.interactive_crop_backup import Image


def silent_remove(filename):
    """removes file without error on non existing file"""
    try:
        os.remove(filename)
    except OSError as err:
        if err.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise                    # re-raise exception if a different error occurred


def crop_and_mask(infile, mask_path, temp_dir, thumb, prev_crop=False, prev_mask=False):
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
    mask = image.mask(mask_path)
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
    start = datetime.now()
    parser = argparse.ArgumentParser(description="Tracks larvae for thigmotaxis experiment")
    # add options for argument parser
    parser.add_argument("in_path",
                        help="Path to the video.")
    parser.add_argument("out_path",
                        help="Directory for results. Should be empty.")
    parser.add_argument("-x", "--keep_temp", action="store_true",
                        help="Keep temporary folder after execution.")
    parser.add_argument("-t", "--only_tracking", action="store_true",
                        help="Only perform tracking step.")
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
    parser.add_argument("-c", "--cpu", type=int, default=1,
                        help="Set number of threads for multi core machines.")
    parser.add_argument("--big", action="store_true",
                        help="Reduces memory usage for very large video files (time intensive, not recommended).")

    # parse arguments from command line
    args = parser.parse_args()
    # get all file names and directories ready
    infile = os.path.abspath(args.in_path)
    video_name = os.path.basename(infile)
    video_name_base = os.path.splitext(video_name)[0]
    out_dir = os.path.abspath(args.out_path)
    with open(os.path.join(out_dir, 'stats.txt'), 'w') as out:
        out.write('well\t')
        out.write('time in outer region\t')
        out.write('distance in outer region\t')
        out.write('time in inner region\t')
        out.write(' distance in inner region\t')
        out.write(' % of time in outer region\t')
        out.write(' % of distance in outer region\n')
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
    mask_paths = []
    start_frame = False
    end_frame = False
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        mask_paths.append(os.path.join(temp_dir, "mask.tiff"))

    crops = []
    if not args.only_tracking:
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
                mask_path = mask_paths[i]
                silent_remove(os.path.join(temp_dir, "crop.tiff"))
                ffmpeg = Ffmpeg(infile, os.path.join(temp_dir, "crop.tiff"))
                ffmpeg.pix_fmt = "gray8"
                ffmpeg.vframes = "1"
                ffmpeg.ss = "150"
                ffmpeg.filter = "crop=" + crop
                ffmpeg.run()
                image = Image(os.path.join(temp_dir, "crop.tiff"), prev_mask=prev_mask)
                prev_mask = image.mask(mask_path)
        else:
            m = (0, 0)
            for i in range(len(temp_dirs)):
                # prepare cropping and masking
                temp_dir = temp_dirs[i]
                mask_path = mask_paths[i]
                if len(crops) == 0:
                    c, m = crop_and_mask(infile, mask_path, temp_dir, thumb)
                    crops.append(c)
                else:
                    c, m = crop_and_mask(infile, mask_path, temp_dir, thumb, crops[-1], m)
                    crops.append(c)
        i = 0
        while i < len(temp_dirs):
            threads = {}
            for thread in range(args.cpu):
                try:
                    temp_dir = temp_dirs[i]
                    crop = crops[i]
                    # prepare the video for segmentation
                    threads[thread] = Thread(target=prepare_vid,
                                             args=[cropped_video, infile, temp_dir, crop])
                    threads[thread].start()
                    i += 1
                except IndexError:
                    break
            for thread in threads:
                threads[thread].join()
            while not start_frame:
                try:
                    start_frame = int(input("First frame to keep: "))
                except ValueError:
                    start_frame = False
            while not end_frame:
                try:
                    end_frame = int(input("Last frame to keep: ")) + 1
                except ValueError:
                    end_frame = False
        for i in range(len(temp_dirs)):
            # segment the video
            temp_dir = temp_dirs[i]
            mask_path = mask_paths[i]
            seg_path = seg_paths[i]
            # run the segmentation macro
            if args.median:
                fiji = ImageJMacro("segmentation_median")
            else:
                fiji = ImageJMacro("segmentation")
            fiji.run([temp_dir + cropped_video, str(start_frame),
                      str(end_frame), seg_path, mask_path])

    for i in range(len(seg_paths)):
        # track outer region
        seg_path = seg_paths[i]
        if args.big:
            outer = Video(seg_path + "_outer.tiff", big=True)
        else:
            outer = Video(seg_path + "_outer.tiff")
        outer_tracks = outer.track()
        del outer
        # track inner region
        if args.big:
            inner = Video(seg_path + "_inner.tiff", big=True)
        else:
            inner = Video(seg_path + "_inner.tiff")
        inner_tracks = inner.track()
        del inner
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
        for i in range(args.number):
            silent_remove(os.path.join(out_dir,
                                       "SEG_" + str(i) + '_' + video_name_base + "_outer.tiff"))
            silent_remove(os.path.join(out_dir,
                                       "SEG_" + str(i) + '_' + video_name_base + "_inner.tiff"))

    end = datetime.now()
    print("Executed in " + str(end-start))


if __name__ == '__main__':
    main()
