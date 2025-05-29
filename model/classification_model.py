from deepface.models.facial_recognition.VGGFace import VggFaceClient
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Flatten
from tensorflow.keras.models import Model

import tensorflow as tf
from module import config

def vggface_preprocessing_layer(x):
    # Subtract mean values for VGGFace (RGB)
    mean = tf.constant([93.5940, 104.7624, 129.1863], dtype=tf.float32)
    return x - mean

class FacialRecognitionModel:
    def __init__(self):
        self.class_names =["ChauBui", "Erik", "HoaMinzy", "KhoaPub", "LamVlog",
                                    "LanAnh", "NguyenVietHoang", "PhuongLy", "SonTung", "TranMinhHieu"]  # Renamed for clarity
        self.model = self.load_model()

    def load_model(self):
        # Initialize VGGFace client and get base model
        client = VggFaceClient()
        base_model = client.model
        base_input = base_model.input
        # t = Lambda(vggface_preprocessing_layer)(base_input)
        # Freeze all layers except the last one
        for layer in base_model.layers[:-1]:
            layer.trainable = False

        x = base_model.output
        x = Dense(2048, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)
        x = Dense(512, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)
        x = Dense(256, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.5)(x)
        x = Dense(len(self.class_names), activation='softmax')(x)

        model = tf.keras.Model(inputs=base_input, outputs=x)

        # Compile model
        model.compile(optimizer='adam',
                      loss='categorical_crossentropy',  # Fixed loss function
                      metrics=['accuracy', tf.keras.metrics.Precision(thresholds=0.7)])

        self.model = model
        return self.model

    def get_model(self):
        if self.model is None:
            self.load_model()
        return self.model

    def get_embedding_model(self):
        my_model = tf.keras.models.load_model(config.CHECK_POINT)
        my_model_output = Flatten()(my_model.layers[-10].output)
        embedding_model = Model(inputs=my_model.input, outputs=my_model_output)
        return embedding_model
