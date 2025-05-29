import os.path

import tensorflow as tf
from deepface.modules import preprocessing
from matplotlib import pyplot as plt
from script.face_recognition.model.classification_model import FacialRecognitionModel

AUTOTUNE = tf.data.AUTOTUNE

train_dir = r"D:\Python plus\AI_For_CV\dataset\face_dataset\train"
val_dir = r"D:\Python plus\AI_For_CV\dataset\face_dataset\val"
checkpoint_dir = r"D:\Python plus\AI_For_CV\script\face_recognition\checkpoint\v1"

os.makedirs(checkpoint_dir, exist_ok=True)
# Create dataset
train_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    train_dir,
    labels='inferred',
    label_mode='categorical',
    shuffle=True,
    batch_size=32,
    image_size=(224, 224),
    seed=7,
)

val_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    val_dir,
    labels='inferred',
    label_mode='categorical',
    shuffle=True,
    batch_size=32,
    image_size=(224, 224),
    seed=7,
)
# Preprocess images for VGGFace
def preprocess_image(image, label):
    # Ensure image is float32
    image = tf.cast(image, tf.float32)
    # Normalize for VGGFace: subtract mean values [93.5940, 104.7624, 129.1863]
    mean = tf.constant([93.5940, 104.7624, 129.1863], dtype=tf.float32)
    image = image - mean
    return image, label

train_dataset = train_dataset.map(preprocess_image, num_parallel_calls=AUTOTUNE)
val_dataset = val_dataset.map(preprocess_image, num_parallel_calls=AUTOTUNE)
train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
val_dataset = val_dataset.prefetch(buffer_size=AUTOTUNE)

# Initialize model
facial_model = FacialRecognitionModel()
model = facial_model.model

# Define ModelCheckpoint callback to save the best model
checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=os.path.join(checkpoint_dir, "model.h5"),  # Filepath to save the model
    monitor='val_accuracy',                       # Metric to monitor
    save_best_only=True,                          # Save only the best model
    mode='max',                                   # Maximize val_accuracy
    save_weights_only=False,                      # Save the entire model
    verbose=1                                     # Print when model is saved
)

# Train the model with the callback
history = model.fit(
    train_dataset,
    verbose=1,
    epochs=10,
    validation_data=val_dataset,
    callbacks=[checkpoint_callback]                # Add the checkpoint callback
)

# Optional: Plot training history
plt.plot(history.history['accuracy'], label='train_accuracy')
plt.plot(history.history['val_accuracy'], label='val_accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

plt.plot(history.history['loss'], label='train_loss')
plt.plot(history.history['val_loss'], label='val_loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()