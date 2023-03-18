'''
ENTRENAR: CREA EL ARCHIVO hdf5 EXCLUSIVO DE ESTE RECIPIENTE
1.- LEEMOS LOS ARCHIVOS VACIO,MEDIO,LLENO (20 ARCHIVOS DE CADA UNO)
2.- EXTRAEMOS LOS MFCC DE CADA ARCHIVO
3.- GUARDAMOS LOS MFCC EN UNA MATRIZ
4.- GUARDAMOS LA MATRIZ EN UN ARCHIVO
5.- CARGAMOS EL MODELO
6.- ENTRENAMOS EL MODELO
7.- GUARDAMOS EL MODELO
'''
import os
from flask import Flask,request
from os import mkdir
import librosa
import numpy as np
import pandas as pd
import mysql.connector
import Conexion
mydb = mysql.connector.connect(
  host=Conexion.host,
  user=Conexion.user,
  passwd=Conexion.passwd,
  database=Conexion.database
)
cantidadAudios=20
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

app=Flask(__name__)
@app.route('/listo-entrenar')
def index():
    macAddress=request.args.get('mac')
    macAddressDir=macAddress.replace(':', '')
    #macAddressDir="8CAAB5D6F806"
    carpeta="audioRecibido/"+macAddressDir
    vacio=0
    medio=0
    lleno=0
    for estado in ["Vacio", "Medio", "Lleno"]:
        for i in range(0, cantidadAudios, 1):
            nombreArchivo=carpeta+"/"+estado+str(i)+".wav"
            if os.path.isfile(nombreArchivo):
                print("El archivo existe:",nombreArchivo)
                if estado=="Vacio":
                    vacio=vacio+1
                elif estado=="Medio":
                    medio=medio+1
                elif estado=="Lleno":
                    lleno=lleno+1
            else:
                print("El no archivo existe.",nombreArchivo)
    resultado="{\"data\":["
    resultado=resultado+"{\"Vacio\":\""+str(vacio)+"\",\"Medio\":\""+str(medio)+"\",\"Lleno\":\""+str(lleno)+"\"}"
    resultado=resultado+"]}"
    return resultado

