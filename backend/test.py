from ModelClass.Inference import Inference

inference = Inference()
inference.initialize()
inference.load_model(model_name='models/model_90k_20_loss_l1_l2.keras')

inference.predict('files/inputs/5.png')