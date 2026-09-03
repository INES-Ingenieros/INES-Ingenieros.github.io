# Petición: desplegar un servicio de estampado de QR en Azure

**Para:** quien gestione la suscripción de Azure de INES
**De:** Pedro Irache · Oficina técnica
**Asunto:** despliegue de una Azure Function pequeña, sin acceso a datos ni al tenant

---

## Qué se pide, en una línea

Desplegar una **Azure Function** (runtime de Python, plan de consumo) y devolver
su **URL** y su **clave de función**. Nada más.

Como alternativa, si preferís que lo despliegue yo: **rol de Colaborador sobre un
grupo de recursos nuevo** —no sobre la suscripción— y me encargo del despliegue.

---

## Para qué

La oficina técnica ha puesto en marcha un control de revisiones de planos de obra.
Cada plano lleva impreso un código QR; al escanearlo con el móvil, quien esté en obra
sabe si el papel que tiene en la mano es la revisión vigente o si ya está superada.
El sistema está funcionando y publicado en `https://ines-ingenieros.github.io`.

El circuito se quiere automatizar con **Power Automate**, que ya está incluido en el
M365 de la empresa. Power Automate puede hacer todo el proceso —detectar el plano
nuevo en SharePoint, leer los datos del formulario, sustituir el fichero, actualizar el
estado— **salvo una cosa: no sabe dibujar una imagen dentro de un PDF.**

Esta función es exclusivamente ese trozo.

---

## Qué hace la función

```
recibe:   un PDF y un código de texto
devuelve: el mismo PDF con un QR de 20 mm estampado en cada hoja
```

Es un endpoint HTTP con una sola operación. El PDF se procesa **en memoria y en un
directorio temporal que se borra al terminar**.

## Qué NO hace, y NO necesita

Esto es lo relevante para valorar el riesgo:

| | |
|---|---|
| **Permisos sobre el tenant** | Ninguno. No es una aplicación registrada en Entra ID, no pide consentimiento de administrador, no tiene identidad en el directorio |
| **Acceso a SharePoint** | Ninguno. No lee ni escribe en ninguna biblioteca. Recibe el fichero de Power Automate y lo devuelve |
| **Acceso a Microsoft Graph** | Ninguno |
| **Almacenamiento de datos** | Ninguno. No guarda el PDF ni su contenido. No hay base de datos |
| **Llamadas salientes** | Ninguna. No consulta internet en tiempo de ejecución |
| **Credenciales que custodia** | Ninguna. La única clave que existe es la propia clave de función de Azure, que guarda Power Automate para poder invocarla |
| **Datos personales** | Ninguno. No sabe quién ha subido el plano ni de qué obra es |

La lógica de negocio —qué revisión es, qué número le corresponde, cuándo se publica—
vive en Power Automate y en SharePoint. La función solo dibuja.

---

## Especificaciones técnicas

| | |
|---|---|
| Servicio | Azure Functions |
| Runtime | Python 3.11 o superior |
| Modelo de programación | v2 (decoradores) |
| Plan | Consumo (*Consumption*) |
| Nivel de autenticación | `function` (clave requerida en cada llamada) |
| Región | La que uséis habitualmente. Preferible UE por proximidad y por RGPD |
| Tiempo de espera | 5 minutos configurados; el uso real es de 2 a 5 segundos por plano |
| Memoria | La del plan de consumo es suficiente; los planos con ortofoto rondan 50 MB |
| Tope de entrada | 120 MB, controlado en el propio código |
| Código fuente | `azure_estampado/` en `github.com/INES-Ingenieros/INES-Ingenieros.github.io` |
| Dependencias | `azure-functions`, y el paquete del proyecto, instalado desde ese mismo repositorio público |

**Coste estimado:** el volumen previsto es de decenas de planos al mes, con ejecuciones
de segundos. Debería quedar dentro del margen gratuito mensual del plan de consumo; el
único gasto seguro es la cuenta de almacenamiento que toda Function App requiere, del
orden de céntimos al mes. *Conviene confirmarlo con la calculadora de Azure antes de
aprobar, no dar por bueno este estimado.*

---

## Cómo se comprueba que funciona

La función expone además un `GET /api/salud` **sin clave**, que solo responde con su
número de versión. Sirve para verificar el despliegue sin procesar ningún documento y
sin exponer nada.

---

## Qué necesito de vuelta

1. La **URL** de la función (`https://<nombre>.azurewebsites.net/api/estampar`)
2. La **clave de función**, para configurarla en Power Automate

Con esos dos datos el circuito queda cerrado y ningún plano puede salir a obra sin su
QR por olvido de nadie.

---

*Documentación completa del sistema, incluidas las 17 decisiones de diseño y sus
motivos, en `docs/DECISIONES.md` del repositorio.*
