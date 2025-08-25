# Hello Fairy BLE

Proyecto de componente custom para Home Assistant. El objetivo será implementar la conectividad con luces de navidad Hello Fairy  usando la API BLE de Home Assistant sensores y switches.
Esta basado en la integracion realizara para esphome: https://community.home-assistant.io/t/control-hello-fairy-ble-string-lights-with-esphome/818595


## Características

- Control local vía BLE (sin nube)
- Encendido/apagado, color HSV, brillo
- Efectos predefinidos (Rainbow, Pulse, etc.)
- Reconexión automática y validación de disponibilidad
- Configuración desde la UI (config_flow)

## Instalación

1. Copiar la carpeta `hello_fairy_ble` dentro de `custom_components/`
2. Reiniciar Home Assistant
3. Ir a **Configuración → Dispositivos e Integraciones → Agregar**
4. Buscar “Hello Fairy BLE” y seguir el asistente


## 🧪 Requisitos

- Home Assistant 2024.6 o superior
- Python ≥ 3.10
- Adaptador BLE compatible (probado con dongles USB y chipsets integrados)
- Paquete `bleak==0.21.1`

##  Uso

Una vez configurado, se crea una entidad `light.hello_fairy_<nombre>`. Desde la UI podés:

- Cambiar color y brillo
- Aplicar efectos
- Ver disponibilidad del dispositivo

## Troubleshooting

| Problema | Solución |
|---------|----------|
| No aparece en el escaneo | Verificar que el dispositivo esté encendido y cerca |
| Error “cannot_connect” | Probar con otro adaptador BLE o reiniciar Home Assistant |
| No responde a comandos | Validar logs y revisar reconexión automática |
| Efectos no aplican | Confirmar que el preset esté soportado por el firmware |


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

# Instalación vía HACS
Una vez generado el proyecto, lo vas a poder subir a GitHub y agregarlo como repositorio custom en HACS. Desde ahí, se instala como cualquier otra integración.

# Validación Técnica
* Se usará bleak para manejar la conexión BLE
* Se replicarán los comandos sendhsv, sendpatt y el ACK parsing
* Se convertirá HSV a RGB usando la lógica del script hsv2rgb del archivo adjunto
* Se expondrán los presets como select o number según convenga


## Componentes

### Estructura del proyecto

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
### Lógica principal (ble_handler.py)
* Maneja conexión BLE con bleak o HaBleakClientWrapper
* Detecta dispositivos Hello Fairy por nombre o UUID
* Reintenta conexión si se pierde
* Expone métodos como send_hsv, send_preset, read_command

### Entidad de luz (light.py)
* Encendido/apagado
* Brillo (si el dispositivo lo soporta)
* Color HSV → RGB (usando la lógica del archivo adjunto)
* Selección de escena/preset como select o number

 ### Sensores (sensor.py)
* binary_sensor.hello_fairy_connected: estado de conexión
* sensor.hello_fairy_remote_command: último comando IR recibido

### Configuración (config_flow.py)
* Escaneo BLE inicial
* Selección de dispositivo por MAC
* Timeout configurable
* Visualización de MAC en la UI
