import ast
import csv
import os
import pickle
import numpy as np
import cv2
from deepface.modules import detection, preprocessing
from tensorflow.tools.docs.doc_controls import header
from module.utils import cosine_distance
from model.classification_model import FacialRecognitionModel
from module import config, utils, database

face_model = FacialRecognitionModel()
model = face_model.get_embedding_model()

def DatabaseEmbedding(data_dir,model):
    embedding_dict = {}

    for img in os.listdir(data_dir):
        img_path = os.path.join(data_dir,img)
        img_name = img.split('.')[0]
        embedding_img, _ = utils.face_detect(img_path,model)
        embedding_dict[img_name] = embedding_img

    with open("db_named_embeddings.pkl", "wb") as f:
        pickle.dump(embedding_dict, f)

    print("✔️ Đã lưu embeddings thành công.")


def findPerson(img):
    min_distant = 1
    threshold = config.THRESHOLD
    id = None
    identity = None
    matched_embedding = None

    employees = database.read_employees()
    if not employees:
        print("Không có nhân viên nào trong cơ sở dữ liệu.")
        return None, "unknown", min_distant

    for employee in employees:
        embedding_img = np.load(employee[3])

        dist = cosine_distance(img, embedding_img)
        print("distance:", dist)
        if dist < min_distant:
            min_distant = dist
            identity = employee[1]
            id = employee[0]



    if min_distant <= threshold and identity is not None:
        return id,identity, min_distant
    else:
        return None,"unknown", min_distant

