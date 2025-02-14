# -*- coding: utf-8 -*-
"""Desafio-transfer-learning.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17VhKDqQ3PVg9R2dzQV0peSj9PvgFeFw9

# Projeto DIO Transfer learning / fine-tuning
Esta é a minha solução para o projeto da Dio, onde é aplicado Transfer Learning com o modelo VGG16, pré-treinado no ImageNet, para classificar imagens de gatos e cachorros. As primeiras camadas da rede foram congeladas para manter as características mais gerais, como bordas e texturas, enquanto as últimas foram ajustadas para as novas classes. Os dados foram divididos em 70% para treino, 15% para validação e 15% para teste, e o modelo foi treinado por 10 épocas, acompanhando a evolução com gráficos de perda e acurácia.

Esse método facilitou muito o treinamento, já que aproveitamos uma rede bem treinada, economizando tempo e melhorando a precisão do classificador. Comparado ao treinamento do zero, foi possível alcançar um desempenho superior com um número reduzido de imagens, entregando um modelo ajustado de forma eficiente para a tarefa proposta.

Link para baixar o dataset: https://www.microsoft.com/en-us/download/details.aspx?id=54765.
"""

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

import os

#se estiver usando Theano com GPU
#os.environ["KERAS_BACKEND"] = "tensorflow"

import random
import numpy as np
import keras

import matplotlib.pyplot as plt
from matplotlib.pyplot import imshow

from keras.preprocessing import image
from keras.applications.imagenet_utils import preprocess_input
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Activation
from keras.layers import Conv2D, MaxPooling2D
from keras.models import Model

"""### Descompactando Arquivos do Dataset


Nesta etapa eu subi os arquivo zip no collab contendo as imagens que serão usadas para o treinamento.



"""

#Descompactando o arquivos
!unzip -q kagglecatsanddogs_5340.zip -d cats_dogs_dataset

#Removendo o arquivo zip depois de descompactado
!rm kagglecatsanddogs_5340.zip

!ls cats_dogs_dataset

root = '/content/cats_dogs_dataset/PetImages'
train_split, val_split = 0.7, 0.15

categories = [x[0] for x in os.walk(root) if x[0]][1:]

print(categories)

"""
Pré-processamento dos dados e retorno como vetor
vector."""

