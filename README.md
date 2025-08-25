# hello_fairy_ble
Proyecto de componente custom para Home Assistant. El objetivo será implementar la conectividad con luces de navidad Hello Fairy  usando la API BLE de Home Assistant sensores y switches.
Esta basado en la integracion realizara para esphome: https://community.home-assistant.io/t/control-hello-fairy-ble-string-lights-with-esphome/818595

## Estructura del proyecto

``` 
custom_components/
└── hello_fairy_ble/
    ├── __init__.py
    ├── manifest.json
    ├── const.py
    ├── ble_handler.py
    ├── light.py
    ├── sensor.py
    ├── switch.py
    ├── config_flow.py
    ├── translations/
    │   └── en.json
    └── services.yaml
``` 

# Funcionalidades Incluidas
## Light Entity
* Encendido/apagado
* Control de brillo
* Control de color (HSV → RGB)
* Selección de presets (efectos)
* Reenvío de comandos BLE

## Sensor de Conectividad
* binary_sensor.hello_fairy_connected: indica si el dispositivo está conectado
* Reconexión automática si se pierde la conexión

## Sensor de Comando IR
* sensor.hello_fairy_remote_command: muestra el último comando recibido desde el control remoto

## Configuración desde UI
* Selección de dispositivo por MAC
* Timeout de conexión configurable
* Visualización de MAC en la interfaz

# Flujo de Configuración
* Escaneo BLE para detectar dispositivos Hello Fairy (por nombre o UUID)
* Selección desde la UI
* Guardado de MAC y configuración
* Inicialización de entidades

# Validación Técnica
* Se usará bleak para manejar la conexión BLE
* Se replicarán los comandos sendhsv, sendpatt y el ACK parsing
* Se convertirá HSV a RGB usando la lógica del script hsv2rgb del archivo adjunto
* Se expondrán los presets como select o number según convenga

# Instalación vía HACS
Una vez generado el proyecto, lo vas a poder subir a GitHub y agregarlo como repositorio custom en HACS. Desde ahí, se instala como cualquier otra integración.
