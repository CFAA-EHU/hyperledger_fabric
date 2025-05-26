import os
import hashlib
import time
import csv
import json
import pandas as pd
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def invoke_chaincode(timestamp, istart, iend, program, fhash):
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
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Chaincode invoke successful:")
            print(result.stdout)
        else:
            print("Error during chaincode invoke:")
            print(result.stderr)
    except Exception as e:
        print(f"Failed to invoke chaincode: {e}")

def obtener_info_blockchain():
    try:
        result = subprocess.run(['peer', 'channel', 'getinfo', '-c', 'mychannel'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "Blockchain info:" in line:
                    info_json = line.split(": ", 1)[1]
                    return json.loads(info_json)
    except Exception as e:
        print(f"Error retrieving blockchain info: {str(e)}")
    return None

def calcular_hash_csv(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error calculating hash: {e}")
        return ""

class CSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".csv"):
            timestamp_ns = int(time.time())
            print(f"Detected new CSV file: {event.src_path}")
            print(f"Timestamp (s): {timestamp_ns}")

            base_dir = "/home/ubuntu/fabric-samples/red-propia/python_kafka/csvs/"
            relative_path = os.path.relpath(event.src_path, base_dir)
            print(f"Relative path: {relative_path}")

            df = pd.read_csv(event.src_path)
            interval_start = df["interval_start"].iloc[0]
            interval_end = df["interval_end"].iloc[0]
            program_name = df["program_name"].iloc[0]

            # Generate Verifiable Credential (VC)
            vc = {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    {"name": "https://schema.org/name"}
                ],
                "id": f"urn:uuid:{timestamp_ns}",
                "type": ["VerifiableCredential"],
                "issuer": "did:key:z6MkgcE168tsxJyMhVu5h8MHkN8URVDkSnbn3h1R52mwoGJc",
                "issuanceDate": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "credentialSubject": {
                    "id": f"did:example:{timestamp_ns}",
                    "name": "Ibarmia THR 16 Realtime",
                    "interval_start": interval_start,
                    "interval_end": interval_end,
                    "program_name": program_name,
                    "data": df.to_dict(orient="records")
                }
            }

            # Save VC JSON
            vc_path = f"/home/ubuntu/fabric-samples/red-propia/vcs/vc_{timestamp_ns}.json"
            os.makedirs(os.path.dirname(vc_path), exist_ok=True)
            with open(vc_path, 'w') as f:
                json.dump(vc, f, indent=2)
            print(f"VC saved at: {vc_path}")

            # Hash the VC file (not original CSV)
            hash_vc = calcular_hash_csv(vc_path)
            print(f"VC hash: {hash_vc}")

            invoke_chaincode(timestamp_ns, interval_start, interval_end, program_name, hash_vc)

            # Log file records
            log_csv_path = '/home/ubuntu/fabric-samples/red-propia/registro_archivos_nuevos.csv'
            os.makedirs(os.path.dirname(log_csv_path), exist_ok=True)
            if not os.path.exists(log_csv_path):
                with open(log_csv_path, 'w', newline='') as f:
                    csv.writer(f).writerow(["Timestamp", "Path", "Hash"])
            with open(log_csv_path, 'a', newline='') as f:
                csv.writer(f).writerow([timestamp_ns, relative_path, hash_vc])

            # Blockchain info
            info = obtener_info_blockchain()
            if info:
                block_num = info['height']
                current_hash = info['currentBlockHash']
                prev_hash = info['previousBlockHash']

                bc_info_path = '/home/ubuntu/fabric-samples/red-propia/blockchain_info.csv'
                if not os.path.exists(bc_info_path):
                    with open(bc_info_path, 'w', newline='') as f:
                        csv.writer(f).writerow(["Timestamp", "Block Number", "Current Block Hash", "Previous Block Hash"])
                with open(bc_info_path, 'a', newline='') as f:
                    csv.writer(f).writerow([timestamp_ns, block_num, current_hash, prev_hash])
            else:
                print("Blockchain info not available.")

def monitorear_carpetas(ruta_base):
    event_handler = CSVHandler()
    observer = Observer()
    for root, _, _ in os.walk(ruta_base):
        print(f"Watching folder: {root}")
        observer.schedule(event_handler, path=root, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    ruta_base = "/home/ubuntu/fabric-samples/red-propia/python_kafka/csvs"
    monitorear_carpetas(ruta_base)