def get_image(path):
    img = image.load_img(path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return img, x

"""# Carregando todas as imagens da pasta raiz

Aqui eu tive que redimensionar as imagens para economizar a memória, e limitar para 500 imagens para não "estourar a memória".

"""

import cv2

data = []

def process_image_efficient(img_path, category_index):
    try:
        # Carrega a imagem com cv2
        img = cv2.imread(img_path)
        if img is not None:
            # Redimensiona a imagem para economizar memória
            img_resized = cv2.resize(img, (128, 128))
            img, x = get_image(img_path)
            return {'x': np.array(x[0]), 'y': category_index}
        else:
            print(f"Imagem corrompida ignorada: {img_path}")
            return None
    except Exception as e:
        print(f"Erro ao processar {img_path}: {e}")
        return None

# Processar no máximo 500 imagens por categoria
max_images_per_category = 500
for c, category in enumerate(categories):
    images = [os.path.join(dp, f) for dp, dn, filenames
              in os.walk(category) for f in filenames
              if os.path.splitext(f)[1].lower() in ['.jpg', '.png', '.jpeg']]

    # Seleciona apenas as primeiras 500 imagens
    images = images[:max_images_per_category]

    for img_path in images:
        result = process_image_efficient(img_path, c)
        if result is not None:
            data.append(result)

# Contar o número de classes
num_classes = len(categories)

random.shuffle(data)

"""
Criando a divisão de treinamento/validação/teste (70%, 15%, 15%)"""

idx_val = int(train_split * len(data))
idx_test = int((train_split + val_split) * len(data))
train = data[:idx_val]
val = data[idx_val:idx_test]
test = data[idx_test:]

"""

Dados separados para rótulos."""

x_train, y_train = np.array([t["x"] for t in train]), [t["y"] for t in train]
x_val, y_val = np.array([t["x"] for t in val]), [t["y"] for t in val]
x_test, y_test = np.array([t["x"] for t in test]), [t["y"] for t in test]
print(y_test)

"""
Pré-processe os dados como antes, certificando-se de que sejam float32 e normalizados entre 0 e 1."""

num_classes = 2

# normaliza os dados
x_train = x_train.astype('float32') / 255.
x_val = x_val.astype('float32') / 255.
x_test = x_test.astype('float32') / 255.

# converte os rótulos para vetores one-hot
y_train = keras.utils.to_categorical(y_train, num_classes)
y_val = keras.utils.to_categorical(y_val, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

print(y_test.shape)

"""

Sumário de tudo que foi feito"""

#Sumário
print("finished loading %d images from %d categories"%(len(data), num_classes))
print("train / validation / test split: %d, %d, %d"%(len(x_train), len(x_val), len(x_test)))
print("training data shape: ", x_train.shape)
print("training labels shape: ", y_train.shape)

images = [os.path.join(dp, f) for dp, dn, filenames in os.walk(root) for f in filenames if os.path.splitext(f)[1].lower() in ['.jpg','.png','.jpeg']]
idx = [int(len(images) * random.random()) for i in range(8)]
imgs = [image.load_img(images[i], target_size=(224, 224)) for i in idx]
concat_image = np.concatenate([np.asarray(img) for img in imgs], axis=1)
plt.figure(figsize=(16,4))
plt.imshow(concat_image)

vgg = keras.applications.VGG16(weights='imagenet', include_top=True)
vgg.summary()

# faça uma referência à camada de entrada do VGG
inp = vgg.input

# crie uma nova camada softmax com num_classes neurônios
new_classification_layer = Dense(num_classes, activation='softmax')

# conecte nossa nova camada à penúltima camada do VGG e faça uma referência a ela
out = new_classification_layer(vgg.layers[-2].output)

# crie uma nova rede entre inp e out
model_new = Model(inp, out)

# torne todas as camadas não treináveis, congelando os pesos (exceto a última camada)
for l, layer in enumerate(model_new.layers[:-1]):
    layer.trainable = False

# garanta que a última camada seja treinável/não congelada
for l, layer in enumerate(model_new.layers[-1:]):
    layer.trainable = True

model_new.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

model_new.summary()

print(x_train.shape)
print(x_val.shape)

"""Treinando a IA"""

history2 = model_new.fit(x_train, y_train,
                         batch_size=128,
                         epochs=15,
                         validation_data=(x_val, y_val))

fig = plt.figure(figsize=(16,4))

# Gráfico de Validação da Perda (Loss)
ax = fig.add_subplot(121)
ax.plot(history2.history["val_loss"], label="Modelo")
ax.set_title("Validation Loss")
ax.set_xlabel("Epochs")
ax.legend()

# Gráfico de Validação da Acurácia (Accuracy)
ax2 = fig.add_subplot(122)
ax2.plot(history2.history["val_accuracy"], label="Modelo")
ax2.set_title("Validation Accuracy")
ax2.set_xlabel("Epochs")
ax2.set_ylim(0, 1)
ax2.legend()

plt.show()

loss, accuracy = model_new.evaluate(x_test, y_test, verbose=0)

print('Test loss:', loss)
print('Test accuracy:', accuracy)

"""Plotando os gráficos iniciais"""

# Plotando a perda durante o treino e validação
plt.figure(figsize=(12, 6))
plt.plot(history2.history['loss'], label='Perda - Treinamento', color='blue', linestyle='--')
plt.plot(history2.history['val_loss'], label='Perda - Validação', color='orange')
plt.title('Perda (Loss) por Época')
plt.xlabel('Épocas')
plt.ylabel('Perda')
plt.legend()
plt.grid(True)
plt.show()

# Plotando a acurácia durante o treino e validação
plt.figure(figsize=(12, 6))
plt.plot(history2.history['accuracy'], label='Acurácia - Treinamento', color='blue', linestyle='--')
plt.plot(history2.history['val_accuracy'], label='Acurácia - Validação', color='orange')
plt.title('Acurácia por Época')
plt.xlabel('Épocas')
plt.ylabel('Acurácia')
plt.legend()
plt.grid(True)
plt.show()

"""Para mostrar que está funcionando:"""

# Carrega a imagem
img, x = get_image('/content/novo/meggie.jpg')

print(f"Forma original: {x.shape}")

if len(x.shape) == 4:
    x = np.squeeze(x, axis=0)

print(f"Forma após squeeze (se necessário): {x.shape}")

x = np.expand_dims(x, axis=0)
print(f"Forma final após expand_dims: {x.shape}")

# Fazer a predição
probabilities = model_new.predict(x)

# Se precisar ver as probabilidades ou a classe predita
print(probabilities)

# Nome das classes para ficar fácil de entender
class_names = ['gato', 'cachorro']

# Obtendo o índice da classe com a maior probabilidade
predicted_class_index = np.argmax(probabilities)

# Obtendo o nome da classe
predicted_class = class_names[predicted_class_index]

print(f"A imagem é provavelmente: {predicted_class}")
