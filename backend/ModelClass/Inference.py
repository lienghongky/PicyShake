import tensorflow as tf
import os
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from ModelClass import RIDNetModel,EAM,combined_loss
from ModelClass.tqdm_predict_callback import TQDMPredictCallback 
from patchify import patchify, unpatchify
import numpy as np
#testing purpose
import matplotlib.pyplot as plt
from PIL import Image

class Inference:
    #initialize the model
    def __init__(self,model_name='models/model_90k_20_loss_l1_l2.keras',output_dir='./files/outputs',progress_callback=None):
      self.model_name = model_name
      self.output_dir = output_dir
      self.porgress_callback = progress_callback
      self.is_in_progress = False
      self.progress = 0.0

    #initialize 
    def initialize(self):
      os.makedirs(self.output_dir, exist_ok=True)
      gpus = tf.config.list_physical_devices('GPU')
      if gpus:
        try:
            tf.config.experimental.set_memory_growth(gpus[0], True)
             # Restrict TensorFlow to only allocate 2GB of memory on the first GPU
            print("Physical GPU:", tf.config.list_physical_devices('GPU'))
            print(f"GPU Name: {gpu.name}")
            print(f"Total GPU Memory: {tf.config.experimental.get_memory_info(gpu)['total']} bytes")
            print(f"Currently Allocated GPU Memory: {tf.config.experimental.get_memory_info(gpu)['currently_allocated']} bytes")
            print(f"Free GPU Memory: {tf.config.experimental.get_memory_info(gpu)['free']} bytes")

            print("Initialized with Physical GPU:", tf.config.list_physical_devices('GPU'))
        except RuntimeError as e:
            print(e)
            print("Initialized with CPU")

    #load model
    def load_model(self,model_name=None):
      if model_name is not None:
        self.model_name = model_name 
      self.RIDNet = RIDNetModel
      # self.RIDNet.compile(optimizer=tf.keras.optimizers.Adam(1e-03), loss=tf.keras.losses.MeanSquaredError())
      #self.RIDNet.compile(optimizer=tf.keras.optimizers.Adam(1e-03), loss=combined_loss)
      print(f"Loading Model: {self.model_name}")
      self.RIDNet = tf.keras.models.load_model(self.model_name,custom_objects={'EAM':EAM,'combined_loss':combined_loss})
      print("Model Loaded")

    #predict
    def predict(self, image_path, progress_callback=None):
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      print(image_path)
      try:
        # Load the noisy image
        #noisy_image = img_to_array(load_img(image_path,target_size=(256, 256))) / 255.0
        noisy_image = img_to_array(load_img(image_path))
        # Set the patch size
        patch_size = (256, 256, 3)  # Assuming a 3-channel image, adjust as needed
        # check if image is smaller than patch size
        # Pad the image to make it divisible by the patch size
        target_height = ((noisy_image.shape[0] - 1) // patch_size[0] + 1) * patch_size[0]
        target_width = ((noisy_image.shape[1] - 1) // patch_size[1] + 1) * patch_size[1]
        print(target_height,target_width)
        # Create a new padded image
        padded_image = np.zeros((target_height, target_width, noisy_image.shape[2]), dtype=noisy_image.dtype)
        # pad with reflect
        padded_image = np.pad(noisy_image, ((0, target_height - noisy_image.shape[0]), (0, target_width - noisy_image.shape[1]), (0, 0)), mode='reflect')

          
        Image.fromarray(padded_image.astype(np.uint8)).save('files/debugs/padded_image.png')

        # slice image into 256x256 patches and reconstruct the image back
        patches = patchify(padded_image.astype(np.uint8), patch_size, step=256)
        print(patches.shape)
        self.display_patches(patches)
      
        print(f"Predicting with [{self.model_name}]")
        # Get the denoised image using the model
        denoised_patches = patches
        noisy_patches = []
        for i in range(patches.shape[0]):
          for j in range(patches.shape[1]):
              single_patch_img = patches[i, j, :, :, :][0]
              single_patch_img = single_patch_img / 255.0
              # single_patch_img = tf.expand_dims(single_patch_img, axis=0)
              noisy_patches.append(single_patch_img)

        noisy_patches = np.array(noisy_patches) 
        print(noisy_patches[0].shape)
        output_patches = self.RIDNet.predict(noisy_patches,callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])

        for i in range(denoised_patches.shape[0]):
          for j in range(denoised_patches.shape[1]):
            
              denoised_output_patche = output_patches[i*denoised_patches.shape[1]+j]
              denoised_output_patche = denoised_output_patche.clip(0, 1) 
              denoised_output_patche = denoised_output_patche * 255.0
              denoised_patches[i, j, :, :, :] = denoised_output_patche
              Image.fromarray((denoised_output_patche).astype(np.uint8)).save(f'files/debugs/denoised_patch_{i}_{j}.png')
        
        denoised_image = unpatchify(denoised_patches, padded_image.shape) 
        #save denoised image to debugs
        Image.fromarray(denoised_image.astype(np.uint8)).save('files/debugs/denoised_image.png')
        #crop image to original size
        denoised_image = denoised_image[:noisy_image.shape[0], :noisy_image.shape[1], :]
        #save cropped image to debugs
        Image.fromarray(denoised_image.astype(np.uint8)).save('files/debugs/cropped_denoised_image.png')
        # convert to double 
 

        # Calculate PSNR and SSIM
        # psnr = tf.image.psnr(denoised_image, noisy_image, max_val=255).numpy()
        # ssim = tf.image.ssim(denoised_image, noisy_image, max_val=255, filter_size=11, filter_sigma=1.5, k1=0.01,
        #            k2=0.03).numpy()

        # print("PSNR:", psnr)
        # print("SSIM:", ssim)

      
        # Get the denoised image using the model
        denoised_image_name = image_path.split('/')[-1].split('.')[0] + '_denoised.png'
        save_path = os.path.join(self.output_dir, denoised_image_name)
        # Save denoised image
        tf.keras.preprocessing.image.save_img(save_path, tf.cast(denoised_image, tf.uint8))

        # Call the progress callback if provided
        if progress_callback is not None:
          progress_callback(1.0)  # Indicate completion
        self.is_in_progress = False
        return denoised_image_name, save_path, (0, 0)
      except Exception as e:
        print("An error occurred:", str(e))
        self.is_in_progress = False
        return None, None, None


    #display patches of images in a grid
    def display_patches(self, patches):
      fig, axs = plt.subplots(patches.shape[0], patches.shape[1], figsize=(patches.shape[1], patches.shape[0]))
      if patches.shape[0] == 1 and patches.shape[1] == 1:
        axs = np.array([axs])

      for i in range(patches.shape[0]):
          for j in range(patches.shape[1]):
              single_patch_img = patches[i, j, :, :, :][0]
              axs[i, j].imshow(single_patch_img)
              axs[i, j].axis('off')
              axs[i, j].set_aspect('equal')

      plt.subplots_adjust(wspace=0.04, hspace=0.02)  # adjust the space between images
      plt.tight_layout()
      plt.savefig('files/debugs/all_patches.png')
      
    #Calculate PSNR and SSIM
    def calculate_average_pnsr_ssim(self,validation_image_paths):

      #Calculate average psnr and ssim over the whole dataset
      # print("Average PSNR:", psnr)
      # print("Average SSIM:", ssim)
        
      # Calculate average PSNR and SSIM values for the whole dataset
      avg_psnr = 0.0
      avg_ssim = 0.0
      count = 0

      for i, image_path in enumerate(validation_image_paths):
        if i >= 1000:
          break
        print(image_path)
        # Load the noisy image
        noisy_image = img_to_array(load_img(image_path, target_size=(256, 256)))/255.0

        # Get the denoised image using the model
        denoised_image = self.RIDNet.predict(tf.expand_dims(noisy_image, axis=0))[0]
        denoised_image = denoised_image.clip(0, 1) 
        # get the color image
        denoised_image = denoised_image * 255.0
        noisy_image = noisy_image * 255.0
        #get original image
        c_img = img_to_array(load_img(image_path.replace("input","groundtruth"), target_size=(256, 256)))
        #calculate psnr, ssim then print
        psnr = tf.image.psnr(denoised_image, c_img, max_val=255)
        ssim = tf.image.ssim(denoised_image, c_img, max_val=255, filter_size=11, filter_sigma=1.5, k1=0.01, k2=0.03)

        print("PSNR:", psnr.numpy())
        print("SSIM:", ssim.numpy())

        # Accumulate PSNR and SSIM values
        avg_psnr += psnr.numpy()
        avg_ssim += ssim.numpy()
        count += 1

      # Calculate average PSNR and SSIM
      avg_psnr /= count
      avg_ssim /= count

      print("Average PSNR:", avg_psnr)
      print("Average SSIM:", avg_ssim)













