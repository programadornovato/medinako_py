'''
LEE PARA ENTRENAR:
ESTE PROGRAMA RECIBE LOS AUDIOS DE LOS DISPOSITIVOS
QUE DESPUES SERAN LEIDOS PARA CREAR UN MODELO
'''
from datetime import datetime
import socket
import wave
from itertools import groupby
import os

sockEntrenar = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Recibimos datos desde cualquier ip al puerto 8080
sockEntrenar.bind(("", 8080))
# Si el socket se tarda mas de 1 segundo en recibir datos, se cierra
sockEntrenar.settimeout(2)
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
                data, addr = sockEntrenar.recvfrom(1024)
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
                    estado=""
                    contadorPaq=0
                    contadorArch=0
                    print ('direccion', direccionIP)
                    #Ciclo que leera cada frame (sonido/segundo) y lo guardara en la variable framesData que despues se guardara en un archivo
                    for content in group:
                        print ('\ttam=', len(content["data"])," contadorPaq=",contadorPaq)
                        #Si el tamaño es menor a 50 entonces es macadress del esp8266
                        if(len(content["data"])<100):
                            contenido=content["data"].decode("utf-8")
                            #Si el contenido recibido es igual a algun estado entonces  guardamos ese estado
                            if(contenido=="Vacio" or contenido=="Medio" or contenido=="Lleno"):
                                estado=contenido
                            #Si el contenido recibido es para inicializar el servidor y escuchar todo
                            elif(contenido=="1"):
                                pass
                            #Si el contenido no es ningun estado ni 1 entonces es una macadress
                            else:
                                macAddress=contenido
                                macAddress=content["data"].decode("utf-8")
                        else:
                            framesData.append(content["data"])
                            if( (contadorPaq%8)==0 and contadorPaq>0 ):
                                #Creamos el nombre del archivo con la direccion ip y la fecha de hoy
                                nombreArchivo = estado+str(contadorArch)+".wav"
                                print(nombreArchivo)
                                macAddressDir=macAddress.replace(':', '')
                                try:
                                    os.mkdir("audioRecibido/"+macAddressDir)
                                except FileExistsError:
                                    pass
                                nombreArchivo="audioRecibido/"+macAddressDir+"/"+nombreArchivo
                                #Si el archivo del modelo existe lo borramos
                                if os.path.exists(nombreArchivo):
                                    os.remove(nombreArchivo)

                                # Creamos un archivo con la fecha y hora y la direccion ip
                                file = wave.open(nombreArchivo, 'wb')
                                file.setnchannels(1)
                                file.setframerate(11111)
                                # en bytes. 1->8 bits, 2->16 bits
                                file.setsampwidth(1)
                                file.writeframes(b''.join(framesData))
                                file.close()
                                contadorArch=contadorArch+1
                                framesData=[]
                            contadorPaq=contadorPaq+1
                frames=[]
                framesData=[]
                data=""
except KeyboardInterrupt:
    print("Cerrando...")
    sockEntrenar.close()