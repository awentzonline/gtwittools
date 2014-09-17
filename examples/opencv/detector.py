import os

import cv2


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
eye_classifier = cv2.CascadeClassifier(
    os.path.join(DATA_DIR, 'haarcascade_frontalface_default.xml'))
face_classifier = cv2.CascadeClassifier(
    os.path.join(DATA_DIR, 'haarcascade_frontalface_default.xml'))


def detect_in_files(fn, filename_q, classifiers={}):
    for filename in filename_q:
        img = cv2.imread(filename)
        features = {}
        for name, classifier in classifiers.items():
            rects = classifier.detectMultiScale(img)
            features[name] = rects
        fn(img, features, filename)
