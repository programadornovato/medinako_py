'''
PREDECIR
ESTE PROGRAMA SE ENCARGA DE RECIBIR LOS AUDIOS DE LOS DISPOSITIVOS 
PREDECIR SU ESTADO (VACIO,MEDIO,LLENO) Y AGREGARLAS A LA BASE DE DATOS
'''
from datetime import datetime
import socket
import wave
from itertools import groupby
import CargaModelo as model
#pip install mysql-connector
import mysql.connector
import Conexion
import os
mydb = mysql.connector.connect(
  host=Conexion.host,
  user=Conexion.user,
  passwd=Conexion.passwd,
  database=Conexion.database
)
mycursor = mydb.cursor()
sockPredecir = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Recibimos datos desde cualquier ip al puerto 80
sockPredecir.bind(("", 80))
# Si el socket se tarda mas de 1 segundo en recibir datos, se cierra
sockPredecir.settimeout(2)
#Iniciamos los frames para guardar el archivo
frames = []
#Almacenamos la direccion ip de del paquete recibido
direccionIP=""
#Almacenamos el puerto de del paquete recibido
data=""
# Se sale si precionamos ctrl + c
try:
    # Creamos un ciclo infinito
    while True:
        # Se sale si no se reciben datos por mas de 1 segundo
        try:
            #Creamos un bucle infinito para que siempre este escuchando
            while True:
                data, addr = sockPredecir.recvfrom(1024)
                direccionIP=str(addr[0])
                print (len(data))
                frames.append({'data':data,'direccion':direccionIP})
        #Si se dejo de recibir datos por mas de 1 segundo, se sale del ciclo
        except socket.timeout:
            # Si se recibio algo, se guarda en un archivo
            if(len(data)>0):
                #Agrupamos los frames por direccion ip
                frames.sort(key=lambda content: content['direccion'])
                groups = groupby(frames, lambda content: content['direccion'])
                #Hacemos un ciclo por cada direccion ip (grupo)
                for direccionIP, group in groups:
                    #Esta variable almacenara los frames (sonido/segundo) que despues se guardaran en un archivo
                    framesData=[]
                    macAddress=""
                    print ('direccion', direccionIP)
                    #Ciclo que leera cada frame (sonido/segundo) y lo guardara en la variable framesData que despues se guardara en un archivo
                    for content in group:
                        print ('\t', len(content["data"]))
                        # Si el tamano es menor a 50 entonces es macadress del esp8266
                        if(len(content["data"])<100):
                            contenido=content["data"].decode("utf-8")
                            #Si el contenido recibido es para inicializar el servidor y escuchar todo
                            if(contenido=="1"):
                                pass
                            else:
                                macAddress=content["data"].decode("utf-8")
                        else:
                            framesData.append(content["data"])
                    macAddressDir=macAddress.replace(':', '')
                    #Creamos el nombre del archivo con la direccion ip y la fecha de hoy
                    nombreArchivoAudio = direccionIP+"-"+datetime.now().strftime('%Y-%m-%d-%H-%M-%S')+".wav"
                    print("nombreArchivoAudio=",nombreArchivoAudio)
                    #Si estamos en windows, se crea un archivo en la carpeta de windows, si no, en la carpeta de linux
                    nombreArchivoAudio="audioRecibido/"+nombreArchivoAudio
                    # Creamos un archivo con la fecha y hora y la direccion ip
                    file = wave.open(nombreArchivoAudio, 'wb')
                    file.setnchannels(1)
                    file.setframerate(11111)
                    # en bytes. 1->8 bits, 2->16 bits
                    file.setsampwidth(1)
                    file.writeframes(b''.join(framesData))
                    file.close()
                    file_size = os.path.getsize(nombreArchivoAudio)
                    #Si el tamano del archivo es mayor a 5KB hacemos la prediccion del sonido
                    if( file_size>5000 ):
                        #Si el modelo de esta mac existe la usamos de lo contrario usamos el archivo estandar
                        archivoModelo="modelos/"+macAddressDir+".hdf5"
                        if os.path.isfile(archivoModelo)==False:
                            archivoModelo="modelos/estandar.hdf5"
                        print("archivoModelo=",archivoModelo)
                        try:
                            estadoLleno,exactitud=model.nivelDeLleno(rutaModelo=archivoModelo,archivoAudio=nombreArchivoAudio)
                            print("---ESTADO:",estadoLleno," | Exactitud de prediccion:",exactitud)
                        except:
                            estadoLleno="Intente de nuevo"
                            print("---ESTADO:",estadoLleno)
                        #Insertamos en la tabla mediociones las mediciones de este dispositivo
                        sql = "INSERT INTO mediciones(ip,idDispositivo,archivoAudio,estado) VALUES (%s,%s,%s,%s)"
                        val = (direccionIP,macAddress,nombreArchivoAudio,estadoLleno)
                        #validar si se inserto correctamente
                        try:
                            mycursor.execute(sql, val)
                            mydb.commit()
                        except mysql.connector.Error as error:
                            print("Error: No se pudo insertar la medicion ",error)
                        finally:
                            if os.path.exists(nombreArchivoAudio):
                                #os.remove(nombreArchivoAudio)
                                #print(nombreArchivoAudio," borrado")
                                pass
                            #mycursor.close()
                            pass
                frames=[]
                framesData=[]
                data=""
except KeyboardInterrupt:
    print("Cerrando...")
    sockPredecir.close()