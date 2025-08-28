import cv2
from deepface.modules import detection, preprocessing
from gtts import gTTS
import pygame
import time
import os
import numpy as np

def bbox_area_process(bbox):
    return bbox['w'] * bbox['h']


def cosine_distance(vec1, vec2):
    """
    Tính khoảng cách cosine giữa 2 vector
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    # Tính cos similarity
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    cosine_similarity = dot / (norm1 * norm2)

    # Khoảng cách cosine = 1 - độ tương đồng cosine
    return 1 - cosine_similarity

def distance_to_similarity(distance, min_d=0.15, max_d=0.36):
    if distance > max_d:
        return 0
    elif distance < min_d:
        return 100
    else:
        return round(100 * (1 - (distance - min_d) / (max_d - min_d)), 2)

def face_filter(faces):
    face_img = None
    face_bb = None
    largest_bbox = 0
    for face in faces:
        region_dict = {
            "x": face.facial_area.x,
            "y": face.facial_area.y,
            "w": face.facial_area.w,
            "h": face.facial_area.h
        }
        bbox_area = bbox_area_process(region_dict)
        if bbox_area > largest_bbox:
            largest_bbox = bbox_area
            face_img = face.img
            face_bb = face.facial_area

    return face_img, face_bb

def face_detect(path,embedding_model):
    face_img = None
    face_bb = None
    largest_bbox = 0
    if isinstance(path, str):
        img = cv2.imread(path)
    else:
        img = path

    faces = detection.detect_faces(detector_backend="mtcnn", img=img)
    if not faces:
        return None, None

    # get the largest bbox of face

    face_img, face_bb = face_filter(faces)

    # face_img = faces[0].img
    # face_bb = faces[0].facial_area  # dict với x, y, w, h
    face_img = preprocessing.resize_image(face_img,(224,224))
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

# if __name__ == '__main__':
    # bbox = {'x': 100, 'y': 50, 'w': 150, 'h': 200}
    # area = bbox_area_process(bbox)
    # print("Area of bounding box:", area)