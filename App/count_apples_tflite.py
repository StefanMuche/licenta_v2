import numpy as np
import os
from tqdm import tqdm
import cv2
import torch
from torchvision import transforms
from torch.utils.data import DataLoader
from PIL import Image
from unet_pytorch import UNet
import matplotlib.pyplot as plt
from skimage import color, measure
import tensorflow as tf
########### DEFINIREA CONSTANTELOR ######################

PATCH_SIZE= 256
NR_PATCHES = 12
DIM_TRAIN_IMAGES = 331
IMG_WIDTH = 256
IMG_HEIGHT = 256
IMG_CHANNELS = 3

############# DEFINIREA VECTORILOR CE CONTIN IMAGINILE ##############################

x_train_uncropped = np.zeros((DIM_TRAIN_IMAGES, 1024, 768, IMG_CHANNELS), dtype = np.uint8)

import tensorflow as tf
import numpy as np
from PIL import Image
import cv2
from skimage import color, measure

def process_and_reconstruct_image(image_path, interpreter):
    # Încarcă imaginea originală și convert-o în formatul așteptat de TensorFlow
    image = Image.open(image_path).convert('RGB')
    image = image.resize((768, 1024), Image.BILINEAR)
    image_np = np.array(image).astype('float32') / 255.0  # Normalizare și convertire în NumPy array

    # Transpunere pentru a aduce canalele în conformitate cu așteptările modelului
    image_np = np.transpose(image_np, (2, 0, 1))  # De la (H, W, C) la (C, H, W)
    # Prepare the model's input dimensions (e.g., [1, 256, 256, 3] for each patch)
    input_details = interpreter.get_input_details()
    batch_size, height, width, channels = input_details[0]['shape']

    # Inițializează tensorul pentru imaginea reconstituită
    reconstructed_mask = np.zeros((1024, 768), dtype=np.uint8)

    # Imparte imaginea în patch-uri și procesează fiecare patch
    for i in range(4):  # 4 patch-uri pe înălțime
        for j in range(3):  # 3 patch-uri pe lățime
            # Extrage patch-ul
            patch = image_np[:, i*256:(i+1)*256, j*256:(j+1)*256]
            patch = np.expand_dims(patch, axis=0)  # Adaugă dimensiunea batch-ului

            # # Aplică modelul TensorFlow pe patch, folosind dicționarul de intrare
            # input_dict = {'input': patch}  # 'input' este numele tensorului de intrare specificat în model
            # results = model(**input_dict)
            # pred_mask = results['output'].numpy()  # 'output' este numele tensorului de ieșire
            # pred_mask = (pred_mask > 0.5).astype(np.uint8)  # Convertirea predicției în masca binară
             # Set tensor to the correct input index and run the model
            interpreter.set_tensor(input_details[0]['index'], patch)
            interpreter.invoke()

            # Get the output and post-process it
            output_details = interpreter.get_output_details()
            pred_mask = interpreter.get_tensor(output_details[0]['index'])
            pred_mask = (pred_mask > 0.5).astype(np.uint8)  # Thresholding to create a binary mask

            # Adaugă patch-ul procesat în masca reconstituită
            reconstructed_mask[i*256:(i+1)*256, j*256:(j+1)*256] = pred_mask[0, 0, :, :] * 255

    # Post-procesare pentru a separa obiectele
    ret, thresh = cv2.threshold(reconstructed_mask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((3,3), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    labels = measure.label(opening, background=0)
    num_mere = np.max(labels)  # Numără obiectele detectate
    label_overlay = color.label2rgb(labels, image=np.array(Image.open(image_path).convert('RGB').resize((768, 1024))), bg_label=0, alpha=0.3)
    print(f'Found {num_mere} apples.')
    return num_mere