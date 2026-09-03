# Control de planos con QR

Herramienta para que **cualquiera, en obra y con su propio móvil, pueda comprobar
en cinco segundos si el plano de papel que tiene en la mano es la revisión vigente
o si ya está superado.**

INES Ingenieros Consultores · Proyecto iniciado el 3 de septiembre de 2026

---

## El problema que resuelve

En obra circulan planos en papel. Se imprimen, se doblan, se dejan en la caseta,
se fotocopian y pasan de mano en mano. Cuando sale una revisión nueva, las copias
antiguas no desaparecen: siguen ahí, con el mismo aspecto que las buenas.

El resultado es que **nadie puede saber, mirando un plano impreso, si está
trabajando con la última versión**. Y no hay forma de averiguarlo sin llamar a la
oficina y preguntar.

En los proyectos que estamos manejando el problema es todavía más básico de lo que
parece. Al analizar un plano real de la obra de Seseña descubrimos que **el cajetín
no tiene ninguna casilla de revisión**. No es que el control sea manual: es que el
papel no lleva encima ningún dato que permita saber de qué revisión es.

## Cómo funciona

Se añade un **código QR** en cada plano antes de imprimirlo. Ese QR es distinto para
cada revisión. Al escanearlo con la cámara del móvil se abre una página web que
responde una de tres cosas:

| Respuesta | Significado |
|---|---|
| **VIGENTE** | Ese papel es la última revisión. Se puede usar. |
| **SUPERADO** | Hay una revisión posterior. Ese papel no se debe usar. |
| **CÓDIGO NO VÁLIDO** | El QR no corresponde a ningún plano registrado. |

La página es pública: **no pide contraseña ni cuenta de empresa**. Eso es
deliberado, porque quien más necesita consultarla es el encargado de la contrata o
la asistencia técnica del cliente, que no tienen acceso a los sistemas de INES.

## El recorrido completo

```
   QUIEN EMITE EL PLANO              LA HERRAMIENTA                    LA OBRA
   ────────────────────              ──────────────                    ───────

   Plotea el PDF desde     ──►   1. Le asigna código
   AutoCAD o Civil 3D               y número de revisión
                                2. Estampa el QR sobre        ──►   Se imprime
                                   el PDF                              y va a obra
                                3. Anota la revisión                      │
                                   en el registro                         │
                                4. Publica el registro                    │
                                   en la web                              ▼
                                          │                        Alguien escanea
                                          │                          el QR
                                          ▼                               │
                                    planos.json                           │
                                   (web pública)   ◄────────────────────── ┘
                                          │
                                          ▼
                                 VIGENTE / SUPERADO
```

Los PDF siguen guardándose donde están hoy: en **SharePoint**, que es el archivo
oficial. La web pública no contiene planos, solo un listado de qué revisión está
vigente. Se explica en [docs/DECISIONES.md](docs/DECISIONES.md), decisión D-02.

## Documentación

| Documento | Para qué sirve |
|---|---|
| [docs/GUIA_USUARIO.md](docs/GUIA_USUARIO.md) | Cómo se usa. Empieza por aquí si eres nuevo. |
| [docs/DECISIONES.md](docs/DECISIONES.md) | Qué se decidió, por qué, y qué se descartó. |

## Estado actual

**El sistema está funcionando de principio a fin.** Web publicada, herramienta
construida y QR validado en papel con un móvil real.

Hecho:

- [x] Dónde viven los PDF (SharePoint) y quién puede consultar la web (todo el mundo)
- [x] Cómo se identifica cada plano y cada revisión, y qué guarda el registro
- [x] **La web de verificación**, probada en los cuatro casos: vigente, superado,
      código no válido y revisión desconocida
- [x] Colores, tipografía y logotipo corporativos de INES
- [x] **La herramienta de emisión**: estampa el QR en todas las hojas del PDF y
      mantiene el registro. 80 tests
- [x] **Ensayo en papel superado**: el QR de 20 mm se lee bien impreso a tamaño real
- [x] **Publicada** en `https://ines-ingenieros.github.io`
- [x] Primer plano emitido de verdad: `SESENA-101-R00`, 4 hojas

Lo que falta:

- [ ] Repetir el ensayo del QR **sobre una fotocopia** y con un móvil viejo, que es
      lo que de verdad circula por la obra
- [ ] Decidir si la emisión se dispara desde SharePoint en vez de a mano (ver D-04)
- [ ] Decidir cómo se replica en las siguientes obras
- [ ] Alojar la tipografía Montserrat en el repositorio, para no depender de Google

### Ver la web en local

```bash
python -m http.server 8765
```

Y abrir `http://127.0.0.1:8765`. Para probar un veredicto concreto, añadir el código
a la dirección: `http://127.0.0.1:8765/?p=DEMO-101-R00`.

## Estructura de carpetas

```
00_CONTROL_PLANOS/
├── README.md              este documento
├── docs/
│   ├── DECISIONES.md      registro de decisiones y su justificación
│   └── GUIA_USUARIO.md    guía de uso
├── index.html             la web pública de verificación
├── planos.json            el registro de planos y revisiones
├── logo-ines.svg          logotipo corporativo (vectorial)
├── .nojekyll              desactiva el procesado de Jekyll en GitHub Pages
├── src/control_planos/    la herramienta de emisión
├── config/config.yaml     configuración
├── tests/                 80 tests
├── crear_accesos.py       crea los accesos directos (una vez por puesto)
├── Emitir plano.lnk       se le arrastra el PDF encima
├── Publicar en la web.lnk doble clic para subir a la web
├── muestras/              planos reales de ejemplo (NO se sube al repositorio)
└── .venv/                 entorno virtual de Python (NO se sube)
```

**Los ficheros de la web van en la raíz del repositorio, no en una subcarpeta.** No es
una elección de estilo: GitHub Pages publica la raíz, y el QR impreso apunta a la raíz
del dominio (`https://ines-ingenieros.github.io/?p=...`). Si `index.html` estuviera en
`web/`, la dirección tendría que ser `.../web/?p=...`, más larga y con el QR más denso.

La página no carga ninguna librería externa: es un solo fichero HTML con su CSS y su
JavaScript dentro, para que abra al instante y funcione con mala cobertura.

> **Aviso importante.** La carpeta `muestras/` contiene documentación de cliente y
> está excluida del repositorio en `.gitignore`. Este repositorio va a ser público,
> así que **nunca debe subirse ningún plano a él**.

## Requisitos técnicos

- Python 3.11 o superior (desarrollado con 3.13)
- Sin permisos de administrador: todo funciona dentro del entorno virtual del proyecto
