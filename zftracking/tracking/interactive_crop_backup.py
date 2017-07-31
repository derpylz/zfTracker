"""promts the user to crop or mask a image file"""

from operator import add

import numpy as np

import cv2


def get_radius(pts):
    """takes center and point on circumference and return radius"""
    x0 = pts[0][0]
    y0 = pts[0][1]
    x1 = pts[1][0]
    y1 = pts[1][1]
    r = int(np.math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2))
    return r


class Image:
    """class to crop and select mask regions for wells"""

    def __init__(self, path, prev_crop=False, prev_mask=False, scaling=2):
        self.path = path
        self.refPt = []
        self.cropping = False
        self.image = cv2.imread(self.path)
        self.clone = self.image.copy()
        # scaling for better usability
        self.scaling = scaling
        self.small = cv2.resize(self.image, None, fx=1 / self.scaling, fy=1 / self.scaling)
        self.small_clone = self.small.copy()
        self.height, self.width, self.channels = self.image.shape
        self.prev_crop = prev_crop
        self.prev_mask = prev_mask
        self.xy = []
        self.dxy = []

    def click2rect(self, event, x, y, flags, param):
        """creates rectangle from mouse input"""
        # gets mouse events from crop method
        if event == cv2.EVENT_LBUTTONDOWN:
            # on left mouse click, record starting point for cropping rectangle
            self.refPt = [(x, y)]
            # change cropping state to true
            self.cropping = True
        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            # display a rectangle from starting point to mouse position on mouse move
            # only when the user is currently holding left mouse button down
            # first clear the  image
            self.small = self.small_clone.copy()
            # draw the rectangle on the image
            cv2.rectangle(self.small,
                          self.refPt[0],
                          (x, y),
                          (0, 255, 0), 2)
            # show the image
            cv2.imshow("select crop area", self.small)
        elif event == cv2.EVENT_LBUTTONUP:
            # on left mouse button release, record end point for cropping rectangle
            self.refPt.append((x, y))
            # set cropping state back to false
            self.cropping = False
            # draw a rectangle for the selected crop region
            # clear the image
            self.small = self.small_clone.copy()
            # draw the rectangle on the image
            cv2.rectangle(self.small,
                          self.refPt[0],
                          self.refPt[1],
                          (0, 255, 0), 2)
            # show the image
            cv2.imshow("select crop area", self.small)

    def click2grid(self, event, x, y, flags, param):
        """creates rectangle from mouse input"""
        # gets mouse events from crop method
        if event == cv2.EVENT_LBUTTONDOWN:
            # on left mouse click, record starting point for cropping rectangle
            self.refPt = [(x, y)]
            # change cropping state to true
            self.cropping = True
        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            # display a grid from starting point to mouse position on mouse move
            # only when the user is currently holding left mouse button down
            # first clear the  image
            self.small = self.small_clone.copy()
            # draw the grid on the image
            x_size = x - self.refPt[0][0]
            x_grid_size = int(x_size / 6)
            y_size = y - self.refPt[0][1]
            y_grid_size = int(y_size / 4)
            box = [list(self.refPt[0]), [0, 0]]
            for i in range(4):
                for j in range(6):
                    box[1][0] = box[0][0] + x_grid_size
                    box[1][1] = box[0][1] + y_grid_size
                    cv2.rectangle(self.small, tuple(box[0]), tuple(box[1]), (255, 0, 0), 1)
                    box[0][0] = box[1][0]
                box[0][0] = self.refPt[0][0]
                box[0][1] += y_grid_size
            cv2.rectangle(self.small,
                          self.refPt[0],
                          (x, y),
                          (0, 255, 0), 2)
            # show the image
            cv2.imshow("select crop area", self.small)
        elif event == cv2.EVENT_LBUTTONUP:
            # on left mouse button release, record end point for cropping grid
            self.refPt.append((x, y))
            # set cropping state back to false
            self.cropping = False
            # draw a grid for the selected crop region
            # clear the image
            self.small = self.small_clone.copy()
            # draw the grid on the image
            x_size = x - self.refPt[0][0]
            x_grid_size = int(x_size / 6)
            y_size = y - self.refPt[0][1]
            y_grid_size = int(y_size / 4)
            box = [list(self.refPt[0]), [0, 0]]
            for i in range(4):
                for j in range(6):
                    box[1][0] = box[0][0] + x_grid_size
                    box[1][1] = box[0][1] + y_grid_size
                    cv2.rectangle(self.small, tuple(box[0]), tuple(box[1]), (255, 0, 0), 1)
                    box[0][0] = box[1][0]
                box[0][0] = self.refPt[0][0]
                box[0][1] += y_grid_size
            cv2.rectangle(self.small,
                          self.refPt[0],
                          self.refPt[1],
                          (0, 255, 0), 2)
            # show the image
            cv2.imshow("select crop area", self.small)

    def rect_from_crop(self):
        (width, height, x, y) = self.prev_crop.split(':')
        prev = [(int(int(x) / self.scaling), int(int(y) / self.scaling)),
                (int((int(x) + int(width)) / self.scaling), int((int(y) + int(height)) / self.scaling))]
        width = int(int(width) / self.scaling)
        dxy = (width, 0)
        self.refPt = [tuple(map(add, prev[0], dxy)), tuple(map(add, prev[1], dxy))]
        return prev

    def move_crop(self, event, x, y, flags, param):
        """creates rectangle from mouse input"""
        # gets mouse events from crop method
        if event == cv2.EVENT_LBUTTONDOWN:
            # on left mouse click, record starting point for movement
            self.xy = (x, y)
            # change cropping state to true
            self.cropping = True
        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            # display moved rectangle
            # only when the user is currently holding left mouse button down
            # first clear the  image
            self.small = self.small_clone.copy()
            self.dxy = (x - self.xy[0], y - self.xy[1])
            # draw the rectangle on the image
            cv2.rectangle(self.small,
                          tuple(map(add, self.refPt[0], self.dxy)),
                          tuple(map(add, self.refPt[1], self.dxy)),
                          (0, 255, 0), 2)
            # show the image
            cv2.imshow("select crop area", self.small)
        elif event == cv2.EVENT_LBUTTONUP:
            # on left mouse button release, record end point for cropping rectangle
            self.refPt = (tuple(map(add, self.refPt[0], self.dxy)),
                          tuple(map(add, self.refPt[1], self.dxy)))
            # set cropping state back to false
            self.cropping = False
            # draw a rectangle for the selected crop region
            # clear the image
            self.small = self.small_clone.copy()
            # draw the rectangle on the image
            cv2.rectangle(self.small,
                          self.refPt[0],
                          self.refPt[1],
                          (0, 255, 0), 2)
            # show the image
            cv2.imshow("select crop area", self.small)

    def click2circle(self, event, x, y, flags, param):
        """creates circle from mouse input"""
        # gets mouse events from mask method
        if event == cv2.EVENT_LBUTTONDOWN:
            # on left mouse click, record center point for masking circle
            self.refPt = [(x, y)]
            # set cropping state to true
            self.cropping = True
            # draw a marker on the picture, where user placed the center point
            cv2.drawMarker(self.image,
                           self.refPt[0],
                           (0, 255, 0))
            # show image
            cv2.imshow("select inner circle", self.image)
        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            # display a circle with selected center point to mouse position on mouse move
            # only when the user is currently holding left mouse button down
            # clear the  image
            self.image = self.clone.copy()
            # get radius from center point and point on circumference
            radius = get_radius((self.refPt[0], (x, y)))
            # redraw the center marker
            cv2.drawMarker(self.image,
                           self.refPt[0],
                           (0, 255, 0))
            # draw the circle
            cv2.circle(self.image,
                       self.refPt[0],
                       radius,
                       (0, 255, 0), 2)
            # show image
            cv2.imshow("select inner circle", self.image)
        elif event == cv2.EVENT_LBUTTONUP:
            # on left mouse button release, record point on circumference for masking circle
            self.refPt.append((x, y))
            # set cropping state back to false
            self.cropping = False
            # get radius from center point and point on circumference
            radius = get_radius(self.refPt)
            # draw the circle
            cv2.circle(self.image,
                       self.refPt[0],
                       radius,
                       (0, 255, 0), 2)
            # show the image
            cv2.imshow("select inner circle", self.image)

    def move_mask(self, event, x, y, flags, param):
        """creates rectangle from mouse input"""
        # gets mouse events from mask method
        if event == cv2.EVENT_LBUTTONDOWN:
            # on left mouse click, record starting point for movement
            self.xy = (x, y)
            # change cropping state to true
            self.cropping = True
        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            # move the previous circle
            self.image = self.clone.copy()
            self.dxy = (x - self.xy[0], y - self.xy[1])
            # draw the circle on the image
            cv2.circle(self.image,
                       tuple(map(add, self.refPt[0], self.dxy)),
                       self.refPt[1],
                       (0, 255, 0), 2)
            # draw a marker for the center point
            cv2.drawMarker(self.image,
                           tuple(map(add, self.refPt[0], self.dxy)),
                           (0, 255, 0))
            # show the image
            cv2.imshow("select inner circle", self.image)
        elif event == cv2.EVENT_LBUTTONUP:
            # on left mouse button release, record end point for movement
            self.refPt = (tuple(map(add, self.refPt[0], self.dxy)),
                          self.refPt[1])
            # set cropping state back to false
            self.cropping = False
            # draw a circle for the selected crop region
            # clear the image
            self.image = self.clone.copy()
            # draw the circle on the image
            cv2.circle(self.image,
                       self.refPt[0],
                       self.refPt[1],
                       (0, 255, 0), 2)
            # draw a marker for the center point
            cv2.drawMarker(self.image,
                           tuple(map(add, self.refPt[0], self.dxy)),
                           (0, 255, 0))
            # show the image
            cv2.imshow("select inner circle", self.image)

    def click2line(self, event, x, y, flags, param):
        """creates rectangle from mouse input"""
        # gets mouse events from border method
        if event == cv2.EVENT_LBUTTONDOWN:
            # on left mouse click, record starting point for the line
            self.refPt = [(x, y)]
            # change cropping state to true
            self.cropping = True
        elif event == cv2.EVENT_MOUSEMOVE and self.cropping:
            # display a line from starting point to mouse position on mouse move
            # only when the user is currently holding left mouse button down
            # first clear the  image
            self.small = self.small_clone.copy()
            # draw the line on the image
            cv2.line(self.small,
                     (0, self.refPt[0][1]),
                     (self.width, y),
                     (0, 255, 0), 2)
            # show the image
            cv2.imshow("draw border", self.small)
        elif event == cv2.EVENT_LBUTTONUP:
            # on left mouse button release, record end point for the line
            self.refPt.append((x, y))
            # set cropping state back to false
            self.cropping = False
            # clear the image
            self.small = self.small_clone.copy()
            # draw the line
            cv2.line(self.small,
                     (0, self.refPt[0][1]),
                     (self.width, self.refPt[1][1]),
                     (0, 255, 0), 2)
            # show the image
            cv2.imshow("draw border", self.small)

    def get_crop_coords(self, pts):
        """translates reference points to crop window as needed by ffmpeg"""
        width = 0
        height = 0
        x = 0
        y = 0
        if pts[0][0] < pts[1][0] and pts[0][1] < pts[1][1]:
            # first point is upper left
            pt1 = pts[0]
            pt2 = pts[1]
            x = str(pt1[0] * self.scaling)
            y = str(pt1[1] * self.scaling)
            width = str(pt2[0] * self.scaling - pt1[0] * self.scaling)
            height = str(pt2[1] * self.scaling - pt1[1] * self.scaling)
        elif pts[0][0] > pts[1][0] and pts[0][1] > pts[1][1]:
            # second point is upper left
            pt1 = pts[1]
            pt2 = pts[0]
            x = str(pt1[0] * self.scaling)
            y = str(pt1[1] * self.scaling)
            width = str(pt2[0] * self.scaling - pt1[0] * self.scaling)
            height = str(pt2[1] * self.scaling - pt1[1] * self.scaling)
        elif pts[0][0] < pts[1][0] and pts[0][1] > pts[1][1]:
            # first point is lower left
            pt1 = pts[0]
            pt2 = pts[1]
            x = str(pt1[0] * self.scaling)
            y = str(pt2[1] * self.scaling)
            width = str(pt2[0] * self.scaling - pt1[0] * self.scaling)
            height = str(pt1[1] * self.scaling - pt2[1] * self.scaling)
        elif pts[0][0] > pts[1][0] and pts[0][1] < pts[1][1]:
            # second point is lower left
            pt1 = pts[0]
            pt2 = pts[1]
            x = str(pt2[0] * self.scaling)
            y = str(pt1[1] * self.scaling)
            width = str(pt1[0] * self.scaling - pt2[0] * self.scaling)
            height = str(pt2[1] * self.scaling - pt1[1] * self.scaling)
        return width + ':' + height + ':' + x + ':' + y

    def crop(self):
        """lets the user create a rectangle and return the coordinates of the crop"""
        # initiate a window
        cv2.namedWindow("select crop area")

        if not self.prev_crop:
            # redirect mouse events to click2rect method
            cv2.setMouseCallback("select crop area", self.click2rect)
            # loop until crop is done (c gets pressed)
            while True:
                # show the image
                cv2.imshow("select crop area", self.small)
                # wait for key press
                key = cv2.waitKey(1) & 0xFF
                # if r is pressed, reset the cropping rectangle
                if key == ord("r"):
                    self.small = self.small_clone.copy()
                # if c is pressed, close the window
                elif key == ord("c"):
                    cv2.destroyWindow("select crop area")
                    cv2.waitKey(1) & 0xFF
                    break
        else:
            # redirect mouse events to move_crop method
            cv2.setMouseCallback("select crop area", self.move_crop)
            # create previous and new rectangle
            prev = self.rect_from_crop()
            cv2.rectangle(self.small,
                          prev[0],
                          prev[1],
                          (0, 0, 128), 2)
            cv2.rectangle(self.small,
                          self.refPt[0],
                          self.refPt[1],
                          (0, 255, 0), 2)
            # loop until crop is done (c gets pressed)
            while True:
                # show the image
                cv2.imshow("select crop area", self.small)
                # wait for key press
                key = cv2.waitKey(1) & 0xFF
                # if r is pressed, reset the cropping rectangle
                if key == ord("r"):
                    self.small = self.small_clone.copy()
                    self.prev_crop = False
                    cv2.setMouseCallback("select crop area", self.click2rect)
                # if c is pressed, close the window
                elif key == ord("c"):
                    cv2.destroyWindow("select crop area")
                    cv2.waitKey(1) & 0xFF
                    break
        # if cropping was successful,
        # refPt will have the two defining corner points for the rectangle
        if len(self.refPt) == 2:
            # get the crop coordinates in a ffmpeg compliant format
            crop = self.get_crop_coords(self.refPt)
            # close all windows and return the coordinates
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF
            return crop
        else:
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF

    def auto_crop(self):
        """lets the user create a rectangle around all wells to be tracked"""
        # initiate a window
        cv2.namedWindow("select crop area")

        if not self.prev_crop:
            # redirect mouse events to click2grid method
            cv2.setMouseCallback("select crop area", self.click2grid)
            # loop until crop is done (c gets pressed)
            while True:
                # show the image
                cv2.imshow("select crop area", self.small)
                # wait for key press
                key = cv2.waitKey(1) & 0xFF
                # if r is pressed, reset the cropping rectangle
                if key == ord("r"):
                    self.small = self.small_clone.copy()
                # if c is pressed, close the window
                elif key == ord("c"):
                    cv2.destroyWindow("select crop area")
                    cv2.waitKey(1) & 0xFF
                    break
        # if cropping was successful,
        # refPt will have the two defining corner points for the rectangle
        if len(self.refPt) == 2:
            # get the crop coordinates in a ffmpeg compliant format
            # close all windows and return the coordinates
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF
            crops = []
            x_size = self.refPt[1][0] - self.refPt[0][0]
            x_grid_size = int(x_size / 6)
            y_size = self.refPt[1][1] - self.refPt[0][1]
            y_grid_size = int(y_size / 4)
            box = [list(self.refPt[0]), [0, 0]]
            for i in range(4):
                for j in range(6):
                    box[1][0] = box[0][0] + x_grid_size
                    box[1][1] = box[0][1] + y_grid_size
                    crops.append(self.get_crop_coords(box))
                    box[0][0] = box[1][0]
                box[0][0] = self.refPt[0][0]
                box[0][1] += y_grid_size

            return crops
        else:
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF

    def mask(self, mask_path):
        """lets the user create a circle and saves an image with the mask"""
        # initiate a window
        cv2.namedWindow("select inner circle")
        if not self.prev_mask:
            # redirect mouse events to click2rect method
            cv2.setMouseCallback("select inner circle", self.click2circle)
            # loop until masking is done (c gets pressed)
            while True:
                # show image
                cv2.imshow("select inner circle", self.image)
                # wait for key press
                key = cv2.waitKey(1) & 0xFF
                # if r is pressed, reset the cropping rectangle
                if key == ord("r"):
                    self.image = self.clone.copy()
                # if c is pressed, close the window
                elif key == ord("c"):
                    cv2.destroyWindow("select inner circle")
                    cv2.waitKey(1) & 0xFF
                    break
        else:
            # redirect mouse events to move_mask method
            cv2.setMouseCallback("select inner circle", self.move_mask)
            # create circle where previous mask was
            cv2.circle(self.image,
                       self.prev_mask[0],
                       self.prev_mask[1],
                       (0, 255, 255), 2)
            self.refPt = self.prev_mask
            # loop until masking is done (c gets pressed)
            while True:
                # show the image
                cv2.imshow("select inner circle", self.image)
                # wait for key press
                key = cv2.waitKey(1) & 0xFF
                # if r is pressed, reset the cropping rectangle
                if key == ord("r"):
                    self.image = self.clone.copy()
                    self.prev_mask = False
                    cv2.setMouseCallback("select inner circle", self.click2circle)
                # if c is pressed, close the window
                elif key == ord("c"):
                    cv2.destroyWindow("select inner circle")
                    cv2.waitKey(1) & 0xFF
                    break
        # if cropping was successful,
        # refPt will have the the center and a point on the circumference of the masking circle
        if len(self.refPt) == 2:
            # create a black mask with the same dimensions of the image
            mask = np.zeros((self.width, self.height), np.uint8)
            # draw a circle filled in white on the mask
            if type(self.refPt[1]) == tuple:
                cv2.circle(mask,
                           self.refPt[0],
                           get_radius(self.refPt),
                           (255, 255, 255), -1)
                # write the mask to a file
                cv2.imwrite(mask_path, mask)
                # close all windows
                cv2.destroyAllWindows()
                cv2.waitKey(1) & 0xFF
                return [self.refPt[0], get_radius(self.refPt)]
            else:
                cv2.circle(mask,
                           self.refPt[0],
                           self.refPt[1],
                           (255, 255, 255), -1)
                # write the mask to a file
                cv2.imwrite(mask_path, mask)
                # close all windows
                cv2.destroyAllWindows()
                cv2.waitKey(1) & 0xFF
                return [self.refPt[0], self.refPt[1]]
        else:
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF

    def set_border(self):
        """lets the user create a rectangle around all wells to be tracked"""
        # initiate a window
        cv2.namedWindow("draw border")
        # redirect mouse events to click2line method
        cv2.setMouseCallback("draw border", self.click2line)
        # loop until crop is done (c gets pressed)
        while True:
            # show the image
            cv2.imshow("draw border", self.small)
            # wait for key press
            key = cv2.waitKey(1) & 0xFF
            # if r is pressed, reset the cropping rectangle
            if key == ord("r"):
                self.small = self.small_clone.copy()
            # if c is pressed, close the window
            elif key == ord("c"):
                cv2.destroyWindow("draw border")
                cv2.waitKey(1) & 0xFF
                break
        # if cropping was successful,
        # refPt will have the two defining end points for the border
        if len(self.refPt) == 2:
            # close all windows and return the coordinates
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF

            return self.refPt
        else:
            cv2.destroyAllWindows()
            cv2.waitKey(1) & 0xFF
