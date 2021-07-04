import asyncio
from typing import Tuple, Union
import torch
import websockets
import numpy as np
import cv2
from torchvision import transforms
from CNN import Net


port = 34567
host = "192.168.1.32"

SIDE_LEN = 170

CONFIDENCE_THRESH = 1
MODEL_PATH = './gestures.pth'

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Resize(32),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ]
)


# region Global Variables
mog2: cv2.BackgroundSubtractorMOG2
net: Net
# endregion


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


def get_prediction(proc: np.ndarray) -> int:
    global net

    proc = cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR)
    proc = transform(proc)
    proc = proc.to(device)

    outputs = net(proc[None, ...])
    _, predicted = torch.max(outputs, 1)
    predicted = predicted.item()

    conf_lvl = torch.topk(outputs, 1)[0]
    # print(f'{conf_lvl.item()} : {predicted}')

    if conf_lvl > CONFIDENCE_THRESH and predicted != 5:
        return predicted
    else:
        return 0


async def echo(websocket, path):
    print("Connected")
    async for msg in websocket:
        if isinstance(msg, bytes):  # if the message is an image
            rect, proc = process_image(msg)
            pred = get_prediction(proc)
            print("Predicted:", pred, end='\n\n')
            cv2.imshow("rect", rect)
            cv2.imshow("proc", proc)
            await websocket.send(str(pred))

        if cv2.waitKey(1) & 0xFF == ord('q'):  # stop when pressing q
            exit(0)


def main():
    global mog2, net

    mog2 = cv2.createBackgroundSubtractorMOG2()

    # Initialize the neural net
    net = Net()
    net.to(device)
    net.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device(device)))

    start_server = websockets.serve(echo, host, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
