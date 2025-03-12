from kafka import KafkaConsumer
import json
from pyspark.sql import SparkSession
from pyspark.sql import Row
import csv
from datetime import datetime, timedelta

# Configura SparkSession para procesamiento de datos en tiempo real
spark = SparkSession.builder \
    .appName("Kafka Real-Time Consumer") \
    .getOrCreate()

# Configura el Kafka Consumer
consumer = KafkaConsumer(
    'HyperLedger',  # Nombre del topic
    bootstrap_servers=['10.98.101.104:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Variables para el procesamiento por intervalos
current_program_name = None
interval_start_time = None
interval_data = []
csv_file_path_template = "/home/ubuntu/fabric-samples/red-propia/python_kafka/csvs/rt_{start_time}.csv"

print("Esperando mensajes del Kafka Producer en tiempo real...")


# Función para calcular estadísticas y guardar CSV
def process_interval(interval_data, program_name):
    if not interval_data:
        return

    # Calcular estadísticas
    var1_values = [row["var1"] for row in interval_data if row["var1"] is not None]
    var2_values = [row["var2"] for row in interval_data if row["var2"] is not None]
    var3_values = [row["var3"] for row in interval_data if row["var3"] is not None]

    # Recolectar alarmas únicas en el intervalo
    alarmas = list({row["alarma"] for row in interval_data if "Alarma" in row["alarma"]})
    alarmas_str = "|".join(alarmas) if alarmas else "No"

    var1_mean = sum(var1_values) / len(var1_values) if var1_values else None
    var2_mean = sum(var2_values) / len(var2_values) if var2_values else None
    var3_mean = sum(var3_values) / len(var3_values) if var3_values else None

    # Obtener el inicio y fin del intervalo basado en los timestamps
    start_time = int(interval_data[0]["timestamp"].timestamp())
    end_time = int(interval_data[-1]["timestamp"].timestamp())

    # Crear CSV
    csv_file_path = csv_file_path_template.format(start_time=start_time)
    header = ["interval_start", "interval_end", "program_name", "var1_mean", "var2_mean", "var3_mean", "alarmas"]

    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerow([
            start_time,
            end_time,
            program_name,
            var1_mean,
            var2_mean,
            var3_mean,
            alarmas_str
        ])

    print(f"Intervalo procesado y guardado en: {csv_file_path}")

# Consumir mensajes en tiempo real y procesarlos
try:
    for message in consumer:
        # Extraer el payload y el timestamp
        payload = message.value
        kafka_ts = payload['values'][0]['ts']
        kafka_time = datetime.fromtimestamp(float(kafka_ts) / 1000.0)
        values = {entry['id']: entry['vd'] for entry in payload['values']}

        # Actualizar nombre del programa
        new_program_name = values.get('nombreP', None)
        if current_program_name and new_program_name != current_program_name:
            # Procesar el intervalo actual al cambiar de programa
            process_interval(interval_data, current_program_name)
            interval_data = []  # Reinicia los datos del intervalo
            interval_start_time = kafka_time  # Reinicia el inicio del intervalo al primer timestamp del nuevo programa

        # Si no hay un intervalo en curso, inicializa uno
        if interval_start_time is None:
            interval_start_time = kafka_time

        # Agregar datos al intervalo actual
        interval_data.append({
            "timestamp": kafka_time,
            "var1": values.get('var1', None),
            "var2": values.get('var2', None),
            "var3": values.get('var3', None),
            "alarma": values.get('alarma', None)
        })

        # Si ha pasado un minuto, procesa el intervalo
        if (kafka_time - interval_start_time) >= timedelta(minutes=1):
            process_interval(interval_data, new_program_name)
            interval_data = []  # Reinicia los datos del intervalo
            interval_start_time = kafka_time  # Reinicia el inicio del intervalo al timestamp actual

        # Actualiza el programa actual
        current_program_name = new_program_name

except KeyboardInterrupt:
    print("Consumo interrumpido manualmente")
    # Procesar cualquier intervalo restante al finalizar
    if interval_data:
        process_interval(interval_data, current_program_name)
finally:
    # Parar SparkSession
    spark.stop()
    print("Sesión de Spark terminada")

