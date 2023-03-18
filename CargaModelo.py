from keras.models import load_model
import librosa
import numpy as np
import pandas as pd
#Extraemos los MFCC de cada archivo (osea convertimos el audio en una representacion grafica)
def extract_features(file_name):
    try:
        audio, sample_rate = librosa.load(file_name, res_type='kaiser_fast') 
        mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
        mfccsscaled = np.mean(mfccs.T,axis=0)
    except Exception as e:
        print("Error encountered while parsing file: ", file_name)
        return None 
    return mfccsscaled

def nivelDeLleno(rutaModelo,archivoAudio):
    model = load_model(rutaModelo)
    datosAudio = []
    #Extraemos el MFCC y los guardamos en rasgosArchivo
    rasgosArchivo = extract_features(archivoAudio)
    datosAudio.append([rasgosArchivo])
    datosAudioDataframe = pd.DataFrame(datosAudio, columns=['feature'])
    datosAudioNP = np.array(datosAudioDataframe.feature.tolist())

    prediccion = model.predict(datosAudioNP)
    listaEstados = np.array(['Vacio', 'Medio', 'Lleno'], dtype=np.object)
    numeroPrediccion = np.argmax(prediccion, axis = 1)
    exactitud=prediccion[0][numeroPrediccion[0]]
    return listaEstados[numeroPrediccion[0]],exactitud
    #print(listaEstados[numeroPrediccion[0]])
#estadoLleno=nivelDeLleno(rutaModelo='saved_models/weights.best.basic_mlp.hdf5',archivoAudio='audio/medio_05.wav')
#print(estadoLleno)