# Despliegue en Hyperledger Fabric

Para desplegar una red de Hyperledger Fabric, debemos configurar y generar varios archivos esenciales y seguir una serie de comandos específicos. En este ejemplo, se va a desplegar una red con dos máquinas virtuales, donde se desplegará un orderer y dos organizaciones. El orderer y la organización 1 (Org1) estarán en la máquina virtual 1 (MV1); la organización 2 (Org2) estará en la máquina virtual 2 (MV2).

El archivo _crypto-config.yaml_ es crucial para definir la estructura y configuración de la red blockchain. Este archivo especifica las organizaciones participantes, sus dominios, los nodos de tipo orderer y los pares (peers). También define la generación de materiales criptográficos (certificados y llaves) necesarios para la autenticación y comunicación segura entre los nodos de la red.

- __OrdererOrgs__: Define las organizaciones que actúan como nodos orderer. Se especifican el nombre de la organización, el dominio y se activan las Organizational Units (OU) para los nodos.
- __PeerOrgs__: Define las organizaciones que actúan como pares. En este ejemplo, hay dos organizaciones, Org1 y Org2, cada una con un nodo de par. Se definen el nombre de la organización, el dominio, se activan las Organizational Units (OU) para los nodos y se define el número de nodos de par junto con el número de usuarios asociados a la organización.

Para generar los materiales criptográficos definidos en el archivo _crypto-config.yaml_, utilizamos la herramienta cryptogen.

_cryptogen generate --config=./crypto-config.yaml_

La variable de entorno FABRIC_CFG_PATH se utiliza para especificar la ruta donde se encuentran los archivos de configuración de Fabric, como configtx.yaml y otros archivos YAML necesarios para configurar y desplegar la red.

_export FABRIC_CFG_PATH=/home/ubuntu/fabric-samples/red-propia_

Para configurar y desplegar una red de Hyperledger Fabric, el archivo configtx.yaml es fundamental. Este archivo define la configuración del canal, las organizaciones participantes y las políticas de consenso. Aquí se explicará la estructura y contenido del archivo configtx.yaml que se utiliza para la configuración de la red.

- Organizations: Este apartado define las organizaciones participantes en la red, incluyendo tanto los nodos orderer como los nodos peer.
  - OrdererOrg: Define la organización del nodo orderer. Incluye el nombre de la organización, su ID, el directorio MSP (Membership Service Provider) y las políticas de acceso (lectura, escritura, administración y validación de bloques).
  - Org1: Define la primera organización peer (Org1). Incluye el nombre, ID, directorio MSP, políticas de acceso y los anchor peers.
  - Org2: Define la segunda organización peer (Org2) con la misma estructura a la de Org1.
- Capabilitites: Este apartado define las capacidades del canal, el orden y la aplicación. En este caso, se utilizan las capacidades de la versión 2.0 de Hyperledger Fabric.
- Application: Define las configuraciones por defecto para las aplicaciones, incluyendo políticas de acceso y capacidades.
- Orderer: Define las configuraciones por defecto del nodo orderer, incluyendo el tipo de orden, direcciones, tamaño de los lotes y políticas de acceso.
- Channel: Define las configuraciones por defecto para los canales, incluyendo las políticas de acceso y capacidades.
- Profiles: Define los perfiles de configuración para la red, incluyendo el genesis block y la configuración del canal.
  - TwoOrgsOrdererGenesis: Define el perfil para el genesis block, incluyendo las organizaciones orderer y sus capacidades.
  - TwoOrgsChannel: Define el perfil para la configuración del canal, incluyendo las organizaciones participantes y sus capacidades.

