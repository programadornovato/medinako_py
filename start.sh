#ACTIVAMOS CONDA CON LA VERSION PY36
conda activate py36
# NOS MOVEMOS A LA UBICACION DE MEDINAKO
cd /root/medinako/
# MATAMOS TODOS LOS PROCESOS DE PYTHON
kill -9 `pidof python`
# INICIAMOS LOS PROCESOS DE PYTHON DE PREDECIR, LEER ENTRENAR Y ENTRENAR
python Predecir.py 2>&1 | while read line; do echo `/bin/date` "$line" >> /root/medinako/logs/Predecir.log; done&
python LeeParaEntrenar.py 2>&1 | while read line; do echo `/bin/date` "$line" >> /root/medinako/logs/LeeParaEntrenar.log; done&
FLASK_APP=Entrenar.py FLASK_ENV=Entrenar.py flask run --host=0.0.0.0 2>&1 | while read line; do echo `/bin/date` "$line" >> /root/medinako/logs/Entrenar.log; done&
