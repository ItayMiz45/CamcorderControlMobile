import asyncio
from typing import Tuple, Union
import numpy as np
import cv2
import os
from tkinter import messagebox as mb
import threading
import websockets


VIDEO_PATH = "output.avi"
TMP_VIDEO_PATH = "tmp.avi"

SIDE_LEN = 170

port = 34567
host = "192.168.1.32"

# region Global Variables
mog2: cv2.BackgroundSubtractorMOG2
out: cv2.VideoWriter
input_thread: threading.Thread
# endregion


def clean_vids():
    if os.path.exists(TMP_VIDEO_PATH) and os.path.exists(VIDEO_PATH):
        os.remove(VIDEO_PATH)  # last video
        os.rename(TMP_VIDEO_PATH, VIDEO_PATH)


# Copy video from <VIDEO_PATH> to <TMP_VIDEO_PATH>
def copy_video():
    cap = cv2.VideoCapture(VIDEO_PATH)
    out = cv2.VideoWriter(TMP_VIDEO_PATH, cv2.VideoWriter_fourcc(*"DIVX"), 20, (SIDE_LEN, SIDE_LEN), False)

    # keep reading while the VideoCapture is open
    while cap.isOpened():
        good_read, frame = cap.read()
        if not good_read:  # stop if there is a problem reading
            break

        # convert the bgr image to grayscale, and then make it a binary image (black & white) using a threshold
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh, frame = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # finally, write the binary image to the output video
        out.write(frame)

    # return the copied video
    return out


start_capture = False


def get_user_input():
    global start_capture

    mb.showinfo("Start Capturing", "Press OK to start capturing video")

    start_capture = True


def process_image(image: bytes) -> Union[Tuple[np.ndarray, np.ndarray], None]:
    global mog2

    arr = np.array(list(image))
    arr = arr.reshape(240, 320)
    img = arr.astype(np.uint8)
    # img = np.flip(img)

    start_point = (240//2, 30)
    end_point = tuple([x+SIDE_LEN for x in start_point])

    img_with_rect = cv2.rectangle(img, start_point, end_point, color=255)

    # define region of interest (the rectangle)
    roi = img[start_point[1]:end_point[1], start_point[0]:end_point[0]]

    # apply the background subtractor on the roi to create a grayscale mask
    mog_mask = mog2.apply(roi)

    # dilate the image, blur it, and make it black and white, to reduce noise
    kernel = np.ones((3, 3))
    dilated = cv2.dilate(mog_mask, kernel, iterations=6)
    blurred = cv2.GaussianBlur(dilated, (5, 5), 0)
    ret, thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY)

    im_shape = thresh.shape
    filled = thresh.copy()
    cv2.line(filled, (0, im_shape[1]), (im_shape[0], im_shape[1]), (255, 255, 255), 25)
    contours, hierarchy = cv2.findContours(filled, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        print("Len is 0, returning")
        return

    cnt = [max(contours, key=cv2.contourArea)]
    cv2.drawContours(filled, cnt, -1, (255, 255, 255), cv2.FILLED)
    cv2.line(filled, (0, im_shape[1]), (im_shape[0], im_shape[1]), (0, 0, 0), 25)

    return img_with_rect, filled


async def server(websocket, path):
    global out, input_thread, start_capture

    print("Connected")
    async for msg in websocket:
        if isinstance(msg, bytes):  # if the message is an image
            rect, proc = process_image(msg)
            cv2.imshow("rect", rect)
            cv2.imshow("proc", proc)

            if start_capture:
                out.write(proc)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # stop when pressing q
            out.release()
            cv2.destroyAllWindows()
            input_thread.join()
            clean_vids()

            exit(0)


def main():
    global mog2, out, input_thread

    if os.path.exists(VIDEO_PATH):
        print("Copying video...")
        out = copy_video()
        print("Done")
    else:
        out = cv2.VideoWriter(VIDEO_PATH, cv2.VideoWriter_fourcc(*"DIVX"), 20, (SIDE_LEN, SIDE_LEN), False)

    mog2 = cv2.createBackgroundSubtractorMOG2()

    input_thread = threading.Thread(target=get_user_input)
    input_thread.start()

    start_server = websockets.serve(server, host, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
