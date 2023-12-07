import tensorflow as tf
from tensorflow.keras.layers import Layer, Conv2D, GlobalAveragePooling2D, concatenate, Add, Activation, Multiply, Input, Reshape
from tensorflow.keras.models import Model

class EAM(tf.keras.layers.Layer):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        
        self.conv1 = Conv2D(64, (3,3), dilation_rate=1,padding='same',activation='relu')
        self.conv2 = Conv2D(64, (3,3), dilation_rate=2,padding='same',activation='relu') 

        self.conv3 = Conv2D(64, (3,3), dilation_rate=3,padding='same',activation='relu')
        self.conv4 = Conv2D(64, (3,3), dilation_rate=4,padding='same',activation='relu')

        self.conv5 = Conv2D(64, (3,3),padding='same',activation='relu')

        self.conv6 = Conv2D(64, (3,3),padding='same',activation='relu')
        self.conv7 = Conv2D(64, (3,3),padding='same')

        self.conv8 = Conv2D(64, (3,3),padding='same',activation='relu')
        self.conv9 = Conv2D(64, (3,3),padding='same',activation='relu')
        self.conv10 = Conv2D(64, (1,1),padding='same')

        self.gap = GlobalAveragePooling2D()

        self.conv11 = Conv2D(64, (3,3),padding='same',activation='relu')
        self.conv12 = Conv2D(64, (3,3),padding='same',activation='sigmoid')

    def call(self,input):
        conv1 = self.conv1(input)
        conv1 = self.conv2(conv1)

        conv2 = self.conv3(input)
        conv2 = self.conv4(conv2)

        concat = concatenate([conv1,conv2])
        conv3 = self.conv5(concat)
        add1 = Add()([input,conv3])

        conv4 = self.conv6(add1)
        conv4 = self.conv7(conv4)
        add2 = Add()([conv4,add1])
        add2 = Activation('relu')(add2)

        conv5 = self.conv8(add2)
        conv5 = self.conv9(conv5)
        conv5 = self.conv10(conv5)
        add3 = Add()([add2,conv5])
        add3 = Activation('relu')(add3)

        gap = self.gap(add3)
        gap = Reshape((1,1,64))(gap)
        conv6 = self.conv11(gap)
        conv6 = self.conv12(conv6)
        
        mul = Multiply()([conv6, add3])
        out = Add()([input,mul]) # This is not included in the reference code
        return out

class RIDNet(Model):
    def __init__(self):
        super().__init__()
        self.input_layer = Input(shape=(256, 256, 3))
        self.conv1 = Conv2D(64, (3,3),padding='same')
        self.eam1 = EAM()
        self.eam2 = EAM()
        self.eam3 = EAM()
        self.eam4 = EAM()
        self.conv2 = Conv2D(3, (3,3),padding='same')
        self.add = Add()

    def call(self):
        x = self.conv1(self.input_layer)
        x = self.eam1(x)
        x = self.eam2(x)
        x = self.eam3(x)
        x = self.eam4(x)
        x = self.conv2(x)
        out = self.add([x, self.input_layer])
        return out

ridnet = RIDNet()
model = ridnet.call()
RIDNetModel = Model(ridnet.input_layer, model)

# 90k_20_loss_l1_l2
# Define the loss function
def combined_loss(y_true, y_pred):
    # Compute the L1 loss
    l1_loss = tf.reduce_mean(tf.abs(y_true - y_pred))

    # Compute the L2 loss
    l2_loss = tf.reduce_mean(tf.square(y_true - y_pred))

    # Combine the L1 and L2 losses
    combined = l1_loss + l2_loss


    return combined
