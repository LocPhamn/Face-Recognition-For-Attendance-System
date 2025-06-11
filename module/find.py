import ast
import csv
import os
import pickle
import numpy as np
import cv2
from deepface.modules import detection, preprocessing
from tensorflow.tools.docs.doc_controls import header

from model.classification_model import FacialRecognitionModel
from module import config, utils

face_model = FacialRecognitionModel()
model = face_model.get_embedding_model()

def DatabaseEmbedding(data_dir,model):
    embedding_dict = {}

    for img in os.listdir(data_dir):
        img_path = os.path.join(data_dir,img)
        img_name = img.split('.')[0]
        embedding_img, _ = utils.preprocess(img_path,model)
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

    with (open(r"D:\Python plus\AI_For_CV\dataset\face_dataset\employee.csv", "r") as f):
        # db_embeddings =
        reader = csv.reader(f)
        next(reader, None)  # Bỏ qua tiêu đề
        query_embedding = img
        for row in reader:
            embedding_img = np.load(row[3])
            dist = np.linalg.norm(query_embedding - embedding_img)
            if dist < min_distant:
                min_distant = dist
                identity = row[1]
                id = row[0]


    if min_distant <= threshold and identity is not None:
        return id,identity, min_distant
    else:
        return None,"unknown", min_distant