@app.route('/entrenar')
def index2():
    features=[]
    macAddress=request.args.get('mac')
    macAddressDir=macAddress.replace(':', '')
    #Creamos el nombre del modelo
    archivoModeo='modelos/'+macAddressDir+'.hdf5'
    #Si el archivo del modelo existe lo borramos
    if os.path.exists(archivoModeo):
        os.remove(archivoModeo)
    carpeta="audioRecibido/"+macAddressDir+"/"
    
    
    class_label=1
    for estado in ["Vacio", "Medio", "Lleno"]:
        for i in range(0, cantidadAudios, 1):
            #file_name=carpeta+"/"+estado+str(i)+".wav"
            file_name = os.path.join(os.path.abspath(carpeta),estado+str(i)+".wav")
            if os.path.isfile(file_name):
                #print("file_name=",file_name,"----class_label=",class_label)
                #Extraemos el MFCC y los guardamos en data
                data = extract_features(file_name)
                #Insertamos en el arreglo el valor del MFCC junto a su etiqueta
                features.append([data, str(class_label)])
        class_label=class_label+1
    # convertimos el arreglo en un DataFrame de pandas y lo dividimos en 2 columnas ('feature','class_label')
    

    featuresdf = pd.DataFrame(features, columns=['feature','class_label'])
    
    print('finalizo la extraccion de ', len(featuresdf), ' archivos') 
    features = featuresdf.loc[1]
    print(list(features))

    ############################
    #Convertir los datos y etiquetas
    ############################
    '''
    Para transformar los datos categóricos a numéricos usaremos «LabelEncoder» y así conseguiremos que el modelo sea capaz de entenderlos.
    '''
    from sklearn.preprocessing import LabelEncoder
    from tensorflow.keras.utils import to_categorical

    # Convertimos los rasgos MFCC a arreglo numpy
    X = np.array(featuresdf.feature.tolist())
    # Convertimos las etiquetas a arreglo numpy
    y = np.array(featuresdf.class_label.tolist())

    # Codificamos las etiquetas con sklearn.preprocessing para que coloque un 1 y lo demas lo rellene con 0 por ejemplo
    le = LabelEncoder()
    yy = to_categorical(le.fit_transform(y))
    print("Mostramos el valor de \"X\" que son los rasgos en MFCC")
    print(X)
    print("Mostramos el valor de \"y\" que son las etiquetas osea classID que extrajimos de UrbanSound8K_csv")
    print(y)
    print("Mostramos el valor de \"yy\" que son las etiquetas (classID) pero transformadas con sklearn.preprocessing. Por ejemplo:")
    print("El classID=3 no dara una arreglo asi [0.0.0.1.0.0.0.0.0.0]")
    print("El classID=2 no dara una arreglo asi [0.0.1.0.0.0.0.0.0.0]")
    print("El classID=1 no dara una arreglo asi [0.1.0.0.0.0.0.0.0.0]")
    print(yy)


    ###########################################
    #Dividir los datos en entrenamiento y test
    ###########################################
    #Dividimos el conjunto de datos en dos bloques (80% y 20%) y de ellos sacamos valores de X y de Y
    from sklearn.model_selection import train_test_split 
    x_train, x_test, y_train, y_test = train_test_split(X, yy, test_size=0.2, random_state = 42)

    #####################
    # Construir el modelo
    #####################
    '''
    Construimos una red neuronal mediante un perceptrón multicapa (MLP) usando Keras y un backend de Tensorflow.
    Se plantea un modelo secuencial para que podamos construir el modelo capa por capa.
    Se plantea una arquitectura de modelo simple, compuesta por:
    - Capa de entrada con 40 nodos, ya que la función MFCC de extracción de características nos devuelve un conjunto de datos de 1×40
    - Capas ocultas de 256 nodos, estas capas tendrán una capa densa con una función de activación de tipo ReLu, (se ha demostrado que esta función de activación funciona bien en redes neuronales). 
        También destacar que aplicaremos un valor de Dropout del 50% en nuestras dos primeras capas. Esto excluirá al azar los nodos de cada ciclo de actualización, lo que a su vez da como resultado 
        una red que es capaz de responder mejor a la generalización y es menos probable que se produzca sobreajuste en los datos de entrenamiento.
    - Capa de salida de 10 nodos, que coinciden con el número de clasificaciones posibles. La activación es para nuestra capa de salida una función softmax. 
        Softmax hace que la salida sume 1, por lo que la salida puede interpretarse como probabilidades. El modelo hará su predicción según la opción que tenga la mayor probabilidad
    '''
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
    from tensorflow.keras.layers import Convolution2D, MaxPooling2D
    from tensorflow.keras.optimizers import Adam
    from sklearn import metrics 

    num_labels = yy.shape[1]
    
    # Declaramos un modelo
    model = Sequential()
    #Creamos una capa que recibira 40 nodos de entrada y 256 capas ocultas
    model.add(Dense(256, input_shape=(40,)))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(num_labels))
    model.add(Activation('softmax'))

    #####################
    #Compilar el modelo
    #####################
    '''
    Para compilar nuestro modelo, utilizaremos los siguientes tres parámetros:
    - Función de pérdida: utilizaremos categorical_crossentropy. Esta es la opción más común para la clasificación. Una puntuación más baja indica que el modelo está funcionando mejor.
    - Métricas: utilizaremos la métrica de accuracy que nos permitirá ver la precisión en los datos de validación cuando entrenemos el modelo.
    - Optimizador: aquí usaremos adam, que generalmente es un buen optimizador para muchos casos de uso.
    '''
    # Compilamos el modelo
    model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer='adam')
    # Imprimimos el resultado de la compilacion
    model.summary()
    # Calcular la precisión previa al entrenamiento
    score = model.evaluate(x_test, y_test, verbose=0)
    accuracy = 100*score[1]
    print("Precisión previa al entrenamiento: %.4f%%" % accuracy)


    #####################
    #Entrenar el modelo
    #####################
    '''
    Se empieza probando con un número de épocas bajo y se prueba hasta ver donde alcanza un valor asintótico en el que por más que subamos las épocas no conseguimos que el modelo mejore significativamente.
    Por otro lado, el tamaño del lote debe ser suficientemente bajo, ya que tener un tamaño de lote grande puede reducir la capacidad de generalización del modelo.
    '''
    from tensorflow.keras.callbacks import ModelCheckpoint 
    from datetime import datetime 

    num_epochs = 100
    num_batch_size = 32
    #Creamos un el archivo del modelo
    checkpointer = ModelCheckpoint(filepath=archivoModeo, verbose=0, save_best_only=True)
    start = datetime.now()
    model.fit(x_train, y_train, batch_size=num_batch_size, epochs=num_epochs,validation_data=(x_test, y_test), callbacks=[checkpointer], verbose=0)
    duration = datetime.now() - start
    print("Entrenamiento completado en un tiempo de: ", duration)



    ########################
    #Evaluar el modelo
    ########################
    '''
    Finalmente, para determinar la precisión del modelo generado, llamamos a la función evaluate y le pasamos los datos de test que hemos definido previamente.
    '''
    # Evaluamos el modelo con el set de datos de testing
    score = model.evaluate(x_test, y_test, verbose=0)
    print("Testing Accuracy: ", score[1])

    return str(score[1])

@app.route('/existe-modelo')
def existeModelo():
    macAddress=request.args.get('mac')
    macAddressDir=macAddress.replace(':', '')
    archivoModelo="modelos/"+macAddressDir+".hdf5"
    #Validar que el archivo existe
    if os.path.isfile(archivoModelo):
        return "1"
    else:
        return "0"

@app.route('/lista-mediciones')
def listaMediciones():
    import json
    from datetime import date, datetime
    if 'mac' in request.args:
        macAddress=request.args.get('mac')
        fecha=request.args.get('fecha')
        #macAddressDir=macAddress.replace(':', '')
        sql = "SELECT ip,idDispositivo,archivoAudio,estado,fechaCreacion FROM mediciones WHERE idDispositivo='"+macAddress+"' and fechaCreacion>='"+fecha+" 00:00:00'  AND fechaCreacion<='"+fecha+" 23:59:59' order by fechaCreacion desc; ";
        print(sql)
        mycursor = mydb.cursor()
        mycursor.execute(sql)
        row_headers=[x[0] for x in mycursor.description] #this will extract row headers
        rv = mycursor.fetchall()
        mydb.commit()
        json_data=[]
        for result in rv:
            print(result)
            json_data.append(dict(zip(row_headers,result)))
        jsonString="{\"data\":"
        jsonString=jsonString + json.dumps(json_data, default=str)
        jsonString=jsonString + "}"
        mycursor.close()
        return jsonString
    else:
        jsonString="{\"data\":"
        jsonString=jsonString + "[]"
        jsonString=jsonString + "}"
        return jsonString
#INICIAMSO FLASK
if __name__ == "__main__":
  app.run(host="0.0.0.0")
