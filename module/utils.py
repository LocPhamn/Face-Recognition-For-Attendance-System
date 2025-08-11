import cv2
from deepface.modules import detection, preprocessing
from gtts import gTTS
import pygame
import time
import os

def distance_to_similarity(distance, min_d=0.2, max_d=0.8):
    if distance > max_d:
        return 0
    elif distance < min_d:
        return 100
    else:
        return round(100 * (1 - (distance - min_d) / (max_d - min_d)), 2)

def preprocess(path,embedding_model):
    if isinstance(path, str):
        img = cv2.imread(path)
    else:
        img = path

    faces = detection.detect_faces(detector_backend="mtcnn", img=img)
    if not faces:
        return None, None

    face_img = faces[0].img
    face_img = preprocessing.resize_image(face_img,(224,224))
    face_bb = faces[0].facial_area  # dict với x, y, w, h
    embedding_img = embedding_model.predict(face_img)[0]
    return embedding_img, face_bb

def check_face(path,embedding_model):
    if isinstance(path, str):
        img = cv2.imread(path)
    else:
        img = path

    faces = detection.detect_faces(detector_backend="mtcnn", img=img)
    if not faces:
        return None, None

    face_img = faces[0].img
    face_img = preprocessing.resize_image(face_img,(224,224))
    face_bb = faces[0].facial_area  # dict với x, y, w, h
    embedding_img = embedding_model.predict(face_img)[0]
    return embedding_img, face_bb

def speak_vie(text):
    tts = gTTS(text=text, lang='vi')
    filename = "success_vi.mp3"
    tts.save(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.unload()
    pygame.mixer.quit()
    os.remove(filename)