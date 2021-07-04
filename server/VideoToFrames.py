import tkinter as tk
import cv2
from PIL import Image, ImageTk
import os
import shutil
import glob
import csv


VIDEO_PATH = "output.avi"
FRAMES_PATH = "Frames/"
CSV_PATH = "gestures.csv"
IMG_FORMAT = ".png"


class FramesCreator:

    def __init__(self, frames_path):
        self.cap = cv2.VideoCapture(VIDEO_PATH)
        self._num_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._frames_path = frames_path

        self.images_path = []

        # region tkinter
        self.root = tk.Tk()
        self.root.title("A simple GUI")

        self.root.bind("<Up>", lambda *args: self.next())
        self.root.bind("<Down>", lambda *args: self.prev())

        self.curr_frame_indx = 1
        self.curr_frame_indx_strvar = tk.StringVar()
        self.curr_frame_indx_strvar.set(str(self.curr_frame_indx))

        self.main_frame = tk.Frame(self.root, height=700, width=700, bg="light blue")
        self.main_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        self.curr_frame_label = tk.Label(self.main_frame, textvariable=self.curr_frame_indx_strvar, bg="light blue")
        self.curr_frame_label.grid(row=0, column=0, pady=(0, 15))

        self.pic_label_entry = tk.Entry(self.main_frame)
        self.pic_label_entry.grid(row=1, column=0, columnspan=4)

        self.prev_button = tk.Button(self.main_frame, text="Previous", command=self.prev)
        self.prev_button.grid(row=2, column=0, columnspan=2, sticky="nw")

        self.next_button = tk.Button(self.main_frame, text="Next", command=self.next)
        self.next_button.grid(row=2, column=2, columnspan=2, sticky="ne")

        self.total_frames_label = tk.Label(self.main_frame, text=f"Total: {self._num_frames-1}", bg="light blue")
        self.total_frames_label.grid(row=3, column=0, sticky="nw", pady=(10, 0))

        self.frame_window()

        self.root.mainloop()
        # endregion

    def frame_window(self):
        # Toplevel object which will
        # be treated as a new window
        self.img_win = tk.Toplevel(self.root)

        # sets the title of the
        # Toplevel widget
        self.img_win.title("Frame")

        # sets the geometry of toplevel
        self.img_win.geometry("200x200")

        ret, self.frame = self.cap.read()

        self.imagetk = ImageTk.PhotoImage(image=Image.fromarray(self.frame))
        self.frame_label = tk.Label(self.img_win, image=self.imagetk)
        self.frame_label.pack()

    def prev(self):
        self.delete_img()

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.curr_frame_indx - 2)
        ret, self.frame = self.cap.read()

        if ret:
            self.update_counter()
            self.imagetk = ImageTk.PhotoImage(image=Image.fromarray(self.frame))  # create a new imagetk from the new frame
            self.frame_label.configure(image=self.imagetk)  # display the new imagetk

    def next(self):
        if self.pic_label_entry.get() == "":
            return

        if self.curr_frame_indx == self._num_frames - 1:
            return

        self.save_img()

        ret, self.frame = self.cap.read()

        if ret:
            self.update_counter()
            self.imagetk = ImageTk.PhotoImage(image=Image.fromarray(self.frame))  # create a new imagetk from the next frame
            self.frame_label.configure(image=self.imagetk)  # display the new imagetk

    def update_counter(self):
        self.curr_frame_indx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.curr_frame_indx_strvar.set(str(self.curr_frame_indx))

    def save_img(self):
        img_name = self._frames_path + self.curr_frame_indx_strvar.get() + '_' + self.pic_label_entry.get() + IMG_FORMAT
        cv2.imwrite(img_name, self.frame)
        self.images_path.append(img_name)

    def delete_img(self):
        indx = self.curr_frame_indx - 2

        if indx < 0:
            return

        if os.path.exists(self.images_path[indx]):
            os.remove(self.images_path[indx])
            self.images_path.pop()

        else:
            print(f"The file {self.images_path[indx]} does not exist. Can't delete.")


def get_all_frames(frames_path) -> list:
    return [f.split('\\')[1] for f in glob.glob(f"{frames_path}*")]


def get_label(full_name: str) -> str:
    return full_name.split('.')[0].split('_')[1]  # example: 104_Three.png -> Three


def create_csv_annotations(frames_path, csv_path):
    frames = get_all_frames(frames_path)

    all_rows = [[f, get_label(f)] for f in frames]

    with open(csv_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)


def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)

    else:
        if len(os.listdir(path)) != 0:  # dir not empty
            print("Please empty the directory:", path)
            exit(0)


def main():
    create_folder(FRAMES_PATH)
    FramesCreator(FRAMES_PATH)
    create_csv_annotations(FRAMES_PATH, CSV_PATH)


if __name__ == '__main__':
    main()
