#!/usr/bin/python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import cv2
import os
import random
from keras.models import Sequential
from keras.layers import Conv2D,Dense,Flatten,Dropout,MaxPooling2D
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ReduceLROnPlateau,ModelCheckpoint

# rota para extrair as imagens para treinamento
images_training = 'images/1-training'
images_test = 'images/2-test'

def cnn_train(images_training,images_test):
    # criar automáticamente o arquivo e seta dentro da vairável
    filepath = "weight_kids.h5"
    # configuração do arquivo de peso, save_best_only=True salva o melhor treinamento entre todas as épocas,
    # monitor='val_acc' apresenta os resultados no fim de cada época, verbose=0 apresenta o resultado final
    # depois de cada época
    checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=0, save_best_only=True, mode='max')

    # configuração para receber as imagens e setando varáveis.
    image_height = 150
    image_width = 150
    batch_size = 32
    no_of_epochs = 10

    # playground.tensorflow.org
    # relu função de ativação para deixar pixels negativos zerados, consegue retirar mais contrastes
    model = Sequential()

    # reduz a imagem, em cada época pode ser um kernel
    model.add(Conv2D(batch_size,(3,3), input_shape=(image_height, image_width, 3), activation='relu'))
    model.add(Conv2D(batch_size,(3,3), activation='relu'))

    # a partir da definição que ele compreende retira o melhor de cada imagem
    model.add(MaxPooling2D(pool_size=(3, 3)))

    # técnica para reduzir o overfiting
    model.add(Dropout(0.7))
    model.add(Conv2D(batch_size * 2,(3,3), activation='relu'))
    model.add(Conv2D(batch_size * 2,(3,3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.5))
    model.add(Conv2D(batch_size * 3,(3, 3), activation='relu'))
    model.add(Conv2D(batch_size * 3,(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.3))

    # transforma a matriz em um array
    model.add(Flatten())

    # cada posição do array vai acessar todos os neuronios
    model.add(Dense(units=128, activation='relu'))
    model.add(Dropout(0.3))
    model.add(Dense(units=1, activation='sigmoid'))

    # Loss calcula o erro da rede, optimizer recebe a loss para tentar diminuir essa perda
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # configuração do rescale treinamento
    train_datagen = ImageDataGenerator(rescale=1. / 255,
                                       rotation_range=15,
                                       shear_range=0.2,
                                       zoom_range=0.2
                                       )

    # configuração do rescale teste
    test_datagen = ImageDataGenerator(rescale=1. / 255)

    # aplica o rescale
    training_set = train_datagen.flow_from_directory(images_training,
                                                     target_size=(image_width, image_height),
                                                     batch_size=batch_size,
                                                     class_mode='binary')

    # aplicando o rescale
    test_set = test_datagen.flow_from_directory(images_test,
                                                target_size=(image_width, image_height),
                                                batch_size=batch_size,
                                                class_mode='binary')

    # função auxiliar para diminuir a loss
    reduce_learning_rate = ReduceLROnPlateau(monitor='loss',
                                             factor=0.1,
                                             patience=2,
                                             cooldown=2,
                                             min_lr=0.00001,
                                             verbose=0)

    # repassando as duas funções
    callbacks = [reduce_learning_rate, checkpoint]

    # inicio do treinamento, passa todos os parâmetros já setados
    history = model.fit_generator(training_set,
                                  steps_per_epoch=4860 // batch_size,
                                  epochs=no_of_epochs,
                                  validation_data=test_set,
                                  validation_steps=64 // batch_size,
                                  callbacks=callbacks
                                  )

    # print da classificação criança ou não criança
    print(test_set.class_indices)

    # setando o método
    classifier_json = model.to_json()

    # salvando arquivo da rede em json
    with open('kids.json', 'w') as json_file:
        json_file.write(classifier_json)

    # salvando o resultado do treinamento no .h5
    model.save_weights(filepath)
