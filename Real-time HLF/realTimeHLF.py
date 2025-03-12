import os
import hashlib
import time  # Para obtener el timestamp en nanosegundos
import csv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import json
import pandas as pd


# Para inicializar las variables export
#os.environ['FABRIC_CFG_PATH'] = '/home/ubuntu/fabric-samples/red-propia'
#os.environ['CORE_PEER_TLS_ENABLED'] = 'false'
#os.environ['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
#os.environ['CORE_PEER_MSPCONFIGPATH'] = '/home/ubuntu/fabric-samples/red-propia/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp'
#os.environ['CORE_PEER_ADDRESS'] = 'peer0.org1.example.com:7051'


def invoke_chaincode(timestamp, istart, iend, program, fhash):
    # Define el comando peer chaincode invoke como una lista de argumentos
    command = [
        'peer', 'chaincode', 'invoke',
        '-o', 'orderer.example.com:7050',
        '-C', 'mychannel',
        '-n', 'realtimechaincode',
        '--peerAddresses', 'peer0.org1.example.com:7051',
        '--peerAddresses', 'peer0.org2.example.com:8051',
        '-c', f'{{"function":"CreateRecord","Args":["{timestamp}","{istart}","{iend}","{program}","{fhash}"]}}'

    ]
    try:
        # Ejecuta el comando y captura la salida
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Si el comando se ejecuta correctamente, imprime la salida
        if result.returncode == 0:
            print("Chaincode invoke successful:")
            print(result.stdout)
        else:
            print("Error during chaincode invoke:")
            print(result.stderr)

    except Exception as e:
        print(f"Failed to invoke chaincode: {e}")


# Función para obtener la información del canal mediante el comando peer
def obtener_info_blockchain():
    try:
        # Ejecutar el comando peer channel getinfo
        resultado = subprocess.run(['peer', 'channel', 'getinfo', '-c', 'mychannel'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Si el comando se ejecutó correctamente
        if resultado.returncode == 0:
            # Buscar la línea que contiene "Blockchain info:"
            for linea in resultado.stdout.splitlines():
                if "Blockchain info:" in linea:
                    # Extraer la parte JSON de la línea
                    info_json = linea.split(": ", 1)[1]
                    return json.loads(info_json)
        else:
            print(f"Error ejecutando comando: {resultado.stderr}")
            return None
    except Exception as e:
        print(f"Error obteniendo información de la blockchain: {str(e)}")
        return None



# Función para calcular el hash de un archivo
def calcular_hash_csv(file_path):
    sha256_hash = hashlib.sha256()
    hash_csv=''

    try:
        with open(file_path, "rb") as f:
            # Leer el archivo en bloques para calcular el hash
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        #print(f"Hash del archivo {file_path}: {sha256_hash.hexdigest()}")
        hash_csv = sha256_hash.hexdigest()
    except FileNotFoundError:
        print(f"Archivo no encontrado: {file_path}")
    except Exception as e:
        print(f"Error al calcular el hash: {e}")

    return hash_csv


# Clase para manejar eventos de modificación en las carpetas
class CSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Si el archivo creado es un CSV, calcular el hash
        if not event.is_directory and event.src_path.endswith(".csv"):
            timestamp_ns = int(time.time())  # Devuelve el tiempo en segundos
            #print(timestamp_s)
            #timestamp_ns = time.time_ns()
            # print(type(timestamp_ns))
            print(f"Nuevo archivo CSV detectado: {event.src_path}")

            # Imprimir el timestamp en nanosegundos
            print(f"Timestamp en nanosegundos: {timestamp_ns}")

            # Obtener las subcarpetas hasta el archivo CSV
            directorio_base = "/home/ubuntu/fabric-samples/red-propia/python_kafka/csvs/"

            # Obtener la ruta relativa desde el directorio base
            ruta_relativa = os.path.relpath(event.src_path, directorio_base)
            print(ruta_relativa)

            # Cargar el CSV
            df = pd.read_csv("/home/ubuntu/fabric-samples/red-propia/python_kafka/csvs/" + ruta_relativa)

            # Extraer los valores
            interval_start = df["interval_start"].iloc[0]
            interval_end = df["interval_end"].iloc[0]
            program_name = df["program_name"].iloc[0]

            print(interval_start, interval_end, program_name)

            # Imprimir un mensaje cada vez que llega un nuevo archivo CSV
            print(f"¡Nuevo archivo CSV añadido: {os.path.basename(event.src_path)}!")

            # Llamar a la función para calcular el hash del archivo
            hash= calcular_hash_csv(event.src_path)
            print(f"Hash del archivo:  {hash}")

            # Guardar el world state mediante subprocess
            # Llama a la función para ejecutar el comando
            invoke_chaincode(timestamp_ns, interval_start, interval_end, program_name, hash)

            archivo_csv = '/home/ubuntu/fabric-samples/red-propia/registro_archivos_nuevos.csv'
            if not os.path.exists(archivo_csv):
                with open(archivo_csv, mode='w', newline='') as archivo:
                    escritor_csv = csv.writer(archivo)
                    escritor_csv.writerow(["Timestamp", "Path", "Hash"])
            # Finalmente guardar el timestamp, la ruta relativa y el hash en un fichero csv
            with open(archivo_csv, mode='a', newline='') as archivo_csv:
                escritor_csv = csv.writer(archivo_csv)
                escritor_csv.writerow([timestamp_ns, ruta_relativa, hash])

            # Obtener la información del bloque actual
            info_blockchain = obtener_info_blockchain()
            if info_blockchain:
                # Extraer los datos relevantes
                block_number = info_blockchain['height']
                current_block_hash = info_blockchain['currentBlockHash']
                previous_block_hash = info_blockchain['previousBlockHash']

                archivo_bc = '/home/ubuntu/fabric-samples/red-propia/blockchain_info.csv'
                archivo_existe = os.path.exists(archivo_bc)

                if not archivo_existe:
                    # Si el archivo CSV no existe, escribir la cabecera
                    with open(archivo_bc, mode='w', newline='') as archivo:
                        escritor_csv = csv.writer(archivo)
                        escritor_csv.writerow(["Timestamp", "Block Number", "Current Block Hash", "Previous Block Hash"])

                # Escribir en el archivo CSV
                with open(archivo_bc, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp_ns, block_number, current_block_hash, previous_block_hash])

                # Imprimir la información en la consola
                print(f"Block Number: {block_number}")
                print(f"Current Block Hash: {current_block_hash}")
                print(f"Previous Block Hash: {previous_block_hash}")
            else:
                print("No se pudo obtener la información del bloque.")


# Función principal para configurar la monitorización
def monitorear_carpetas(ruta_base):
    # Inicializa el observador
    event_handler = CSVHandler()
    observer = Observer()

    # Recorre todas las subcarpetas de la ruta base (USUARIO/ETAPA/SLOT)
    for root, dirs, files in os.walk(ruta_base):
        print(f"Observando la carpeta: {root}")
        # Observa cada carpeta y sus subcarpetas
        observer.schedule(event_handler, path=root, recursive=False)

    # Inicia el observador
    observer.start()
    try:
        while True:
            # Mantén el observador corriendo
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# Ejecutar la monitorización
if __name__ == "__main__":
    # Ruta base que contiene las carpetas de los USUARIOS
    ruta_base = "/home/ubuntu/fabric-samples/red-propia/python_kafka/csvs"  # Cambia esto a la ruta de tu sistema
    monitorear_carpetas(ruta_base)
