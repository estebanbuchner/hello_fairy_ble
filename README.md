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

1. Ir a **Configuración → Dispositivos e Integraciones → Agregar**
2. Agregar repositorio https://github.com/estebanbuchner/hello_fairy_ble/
3. Buscar “Hello Fairy BLE” y seguir el asistente


## 🧪 Requisitos

- Home Assistant 2024.6 o superior
- Python ≥ 3.10
- Adaptador BLE compatible (probado con dongles USB y chipsets integrados)
- Paquete `bleak>=0.20.2`

##  Uso

Una vez configurado, se crea una entidad `light.hello_fairy_<nombre>`. Desde la UI podés:

- Cambiar color y brillo
- Aplicar efectos
- Ver disponibilidad del dispositivo

### Comando para usarlo desde una automatizacion


``` 
alias: Activar efecto Fairy
trigger:
  - platform: state
    entity_id: binary_sensor.movimiento_pasillo
    to: "on"
action:
  - service: hello_fairy_ble.send_preset_command
    data:
      mac: "11:11:00:30:4E:14"
      preset_id: 20
      brightness: 100
mode: single


``` 
### enviar datos RAW


``` 
action: hello_fairy_ble.send_raw_command
data:
  mac: 11:11:00:30:4E:14
  raw: aa,03,04,02,14,03,e8,b2


``` 

### Algunos comandos

**Azul con alto brillo**
``` 

0xaa, 0x03, 0x07, 0x01, 0x00, 0xF0, 0x03, 0xE8, 0x03, 0xE8, 0x7B
``` 


**Rojo**
``` 
0xaa, 0x03, 0x07, 0x01, 0x00, 0x00, 0x03, 0xE8, 0x03, 0xE8, 0x8B
``` 


**Verde**
``` 
0xaa, 0x03, 0x07, 0x01, 0x00, 0x78, 0x03, 0xE8, 0x03, 0xE8, 0x01
``` 

**Blanco (parpadea!!!) es preset**
``` 
0xaa, 0x03, 0x04, 0x02, 0x15, 0x03, 0xE8, 0xB3
``` 



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
* Selección de presets (efectos)
* Control de color 

## Sensor de Conectividad
* Reconexión automática si se pierde la conexión
* Indicador de estado de conexion


## Sensor de Comando IR 
* sensor.hello_fairy_remote_command: muestra el último comando recibido desde el control remoto

## Configuración desde UI
* Selección de dispositivo por MAC
* Timeout de conexión configurable (pendiente)
* Visualización de MAC en la interfaz

# Flujo de Configuración
* Escaneo BLE para detectar dispositivos Hello Fairy (por nombre o UUID)
* Selección desde la UI
* Guardado de MAC y configuración
* Inicialización de entidades


# Validación Técnica
* Se usará bleak para manejar la conexión BLE
* Se replicarán los comandos sendhsv, sendpatt y el ACK parsing
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
* Color 
* Selección de escena/preset como select o number

 ### Sensores (sensor.py)
* binary_sensor.hello_fairy_connected: estado de conexión
* sensor.hello_fairy_remote_command: último comando IR recibido

### Configuración (config_flow.py)
* Escaneo BLE inicial
* Selección de dispositivo por MAC
* Timeout configurable
* Visualización de MAC en la UI