El siguiente paso que hay que hacer es crear el canal. Con el siguientes comando, se va a configurar y generar el archivo genesis block:
configtxgen -profile TwoOrgsOrdererGenesis -outputBlock ./channel-artifacts/genesis.block -channelID system-channel
Y la transacción del canal, lo que permite proceder con la creación y gestión de la red blockchain en Hyperledger Fabric.
configtxgen -profile TwoOrgsChannel -outputCreateChannelTx ./channel-artifacts/channel.tx -channelID mychannel
Para continuar con la configuración y despliegue de una red de Hyperledger Fabric, es necesario definir y actualizar los anchor peers para cada organización. Los peers de anclaje son nodos peer dentro de una organización que actúan como puntos de comunicación principales para el canal.
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org1MSPanchors.tx -channelID mychannel -asOrg Org1MSP
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org2MSPanchors.tx -channelID mychannel -asOrg Org2MSP
De esta manera vamos a tener los siguientes elementos en la red:
•	genesis.block: Es el bloque genesis que inicia la cadena de bloques en la red.
•	channel.tx: Es el archivo de transacción utilizado para crear un nuevo canal en la red.
•	Org1MSPanchors.tx y Org2MSPanchors.tx: Son archivos de transacción que actualizan los peers de anclaje de las organizaciones Org1 y Org2 respectivamente.
El siguiente paso es definir y configurar los archivos docker-compose.yaml. Estos archivos describen cómo se deben levantar los contenedores Docker para los nodos de la red. En este ejemplo, utilizamos dos archivos docker-compose para dos máquinas virtuales (MV):
•	docker-compose-org1.yaml en la MV1, que levanta el contenedor para el orderer y el peer de la organización Org1. Se define la versión, los volumes persistentes para los contenedores orderer y peer de Org1, la red en la que se comunican los contenedores y los servicios a desplegar:
o	orderer.example.com: nombre del contenedor, imagen de Docker a utilizar (hyperledger/fabric-orderer:latest), environment (Variables de entorno necesarias para la configuración del orderer), volumes (Montaje de volúmenes para compartir archivos necesarios, como el bloque génesis y la MSP) y networks (Red en la que se comunica el contenedor).
o	peer0.org1.example.com: Similar configuración para el peer de Org1, especificando la imagen de Docker, variables de entorno, volúmenes y red.

•	docker-compose-org2.yaml en la MV2, que levanta el contenedor para el peer de la organización Org2. Se define la versión, los volumes persistentes para el contenedor peer de Org2, la red y el servicio a desplegar:
o	peer0.org2.example.com: Similar configuración al peer de Org1, pero con puertos y MSP específicos para Org2.
En cada máquina virtual, se ejecutan los siguientes comandos para levantar los contenedores:
En la MV1: docker-compose -f docker-compose-org1.yaml up -d
En la MV2: docker-compose -f docker-compose-org2.yaml up –d
Esto iniciará los contenedores definidos en cada archivo docker-compose, configurando así la red de Hyperledger Fabric con un orderer y dos organizaciones en diferentes máquinas virtuales.
Un canal es una subred de la red blockchain donde se pueden realizar transacciones específicas entre los miembros del canal. Aquí, detallaremos los pasos y comandos necesarios para que Org1 se una al canal llamado mychannel.

