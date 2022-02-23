# import the necessary packages
from __future__ import print_function
from tkinter.constants import INSERT, WORD
from PIL import Image
from PIL import ImageTk
import tkinter as tki
import threading
import datetime
import imutils
from tensorflow.keras.models import model_from_json
import cv2
import os
import numpy as np
from tkinter import messagebox
from tkinter import Text
from tensorflow.keras.preprocessing import image
import tkinter.font as tkFont
import threading
import xml.etree.ElementTree as ET
from time import sleep

# load model
model = model_from_json(open("6R8.json", "r").read())
# load weights
model.load_weights("6R8.h5")
face_haar_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


class VisionAutocorrectApp:
    def __init__(self, vs):
        self.clearPrevPics()
        self.font = 16
        self.vs = vs
        self.outputPath = "output"
        self.frame = None
        self.thread = None
        self.thread2 = None
        self.stopEvent = None
        # initialize the root window and image panel
        self.root = tki.Tk()
        self.panel = None
        self.height = 20
        self.setZeros()
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()
        self.thread2 = threading.Thread(target=self.scheduleTaskSnap, args=())
        self.thread2.start()
        # set a callback to handle when the window is closed
        self.root.wm_title("Vision Autocorrect")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        self.fontStyle = tkFont.Font(family="Lucida Grande", size=9)
        self.backcolor = "#ff0000"
        self.frontcolor = "#00ff00"

        self.labelExample = Text(
            self.root,
            font=self.fontStyle,
            width=150,
            height=20,
            wrap=WORD,
            padx=10,
            bg=self.backcolor,
            fg=self.frontcolor,
            pady=10,
        )
        self.labelExample.insert(
            INSERT,
            "Strange Bedfellows!” lamented the title of a recent letter to Museum News, in which a certain Harriet Sherman excoriated the National Gallery of Art in Washington for its handling of tickets to the much-ballyhooed “Van Gogh’s van Goghs” exhibit. A huge proportion of the 200, 000 free tickets were snatched up by the opportunists in the dead of winter, who then scalped those tickets at $85 apiece to less hardy connoiseurs.Yet, Sherman’s bedfellows are far from strange. Art, despite its religious and magical origins, very soon became a commercial venture. From bourgeois patrons funding art they barely understood in order to share their protegee’s prestige, to museum curators stage-managing the cult of artists in order to enhance the market value of museum holdings, entrepreneurs have found validation and profit in big-name art. Speculators, thieves, and promoters long ago created and fed a market where cultural icons could be traded like commodities.",
        )
        self.labelExample.pack(side=tki.BOTTOM)

    def clearPrevPics(self):
        filepath = "output"
        for root, dirs, files in os.walk(filepath):
            for file in files:
                print(file)
                os.remove(os.path.join(root, file))

    def scheduleTaskSnap(self):
        while not self.stopEvent.is_set():
            try:
                sleep(2)
                self.classifyImage()
            except RuntimeError as e:
                print("[INFO] caught a RuntimeError")

    def increase_label_font(self):
        fontsize = self.fontStyle["size"]
        self.fontStyle.configure(size=fontsize + 1)

    def change_colors(self):
        self.backcolor = "#ffffff"
        self.frontcolor = "#000000"
        self.labelExample.config(bg=self.backcolor, fg=self.frontcolor)

    def videoLoop(self):
        try:
            while not self.stopEvent.is_set():
                self.frame = self.vs.read()
                self.frame = imutils.resize(self.frame, height=700)
                image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
                image = ImageTk.PhotoImage(image)
                # if the panel is not None, we need to initialize it
                if self.panel is None:
                    self.panel = tki.Label(image=image)
                    self.panel.image = image
                    self.panel.pack(
                        side="left", padx=10, pady=10, expand="yes", fill="both"
                    )
                else:
                    self.panel.configure(image=image)
                    self.panel.image = image
        except RuntimeError as e:
            print("[INFO] caught a RuntimeError")

    def takeSnapshot(self):
        # grab the current timestamp and use it to construct the
        # output path
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        p = os.path.sep.join((self.outputPath, filename))
        # save the file
        cv2.imwrite(p, self.frame.copy())
        print("[INFO] saved {}".format(filename))
        file = "./output/" + filename
        return str(file)

    def classifyImage(self):
        try:
            file = self.takeSnapshot()
            image_test = cv2.imread(str(file))
            gray_img = cv2.cvtColor(image_test, cv2.COLOR_BGR2GRAY)
            faces_detected = face_haar_cascade.detectMultiScale(gray_img)
            for (x, y, w, h) in faces_detected:
                roi_gray = gray_img[
                    y : y + w, x : x + h
                ]  # cropping region of interest i.e. face area from  image
                roi_gray = cv2.resize(roi_gray, (48, 48))
                img_pixels = image.img_to_array(roi_gray)
                img_pixels = np.expand_dims(img_pixels, axis=0)
                img_pixels /= 255
                predictions = model.predict(img_pixels)
                # print(predictions)
                # find max indexed array
                max_index = np.argmax(predictions[0])
                # print(max_index)
                emotions = ("None", "Fatigue", "Glare", "Normal", "Squint")
                predicted_emotion = emotions[max_index]
                print(predicted_emotion)
                # print(predicted_emotion)
                self.parseRules(predicted_emotion)
                self.remove_img(file)
                return True
            self.remove_img(file)
        except Exception as e:
            messagebox.showwarning(
                "Error", "An error occured when classifying" + str(e)
            )

    def remove_img(self, img_name):
        os.remove(img_name)
        # check if file exists or not
        if os.path.exists(img_name) is False:
            # file did not exists
            return True

    def parseRules(self, category):
        tree = ET.parse("rules.xml")
        root = tree.getroot()
        for child in root:
            if child.attrib["category"] == category:
                if str(child[2].text) == str(int(child[0].text) - 1):
                    answer = messagebox.askyesno(
                        title=child.attrib["category"], message=child[1].text
                    )
                    if answer:
                        if category == "Fatigue":
                            self.onClose()
                        else:
                            self.increase_label_font()
                            if self.backcolor != "#ffffff":
                                self.change_colors()
                                messagebox.showinfo(
                                    title="Colors Changed",
                                    message="We have adjusted the colors for a better viewing experience",
                                )
                    child[2].text = str(0)
                else:
                    child[2].text = str(int(child[2].text) + 1)
        tree.write("rules.xml")

    def setZeros(self):
        tree = ET.parse("rules.xml")
        root = tree.getroot()
        for child in root:
            child[2].text = str(0)
        tree.write("rules.xml")

    def onClose(self):
        print("[INFO] closing...")
        self.stopEvent.set()
        self.vs.stop()
        self.root.quit()
