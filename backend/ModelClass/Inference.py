import tensorflow as tf
import os
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from ModelClass import RIDNetModel,EAM,combined_loss
from ModelClass.tqdm_predict_callback import TQDMPredictCallback 
from ModelClass.smooth_tiled_predictions import predict_img_with_smooth_windowing
from patchify import patchify, unpatchify
import numpy as np
from enum import Enum
#testing purpose
import matplotlib.pyplot as plt
from PIL import Image
from sklearn.preprocessing import MinMaxScaler
import threading
from scipy.ndimage import gaussian_filter


class Inference:
    #define Enum for Prediction Mode
    class PredictionMode(Enum):
      ITERATE = 1
      BATCH = 2
      OVERLAPPING = 3
      SMOOTH = 4
      RESIZING = 5
      AUTORESIZING = 6
      
    #initialize the model
    def __init__(self,model_name='models/v9.LATEST_MODEL_100k.keras',output_dir='./files/outputs',progress_callback=None):
      self.model_name = model_name
      self.output_dir = output_dir
      self.porgress_callback = progress_callback
      self.is_in_progress = False
      self.progress = 0.0
      self.save_patches = True
      self.on_pache_denoised: callable = None

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
      try:
        self.RIDNet = RIDNetModel
        # self.RIDNet.compile(optimizer=tf.keras.optimizers.Adam(1e-03), loss=tf.keras.losses.MeanSquaredError())
        #self.RIDNet.compile(optimizer=tf.keras.optimizers.Adam(1e-03), loss=combined_loss)
        print(f"Loading Model: {self.model_name}")
        self.RIDNet = tf.keras.models.load_model(self.model_name,custom_objects={'EAM':EAM,'combined_loss':combined_loss})
        print("Model Loaded")
        return True
      except Exception as e:
        print("An error occurred:", str(e))
        return False

    def predict(self, image_path, progress_callback=None, mode=PredictionMode.ITERATE):
      
      #switch case for prediction mode
      if mode == self.PredictionMode.ITERATE:
        return self.predictIterate(image_path, progress_callback)
      elif mode == self.PredictionMode.BATCH:
        return self.predictBatch(image_path, progress_callback)
      elif mode == self.PredictionMode.OVERLAPPING:
        return self.predictOverlap(image_path, progress_callback)
      elif mode == self.PredictionMode.SMOOTH:
        return self.predictSmooth(image_path, progress_callback)
      elif mode == self.PredictionMode.RESIZING:
        return self.predictResizing(image_path, progress_callback)
      else:
        return self.predictMaxResize(image_path, progress_callback)
      
    #predict
    def predictSmooth(self, image_path, progress_callback=None):
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      print(image_path)
            
      image_name = os.path.basename(image_path).split(".")[0]
      result_dir =  os.path.join(self.output_dir, f'{image_name}')
      os.makedirs(result_dir, exist_ok=True)
      # try:
      # Load the noisy image
      noisy_image = img_to_array(load_img(image_path))/255.0
      # Set the patch size
      patch_size = (256, 256, 3) 
      # check if image is smaller than patch size
      target_height = ((noisy_image.shape[0] - 1) // patch_size[0] + 1) * patch_size[0]
      target_width = ((noisy_image.shape[1] - 1) // patch_size[1] + 1) * patch_size[1]
      scaler = MinMaxScaler()
      input_img = scaler.fit_transform(noisy_image.reshape(-1, noisy_image.shape[-1])).reshape(noisy_image.shape)
      def pred_func(img_batch_subdiv):
        return self.RIDNet.predict(img_batch_subdiv.astype(np.uint8),callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])
      predictions_smooth = predict_img_with_smooth_windowing(
                            input_img, 
                            window_size=256, 
                            subdivisions=2,
                            nb_classes=3,
                            pred_func = pred_func
                          )
      
      denoised_image = predictions_smooth*255.0
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), noisy_image)
      #save denoised image to debugs
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"debug.png"), denoised_image)
      #crop image to original size
      denoised_image = denoised_image[:noisy_image.shape[0], :noisy_image.shape[1], :]
      # Save denoised image
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"output.png"), tf.cast(denoised_image, tf.uint8))

      # Call the progress callback if provided
      if progress_callback is not None:
        progress_callback(1.0)  # Indicate completion
      self.is_in_progress = False
      return image_name,f"{image_name}/output.png", (0, 0)
      # except Exception as e:
      #   print("An error occurred:", str(e))
      #   self.is_in_progress = False
      #   return None, None, None
    #predict with batch
    def predictBatch(self, image_path, progress_callback=None):
      print("predictBatch")
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      print(image_path)
      try:

        image_name = os.path.basename(image_path).split(".")[0]
        result_dir =  os.path.join(self.output_dir, f'{image_name}')
        os.makedirs(result_dir, exist_ok=True)
        print(image_path)
        patches, padded_image, noisy_image = self.image_to_patches(image_path) 

        tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), noisy_image)
        print(f"Predicting with [{self.model_name}]")
        # Get the denoised image using the model
        denoised_patches = patches
        step = 0
        # Load the noisy image
      
        print(f"Predicting with [{self.model_name}]")
        # Get the denoised image using the model
        denoised_patches = patches
        noisy_patches = []
        threading.Thread(target=self.save_debugged_image, args=(denoised_patches, padded_image.shape, result_dir,f"{patches.shape[0]}-{patches.shape[1]}")).start()
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
        tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), noisy_image)
        tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"debug.png"), denoised_image)
        #crop image to original size
        denoised_image = denoised_image[:noisy_image.shape[0], :noisy_image.shape[1], :]
 
        # Save denoised image
        tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"output.png"), tf.cast(denoised_image, tf.uint8))

        # Call the progress callback if provided
        if progress_callback is not None:
          progress_callback(1.0)  # Indicate completion
        self.is_in_progress = False
        return image_name,f"{image_name}/output.png", (0, 0)
      except Exception as e:
        print("An error occurred:", str(e))
        self.is_in_progress = False
        return None, None, None
      #predict
    def predictMaxResize(self, image_path, progress_callback=None):
      print("predictIterate")
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      
      image_name = os.path.basename(image_path).split(".")[0]
      result_dir =  os.path.join(self.output_dir, f'{image_name}')
      os.makedirs(result_dir, exist_ok=True)
      print(image_path)

      noisy_image = img_to_array(load_img(image_path)) 
      min_dim = min(noisy_image.shape[0],noisy_image.shape[1])
      patch_width = min(512,min_dim) 
      
      patches, padded_image, noisy_image = self.image_to_patches(image_path,patch_size=(patch_width,patch_width,3),step=patch_width) 
      
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), noisy_image)
      print(f"Predicting with [{self.model_name}]")
      # Get the denoised image using the model
      denoised_patches = np.copy(patches)
      step = 0
      for i in range(patches.shape[0]):
        for j in range(patches.shape[1]):
            single_patch_img = patches[i, j, :, :, :][0]
            single_patch_img = tf.image.resize(single_patch_img, (256, 256))
            single_patch_img = single_patch_img / 255.0
            denoised_patche = self.RIDNet.predict(tf.expand_dims(single_patch_img, axis=0),callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])[0]
            denoised_patche = denoised_patche.clip(0, 1)
            denoised_patche = denoised_patche * 255.0
            denoised_patche = tf.image.resize(denoised_patche, (patch_width, patch_width))
            denoised_patches[i, j, :, :, :] = denoised_patche
            step += 1
            progress_callback(step/(patches.shape[0]*patches.shape[1]))
            # threading.Thread(target=progress_callback, args=(step/(patches.shape[0]*patches.shape[1]),)).start()
            #save denoised image to debugs
            threading.Thread(target=self.save_debugged_image, args=(denoised_patches, padded_image.shape, result_dir,f"{j}-{i}")).start()

      denoised_image = unpatchify(denoised_patches, padded_image.shape)
      #crop image to original size
      denoised_image = denoised_image[:noisy_image.shape[0], :noisy_image.shape[1], :]
      # convert to double 
      # Get the denoised image using the model
      
    
      # Save denoised image
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"output.png"), tf.cast(denoised_image, tf.uint8))

      # Call the progress callback if provided
      if progress_callback is not None:
        progress_callback(1.0)  # Indicate completion
      self.is_in_progress = False
      return image_name,f"{image_name}/output.png", (0, 0)
    
    #predict with resizing
    def predictResizing(self, image_path, progress_callback=None):
      print("predictResizing")
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      
      image_name = os.path.basename(image_path).split(".")[0]
      result_dir =  os.path.join(self.output_dir, f'{image_name}')
      os.makedirs(result_dir, exist_ok=True)
      #load image
      input = img_to_array(load_img(image_path))/255.0
      noisy_image = tf.image.resize(input, (256, 256))
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), input)

      #save denoised image to debugs
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"debug.png"), noisy_image)
      if self.on_pache_denoised is not None:
        self.on_pache_denoised(image_name,f"{image_name}/debug.png?patch_number={1}")
        


      print(f"Predicting with [{self.model_name}]")
      denoised_image = self.RIDNet.predict(tf.expand_dims(noisy_image, axis=0),callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])[0]
      denoised_image = denoised_image.clip(0, 1)
      denoised_image = denoised_image * 255.0
      threading.Thread(target=progress_callback, args=(1.0,)).start()
            
      #resize image to original size
      denoised_image = tf.image.resize(denoised_image, (input.shape[0], input.shape[1]))
      # Save denoised image
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"output.png"), tf.cast(denoised_image, tf.uint8))

      # Call the progress callback if provided
      if progress_callback is not None:
        progress_callback(1.0)  # Indicate completion
      self.is_in_progress = False
      return image_name,f"{image_name}/output.png", (0, 0)
     #predict
    #predict with overlapping
    def predictOverlap(self, image_path, progress_callback=None):
      print("predictIterate")
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      
      image_name = os.path.basename(image_path).split(".")[0]
      result_dir =  os.path.join(self.output_dir, f'{image_name}')
      os.makedirs(result_dir, exist_ok=True)
      print(image_path)
      patches, padded_image, noisy_image = self.image_to_patches(image_path,step=200) 

      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), noisy_image)
      print(f"Predicting with [{self.model_name}]")
      # Get the denoised image using the model
      denoised_patches = np.copy(patches)
      step = 0
      for i in range(patches.shape[0]):
        for j in range(patches.shape[1]):
            single_patch_img = patches[i, j, :, :, :][0]
            tf.keras.preprocessing.image.save_img(os.path.join(result_dir,f"patch_{j}_{i}.png"), single_patch_img)
            single_patch_img = single_patch_img / 255.0
            denoised_patche = self.RIDNet.predict(tf.expand_dims(single_patch_img, axis=0),callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])[0]
            denoised_patche = denoised_patche.clip(0, 1)
            denoised_patche = denoised_patche * 255.0
            denoised_patches[i, j, :, :, :] = denoised_patche
            step += 1
            progress_callback(step/(patches.shape[0]*patches.shape[1]))
            #save single patch image to debugs
            tf.keras.preprocessing.image.save_img(os.path.join(result_dir,f"denoised_patch_{j}_{i}.png"), denoised_patche)
            #save denoised image to debugs
            # threading.Thread(target=self.save_debugged_image, args=(denoised_patches, padded_image.shape, result_dir,f"{j}-{i}")).start()

      # denoised_image = unpatchify(denoised_patches, padded_image.shape)
      # tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"unp.png"), unpatchify(denoised_patches, padded_image.shape))
      denoised_image = self.patches_to_image(denoised_patches, padded_image.shape,step=200) 
      #crop image to original size
      denoised_image = denoised_image[:noisy_image.shape[0], :noisy_image.shape[1], :]
      # convert to double 
      # Get the denoised image using the model
      
    
      # Save denoised image
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"output.png"), tf.cast(denoised_image, tf.uint8))

      # Call the progress callback if provided
      if progress_callback is not None:
        progress_callback(1.0)  # Indicate completion
      self.is_in_progress = False
      return image_name,f"{image_name}/output.png", (0, 0)
    
    #predict
    def predictIterate(self, image_path, progress_callback=None):
      print("predictIterate")
      self.is_in_progress = True
      self.progress = 0.0
      if progress_callback is None:
        progress_callback = self.porgress_callback
      
      image_name = os.path.basename(image_path).split(".")[0]
      result_dir =  os.path.join(self.output_dir, f'{image_name}')
      os.makedirs(result_dir, exist_ok=True)
      print(image_path)
      patches, padded_image, noisy_image = self.image_to_patches(image_path,step=256) 

      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"input.png"), noisy_image)
      print(f"Predicting with [{self.model_name}]")
      # Get the denoised image using the model
      denoised_patches = np.copy(patches)
      step = 0
      for i in range(patches.shape[0]):
        for j in range(patches.shape[1]):
            single_patch_img = patches[i, j, :, :, :][0]
            single_patch_img = single_patch_img / 255.0
            denoised_patche = self.RIDNet.predict(tf.expand_dims(single_patch_img, axis=0),callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])[0]
            denoised_patche = denoised_patche.clip(0, 1)
            denoised_patche = denoised_patche * 255.0
            denoised_patches[i, j, :, :, :] = denoised_patche
            step += 1
            progress_callback(step/(patches.shape[0]*patches.shape[1]))
            # threading.Thread(target=progress_callback, args=(step/(patches.shape[0]*patches.shape[1]),)).start()
            #save denoised image to debugs
            threading.Thread(target=self.save_debugged_image, args=(denoised_patches, padded_image.shape, result_dir,f"{j}-{i}")).start()

      denoised_image = unpatchify(denoised_patches, padded_image.shape)
      #crop image to original size
      denoised_image = denoised_image[:noisy_image.shape[0], :noisy_image.shape[1], :]
      # convert to double 
      # Get the denoised image using the model
      
    
      # Save denoised image
      tf.keras.preprocessing.image.save_img(os.path.join(result_dir,"output.png"), tf.cast(denoised_image, tf.uint8))

      # Call the progress callback if provided
      if progress_callback is not None:
        progress_callback(1.0)  # Indicate completion
      self.is_in_progress = False
      return image_name,f"{image_name}/output.png", (0, 0)
    
    def save_debugged_image(self, patches, imsize, path,patch_number, space=6):
    # Calculate the size of the new image
      new_imsize = (
          imsize[0] + (patches.shape[0] - 1) * space,
          imsize[1] + (patches.shape[1] - 1) * space,
          patches.shape[5]  # Assuming 4th dimension represents color channels
      )

     
      # Create a new image with the correct dtype
      image = np.zeros(new_imsize, dtype=np.uint8)

      # Place each patch at the correct position
      for i in range(patches.shape[0]):
          for j in range(patches.shape[1]):
              y_start = i * (patches.shape[3] + space)
              y_end = y_start + patches.shape[3]

              x_start = j * (patches.shape[3] + space)
              x_end = x_start + patches.shape[3]
             
              image[y_start:y_end, x_start:x_end, :] = patches[i, j, 0, :, :, :].astype(np.uint8)

      # Save the reconstructed image
      image_id = os.path.basename(path)
      print(image_id)
      image_path = os.path.join(path, 'debug.png')
      tf.keras.preprocessing.image.save_img(image_path, image)
      image_sm_path = os.path.join(path, 'debug.jpg')
      image_sm = Image.fromarray(image.astype(np.uint8))
      image_sm.save(image_sm_path, format='JPEG', optimize=True, quality=60)
      if self.on_pache_denoised is not None:
        self.on_pache_denoised(image_id,f"{image_id}/debug.jpg?patch_number={patch_number}")

      return image
    


    #slice image into patchesdebug_dir
    def image_to_patches(self, image_path, patch_size=(256, 256, 3), step=256):
      noisy_image = img_to_array(load_img(image_path))
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
      patches = patchify(padded_image.astype(np.uint8), patch_size, step=step)
      return patches, padded_image, noisy_image
    
    def patches_to_image(self, patches, imsize, step=256, feathering=2):
        # Calculate the size of the new image
        new_imsize = (
            imsize[0] + (patches.shape[0] - 1) * step,
            imsize[1] + (patches.shape[1] - 1) * step,
            patches.shape[5]  # Assuming 4th dimension represents color channels
        )
        overlap_size = 256 - step
        patch_size = 256
        # Create a new image with the correct dtype
        image = np.zeros(new_imsize, dtype=np.float64)
        blend_weights = np.zeros_like(image)

        # Place each patch at the correct position
        for i in range(patches.shape[0]):
            for j in range(patches.shape[1]):
                y_start = i * step
                y_end = y_start + patches.shape[3]

                x_start = j * step
                x_end = x_start + patches.shape[3]

                feathered_patch = patches[i, j, 0, :, :, :].astype(np.float64)
                
                # Update the image and blend_weights
                image[y_start:y_end, x_start:x_end, :] += feathered_patch
                blend_weights[y_start:y_end, x_start:x_end, :] += 1

        # Normalize the image by the blend weights to avoid intensity artifacts
        image /= blend_weights + 1e-10  # Avoid division by zero

        return image

    #display patches of images in a grid
    def display_patches(self, patches):
      try:
        fig, axs = plt.subplots(patches.shape[0], patches.shape[1], figsize=(patches.shape[1], patches.shape[0]))
        if patches.shape[0] == 1 and patches.shape[1] == 1:
          #add extra dimension for single patch image
          axs = np.array([axs])
        axs = axs.reshape(1,1)
        print(axs.shape)
        for i in range(patches.shape[0]):
            for j in range(patches.shape[1]):
                single_patch_img = patches[i, j,0, :, :, :]
                axs[i, j].imshow(single_patch_img)
                axs[i, j].axis('off')
                axs[i, j].set_aspect('equal')

        plt.subplots_adjust(wspace=0.04, hspace=0.02)  # adjust the space between images
        plt.tight_layout()
        plt.savefig('files/debugs/all_patches.png')
      except Exception as e:
        print("An error occurred:", str(e))
        print("Error in displaying patches")
        pass
      
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