Configuración del Entorno para Org1
Antes de ejecutar los comandos para crear y unirse al canal, es necesario configurar las variables de entorno para Org1. Estas variables especifican la configuración del peer que está ejecutando los comandos.
Deshabilita TLS (Transport Layer Security) para el peer. En un entorno de producción, generalmente se habilitaría TLS para mayor seguridad.
export CORE_PEER_TLS_ENABLED=false  
Especifica el MSP (Membership Service Provider) ID local del peer, que en este caso es Org1MSP.
export CORE_PEER_LOCALMSPID=Org1MSP
Especifica el camino al directorio MSP que contiene los certificados y las claves de la identidad administrativa de Org1.
export CORE_PEER_MSPCONFIGPATH=/home/ubuntu/fabric-samples/red-propia/crypto-config/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
Define la dirección del peer peer0 de Org1.
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
El siguiente comando crea un canal llamado mychannel. Este canal será administrado por el orderer especificado.
peer channel create -o orderer.example.com:7050 -c mychannel -f ./channel-artifacts/channel.tx --outputBlock ./channel-artifacts/mychannel.block
•  -f ./channel-artifacts/channel.tx: Archivo de configuración del canal que especifica los parámetros y las políticas del canal.
•  --outputBlock ./channel-artifacts/mychannel.block: Archivo de salida donde se guarda el bloque génesis del canal.
Una vez que el canal ha sido creado, el peer de Org1 se une al canal utilizando el bloque génesis del canal (mychannel.block).
peer channel join -b ./channel-artifacts/mychannel.block
Para verificar que el peer se ha unido correctamente al canal, se puede listar los canales a los que el peer está unido: peer channel list
Configuración del Entorno para Org2
Para que el peer de Org2 (que reside en la MV2) pueda unirse al canal mychannel, es necesario copiar el bloque de creación del canal (mychannel.block) desde la MV1 a la MV2. Una vez copiado, se pueden configurar las variables de entorno para Org2 y ejecutar los comandos necesarios para unirse al canal.
export CORE_PEER_TLS_ENABLED=false
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_MSPCONFIGPATH=/home/usuario/fabric-samples/red-propia/crypto-config/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=peer0.org2.example.com:8051
Con las variables de entorno configuradas, el peer de Org2 puede unirse al canal utilizando el bloque génesis copiado: peer channel join -b ./channel-artifacts/mychannel.block
Este proceso asegura que ambos peers, peer0.org1.example.com en la MV1 y peer0.org2.example.com en la MV2, estén unidos al canal mychannel, permitiendo que ambas organizaciones participen en la red blockchain y realicen transacciones en el canal compartido.

 
Desplegar un Chaincode en Hyperledger Fabric
El siguiente paso sería desplegar un chaincode para que los peers puedan hacer smartContracts entre ellos y ejecutar transacciones. Desplegar un chaincode en Hyperledger Fabric implica varios pasos, desde empaquetar el chaincode hasta instalarlo, aprobarlo y finalmente comprometerlo en el canal. A continuación, se explica cada uno de los comandos necesarios para este proceso.
Empaquetar el Chaincode (por ejemplo si se escribe un smartContract en go empaquetarlo con todas sus dependencias y crear un .tgz con toda la información del chaincode empaquetada)
peer lifecycle chaincode package mycc.tar.gz --path ~/fabric-samples/red-propia/chaincode-go/ --lang golang --label mycc_1
Instalar el Chaincode en los Peers. Este comando debe ejecutarse en cada peer donde se desee instalar el chaincode, tanto en peer0.org1.example.com como en peer0.org2.example.com.
peer lifecycle chaincode install mycc.tar.gz
Aprobar el Chaincode por la Organización. Este comando debe ejecutarse en ambas organizaciones para que cada una apruebe el chaincode.
peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 --channelID mychannel --name mycc --version 1 --package-id mycc_1:fbf3a62d2d5e9132ef343beef5e33c1c45a4c80762389bf4f52daa770ad7f8f4 --sequence 1 
Comittear el Chaincode en el Canal
peer lifecycle chaincode commit -o orderer.example.com:7050 --channelID mychannel --name mycc --version 1 --sequence 1 --peerAddresses peer0.org1.example.com:7051 --peerAddresses peer0.org2.example.com:8051
Verificar el Chaincode comitteado
peer lifecycle chaincode querycommitted --channelID mychannel --name mycc
Invocar el Chaincode
peer chaincode invoke -o orderer.example.com:7050 --channelID mychannel --name mycc --peerAddresses peer0.org1.example.com:7051 --peerAddresses peer0.org2.example.com:8051 -c '{"function":"InitLedger","Args":[]}'
-c '{"function":"InitLedger","Args":[]}': Invoca la función InitLedger` del chaincode con los argumentos proporcionados.
Consultar el Chaincode
peer chaincode query -C mychannel -n mycc -c '{"Args":["GetAllAssets"]}'
