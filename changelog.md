## [0.1.0] - 2025-08-25
- Implementación inicial de entidad Light con soporte HSV, brillo y efectos
- Módulo BLE modular con reconexión automática y logging
- Compatibilidad con bleak puro y UUID estándar
- Documentación modular por archivo

## [0.1.1] - 2025-08-25
- Correccion de errores

## [0.1.2] - 2025-08-25
- Correccion de errores segunda parte

## [0.1.3] - 2025-08-25
- Arega log de los dispositivos encontrados
- Corrije nombre del prefijo 
- soluciona problema de conexion

## [0.1.4] - 2025-08-25
- Problema con entidad light que no carga

## [0.1.5] - 2025-08-25
- Problema con entidad light que no carga (continuacion)
- Problema con serivicios que no encuentra
- Soluciona problemas de compatibilidad

## [0.1.6] - 2025-08-25
- Problema con entidad light que no carga (continuacion)
- Problema con serivicios que no encuentra (continuacion)
- Solucion a problema que no levanta la integracion.
- Cambia default time out a 30
- agrega clase de testing


## [0.1.7] - 2025-08-26
- Corrigen indentacion en pyton que produce erorr al levantar (ya corregido en HA)
- agrega servicio de testeo


## [0.1.8] - 2025-08-26
- Agrega comando de encendido y apagado
- elimina llamado deprecado
- Soluciona problema de presets y colores (en proceso)



## [0.2.0] - 2025-08-29
- Soluciona problema de presets y colores (en proceso)

## [0.2.1] - 2025-08-29
- Se solucina el envio del preset y de brillo
- Implementa lectura de notificaciones
- Implementa sensor de estado de conexion


## [0.2.2] - 2025-08-29
- Cambia implementacion de lectura de notificaciones

## [0.2.3] - 2025-08-29
- Elimina duplicados en notificaciones


## [0.2.4] - 2025-08-29
- Soluciona instancias duplicadas de HelloFairBLE

## [0.2.5] - 2025-08-29
- Recupera el estado de la luz al iniciar home assistant

## [0.2.6] - 2025-08-29
- Agrega comando para mandar RAW Data a la luz


## [0.2.7] - 2025-09-01
- Agrega controles antes de conectarse para ver que este disponible y ademas si no esta disponible espera un cierto periodo de tiempo par no reintentar inmediatamente y no saturar bt.
- Cambia la dependencia con Bleak

## [0.2.8] - 2025-09-01
- Bug en connect

## [0.3.4] - 2025-09-01
- Actualiza el estado de la luz en home assitant cuando se maneja la luz por el control remoto
- "Descubre" el estado de la luz cuando se inicia home assistant. Esto lo hace mandando un comando que apaga el timer
- Elimina warnings
- Mejora en comando para enviar presets

## [0.3.5] - 2025-09-04
- Correccion en manejo de colores y brillo