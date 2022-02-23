# import the necessary packages
from app import VisionAutocorrectApp
from imutils.video import VideoStream

print("[INFO] warming up camera...")
vs = VideoStream().start()
# time.sleep(2.0)
# start the app
pba = VisionAutocorrectApp(vs)
pba.root.mainloop()


# NOTE  python cam.py
