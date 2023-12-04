import tensorflow as tf
import os
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from ModelClass import RIDNetModel,EAM
from ModelClass.tqdm_predict_callback import TQDMPredictCallback 

class Inference:
    #initialize the model
    def __init__(self,model_name='models/model_70k_20.keras',output_dir='./files/outputs',progress_callback=None):
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
            # tf.config.experimental.set_virtual_device_configuration(
            #     gpus[0],
            #     [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=6048)])

            print("Initialized with Physical GPU:", tf.config.list_physical_devices('GPU'))
        except RuntimeError as e:
            print(e)
            print("Initialized with CPU")

    #load model
    def load_model(self,model_name=None):
      if model_name == None:
        self.model_name = 'models/model_70k_20.keras'
      self.RIDNet = RIDNetModel
      self.RIDNet.compile(optimizer=tf.keras.optimizers.Adam(1e-03), loss=tf.keras.losses.MeanSquaredError())
      self.RIDNet = tf.keras.models.load_model(self.model_name,custom_objects={'EAM':EAM})
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
        noisy_image = img_to_array(load_img(image_path,target_size=(256, 256))) / 255.0
        # slice image into 256x256 patches and reconstruct the image back
        # noisy_image = tf.image.extract_patches(images=tf.expand_dims(noisy_image, axis=0), sizes=[1, 256, 256, 1], strides=[1, 256, 256, 1], rates=[1, 1, 1, 1], padding='VALID').numpy()[0]
        # noisy_image = tf.image.resize(noisy_image, size=(256, 256), method='bicubic', preserve_aspect_ratio=False, antialias=False, name=None).numpy()

        print(f"Predicting with [{self.model_name}]")
        # Get the denoised image using the model
        denoised_image = self.RIDNet.predict(tf.expand_dims(noisy_image, axis=0),callbacks=[TQDMPredictCallback(progress_callback=progress_callback)])[0]
        
        # get the color image
        denoised_image = denoised_image * 255.0
        noisy_image = noisy_image * 255.0

        # Calculate PSNR and SSIM
        psnr = tf.image.psnr(denoised_image, noisy_image, max_val=255).numpy()
        ssim = tf.image.ssim(denoised_image, noisy_image, max_val=255, filter_size=11, filter_sigma=1.5, k1=0.01,
                   k2=0.03).numpy()

        print("PSNR:", psnr)
        print("SSIM:", ssim)

      
        #resize image back to original size noising image size
        denoised_image = tf.image.resize(denoised_image, size=(noisy_image.shape[0], noisy_image.shape[1]), method='bicubic', preserve_aspect_ratio=False, antialias=False, name=None).numpy()
        # Get the name of the denoised image
        denoised_image_name = image_path.split('/')[-1].split('.')[0] + '_denoised.png'
        save_path = os.path.join(self.output_dir, denoised_image_name)
        # Save denoised image
        tf.keras.preprocessing.image.save_img(save_path, tf.cast(denoised_image, tf.uint8))

        # Call the progress callback if provided
        if progress_callback is not None:
          progress_callback(1.0)  # Indicate completion
        self.is_in_progress = False
        return denoised_image_name, save_path, (psnr, ssim)
      except Exception as e:
        print("An error occurred:", str(e))
        self.is_in_progress = False
        return None, None, None


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













