# config.py
import tensorflow as tf

# File paths
TRAIN_DATASET = r"D:\Python plus\AI_For_CV\dataset\face_dataset\train"
VAL_DATASET = r"D:\Python plus\AI_For_CV\dataset\face_dataset\val"
CHECK_POINT = r"D:\Python plus\AI_For_CV\script\face_recognition\checkpoint\v1\model.h5"
ATTENDANCE_REPORT = r"D:\Python plus\AI_For_CV\dataset\face_dataset\attendance\report"
CHECKOUT_REPORT = r"D:\Python plus\AI_For_CV\dataset\face_dataset\attendance\checkout"
EMPLOYEE_CSV = r"D:\Python plus\AI_For_CV\dataset\face_dataset\employee.csv"
EMPLOYEE_DIR = r"D:\Python plus\AI_For_CV\dataset\face_dataset\attendance_face"
EMPLOYEE_EMBEDDING = r"D:\Python plus\AI_For_CV\dataset\face_dataset\attendance_embedding"
ADMIN_DIR = r"D:\Python plus\AI_For_CV\dataset\face_dataset\admin.txt"

# Model input image size
IMAGE_SIZE = (224, 224)

# Batch size and buffer size
BATCH_SIZE = 256
BUFFER_SIZE = BATCH_SIZE * 2

# Define autotune
AUTO = tf.data.AUTOTUNE

# Training parameters
LEARNING_RATE = 0.0001
STEPS_PER_EPOCH = 50
VALIDATION_STEPS = 10
EPOCHS = 10

# Threshold for verification
THRESHOLD = 0.56