import random
from datetime import datetime
import threading
import time
import json
import pandas as pd
from pyspark.sql import SparkSession
from kafka import KafkaProducer
import matplotlib.pyplot as plt


# PARA 1, 5, 1O, 22 y 50 VARIABLES USAR ESTE CSV
df = pd.read_csv('/home/ubuntu/fabric-samples/red-propia/python_kafka/invented_data.csv', sep=',')
i=0
#dfONA.plot(x='Column1',color='red')
#plt.plot(df['var1'])
#plt.plot(df['var2'])
#plt.plot(df['var3'])

#plt.show()


# kafka producer: https://towardsdatascience.com/kafka-python-explained-in-10-lines-of-code-800e3e07dad1
producer = KafkaProducer(bootstrap_servers=['10.98.101.104:9092'],
                         value_serializer=lambda x:
                         json.dumps(x).encode('utf-8'))




#####################----- CON LOS CSV GENERADOS DE UN ENSAYO DE LA IBARMIA ----###########################

##### 1 VARIABLE ######
# coger todos los valores de una columna: Column1
array_np = df["nombre_programa"].to_numpy()
array_var1 = df["var1"].to_numpy()
array_var2 = df["var2"].to_numpy()
array_var3 = df["var3"].to_numpy()
array_alarma= df["alarma"].to_numpy()


## Simulador de Kafka

# https://stackoverflow.com/questions/43535997/execute-a-function-periodically-in-python-for-every-n-milliseconds-in-python-2
def generaterandom_ms_1_variable():
    # iterar el array y para evitar que pete con out of bounds poner este if
    global i
    if (i==2998):
        exit(0)

    # guardar en kafka
    np = array_np[i]
    var1 = array_var1[i]
    var2 = array_var2[i]
    var3 = array_var3[i]
    alarma = array_alarma[i]


    ts = str(time.time_ns() // 1_000_000)
    #print(type(ts))
    #print(ts)
    data = {'values':[{'id': 'nombreP', 'vd': np, 'ts': ts},
                      {'id': 'var1', 'vd': float(var1), 'ts': ts},
                      {'id': 'var2', 'vd': float(var2), 'ts': ts},
                      {'id': 'var3', 'vd': float(var3), 'ts': ts},
                      {'id': 'alarma', 'vd': alarma, 'ts': ts}]}
    producer.send('HyperLedger', value=data)
    #coger siguiente valor
    print(i)
    i=i+1
    #print(str(valor))

    # se ejecuta cada 1 (0.001 seg.) ms (mas o menos)
    threading.Timer(0.1, generaterandom_ms_1_variable).start()

generaterandom_ms_1_variable()
