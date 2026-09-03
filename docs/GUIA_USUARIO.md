# Guía de usuario

Última actualización: 3 de septiembre de 2026 · Sistema en funcionamiento

---

## En treinta segundos

Cada plano lleva un **código QR** impreso al lado del cajetín. Si escaneas ese QR con
la cámara del móvil, se abre una página que te dice si el papel que tienes en la mano
es la última revisión o si ya hay una posterior.

No hace falta instalar ninguna aplicación. No hace falta usuario ni contraseña. No
hace falta ser de INES.

**La web de comprobación está publicada en:**
[https://ines-ingenieros.github.io](https://ines-ingenieros.github.io)

Ahí, sin escanear nada, se ve el listado de todos los planos vigentes.

---

# Parte 1 · Estás en obra con un plano en la mano

## Cómo se comprueba

1. Busca el **código QR**. Está en la esquina inferior derecha, justo encima del
   cajetín.
2. Abre la **cámara** del móvil y apúntale. No hace falta hacer foto: casi todos los
   móviles detectan el QR solos y muestran un aviso para abrir el enlace.
3. Toca el aviso. Se abre la página con la respuesta.

Debajo del QR está impreso también el código en letra normal, algo así como
`SESENA-101-R00`. Sirve para cuando el escaneo no funciona (más abajo se explica).

## Las tres respuestas posibles

### VIGENTE (verde)

Ese papel es la última revisión. **Puedes trabajar con él.**

La pantalla te muestra además de qué plano se trata, de qué revisión, cuándo se emitió
y qué número tiene en el índice de planos, para que puedas contrastarlo con el cajetín.

### SUPERADO (rojo)

**Ese papel no se debe usar.** Hay una revisión posterior.

Muy importante: «superado» no quiere decir que el plano esté mal. Quiere decir que
existe uno más nuevo. La pantalla te dirá cuál es la revisión vigente, de qué fecha es
y, si se ha anotado, **por qué cambió**.

Qué hacer:

- No trabajes con ese papel.
- Pide la revisión vigente a la dirección de obra o a la oficina técnica. La página no
  te da el plano: solo te avisa. Los planos siguen estando donde están siempre.
- Marca o retira el papel antiguo, para que nadie lo vuelva a coger por error.

### CÓDIGO NO VÁLIDO (gris)

El código no corresponde a ningún plano registrado. Puede pasar por tres motivos:

- Es un plano **anterior a la puesta en marcha del sistema** y su QR nunca se registró.
- El QR se ha leído mal por estar dañado o sucio.
- El QR pertenece a otra obra.

Qué hacer: llama a la oficina técnica y dale el código que está impreso en letra
normal debajo del QR.

## Si no hay cobertura

Pasa a menudo, y el sistema está pensado para eso.

- **Si ya has escaneado algún plano antes en ese mismo móvil**, la página suele
  responder igualmente, porque el móvil se guarda la lista en memoria. Fíjate en la
  fecha de «lista actualizada» que aparece abajo: si es de hace mucho, la respuesta
  puede estar anticuada. La página te avisa en naranja cuando está usando la copia
  guardada.
- **Si no responde nada**, sal a una zona con cobertura y vuelve a escanear. O usa el
  método de abajo.

## Si el QR no se lee

Porque está roto, borrado, mojado o mal fotocopiado. Para eso está el **código en
letra normal** impreso al lado.

Llama a la oficina técnica y dicta el código tal cual:

> «Seseña, ciento uno, erre cero cero»

Con eso pueden comprobarlo en un segundo. Esta es la razón de que el código sea legible
y corto en lugar de una ristra de letras y números al azar.

---

# Parte 2 · Eres quien emite los planos

Todo se hace con **dos ficheros, a doble clic**. No hace falta saber Python ni git.
Están los dos en la carpeta del proyecto:

```
C:\Users\pia.INTRANET\projects\00_CONTROL_PLANOS\
    emitir.bat      <- paso 1: mete el QR en el plano
    publicar.bat    <- paso 2: sube la revision a la web
```

## Lo que no cambia en tu trabajo

- Sigues dibujando y ploteando **igual que ahora**, desde AutoCAD o Civil 3D.
- **No se toca ningún DWG** por este motivo. Ni el cajetín, ni la referencia externa.
- Los ficheros se siguen llamando **igual que ahora**, ordenados por número de índice.
- Los PDF se siguen guardando en **SharePoint**, en la biblioteca de la obra.
- Puedes **reordenar el índice de planos** cuando haga falta, sin invalidar ningún QR
  ya impreso. El sistema está diseñado específicamente para aguantar eso.

## Paso 1 · Meter el QR en el plano

1. Abre la carpeta `00_CONTROL_PLANOS` en el explorador de Windows.
2. **Arrastra el PDF ploteado encima de `emitir.bat`** y suéltalo.
3. Se abre una ventana negra que te va preguntando, **una cosa a la vez**:

| Te pregunta | Qué contestar |
|---|---|
| Código de obra | El código corto, p. ej. `SESENA`. Te enseña las obras que ya existen |
| Denominación del documento | Lo que pone el cajetín en «DESIGNACIÓN DEL PLANO» |
| Revisión | Te propone la siguiente. Pulsa Intro para aceptarla |
| Título del plano | La línea de detalle. Puede quedar vacío |
| Nº de índice | El «Nº» del cajetín **de este papel** |
| Motivo del cambio | Solo si no es la primera emisión. **Lo lee el encargado en obra** |

Si la obra es nueva te pedirá además su nombre y su expediente, **una sola vez**.

4. Al terminar te dice el código asignado y dónde ha dejado el PDF sellado:

```
C:\Users\pia.INTRANET\projects\00_CONTROL_PLANOS\salida\
```

5. **Ese PDF de `salida` es el que se guarda en SharePoint y el que se imprime.**
   El original no se toca.

Puedes emitir varios planos seguidos antes de pasar al paso 2.

## Paso 2 · Subir la revisión a la web

**Hasta que no hagas esto, el QR del plano no funciona en obra.** El plano ya lleva el
QR impreso, pero la web todavía no sabe que esa revisión existe: al escanearlo saldría
«CÓDIGO NO VÁLIDO».

1. **Doble clic en `publicar.bat`.**
2. Te enseña qué revisiones va a publicar y te pide confirmación. Escribe `S` e Intro.
3. La web tarda uno o dos minutos en actualizarse. A partir de ahí, los QR responden.

Si el envío falla —sin conexión, por ejemplo— te avisa expresamente de que **los QR
todavía no funcionan** y de que hay que volver a ejecutarlo. No se queda callado.

## Las tres reglas que hay que respetar

**1. Solo se imprime lo que ha pasado por `emitir.bat`.**
Un plano sin QR no se puede comprobar en obra, y ese es justo el problema que estamos
resolviendo. Si un plano sale a obra sin pasar por aquí, el sistema no ha fallado: se
ha esquivado.

**2. Una revisión nueva es una pasada nueva.**
Cada vez que se emite una revisión, se vuelve a arrastrar el PDF. La herramienta marca
la anterior como superada automáticamente. No hay que cambiar nada a mano en ningún
sitio.

**3. Emitir y publicar son dos actos, y los dos son deliberados.**
El sistema **no** vigila carpetas ni publica nada por su cuenta. Nada se convierte en
«vigente» porque hayas guardado un archivo. Es intencionado: evita que un borrador
subido por error aparezca en obra como plano bueno.

## Lo que no debes hacer

- **No subas planos al repositorio de código.** Es público en internet. Los planos van
  a SharePoint. Las carpetas `muestras` y `salida` están excluidas por este motivo.
- **No muevas `index.html` ni `planos.json` a una subcarpeta.** Parecen sueltos en la
  raíz y da la tentación de ordenarlos, pero GitHub Pages publica la raíz: moverlos
  cambiaría la dirección de la web y **dejaría de funcionar todo el papel que haya en
  obra**.
- **No reutilices el número de un documento anulado.** La herramienta no lo hará sola,
  pero conviene saber por qué: un QR antiguo apuntaría a un documento distinto, que es
  el peor fallo posible en un sistema de este tipo.

## Si algo va mal

| Síntoma | Qué significa |
|---|---|
| «MODO PRUEBA» al emitir | Falta `url_base` en `config/config.yaml`. Los planos saldrán marcados como PRUEBA y no valen para obra |
| «la revisión R00 ya está registrada» | Esa revisión ya se emitió. Si de verdad hay que rehacerla, avisa: hay que retirarla del registro a mano y a conciencia, porque su QR puede estar ya impreso |
| «el módulo del QR sale de 0,54 mm» | Es un aviso, no un error. Se ha comprobado que a ese tamaño se lee bien. Solo importaría si alguien alargase la dirección de la web |
| `publicar.bat` dice que no hay nada | No se ha emitido nada nuevo desde la última publicación |
| En obra sale «CÓDIGO NO VÁLIDO» en un plano recién emitido | Falta el paso 2: no se ha publicado |

---

# Preguntas frecuentes

**¿Necesito instalar una aplicación?**
No. La cámara del móvil ya lee QR. La respuesta se abre en el navegador.

**¿Me hace falta cuenta o contraseña?**
No, y es deliberado. Quien más necesita consultar esto es el encargado de la contrata o
la asistencia técnica del cliente, que no tienen cuenta de INES.

**¿Se puede ver el plano desde la página?**
No. La página solo dice si está vigente o superado. Los planos no están en la web:
siguen en SharePoint, con sus permisos de siempre.

**¿Queda registrado quién escanea?**
No. La página no guarda ningún dato de quién consulta ni desde dónde, y **no llama a
ningún servicio externo**: ni Google, ni analítica, ni nada. Todo lo que carga sale del
propio sitio de INES.

**¿Y los planos que ya están en obra sin QR?**
Darán «CÓDIGO NO VÁLIDO» o simplemente no tendrán QR que escanear. Todavía hay que
decidir cómo se tratan; está anotado como pendiente en el registro de decisiones.

**El cajetín no tiene casilla de revisión. ¿Eso es un problema?**
Es precisamente el problema de partida. El cajetín de la Comunidad de Madrid no la
tiene, así que hoy **un plano impreso no lleva encima ningún dato de su revisión**. El
QR y el código impreso al lado son los que aportan esa información que falta.

**¿Y si cambiamos el orden del índice de planos?**
No pasa nada. Los QR ya impresos siguen siendo válidos. El sistema está diseñado
expresamente para soportarlo, y esa fue una de las decisiones de diseño más importantes
que se tomaron.

**¿Cómo se añade una obra nueva?**
No hay que preparar nada. La primera vez que emitas un plano de esa obra, `emitir.bat`
te pedirá su código, su nombre y su expediente, y la da de alta sola. Aparecerá como un
bloque nuevo en el listado de la web.

---

# Vocabulario

| Término | Qué significa aquí |
|---|---|
| **Documento** | El PDF completo que se emite, con todas sus hojas. Es la unidad que se controla |
| **Hoja** | Una página del documento. Todas las hojas de un documento llevan el mismo QR |
| **Revisión** | La versión de ingeniería del documento (`R00`, `R01`...). No tiene nada que ver con el historial de versiones de SharePoint |
| **Vigente** | La última revisión emitida. Es la única que se debe usar |
| **Superado** | Una revisión que ha sido sustituida por otra posterior |
| **Nº de índice** | El número que el documento tiene en el índice de planos. Puede cambiar si se reordena el índice |
| **Correlativo** | El número interno del código QR (`101`). No cambia nunca. No es el número de índice |
| **Registro** | El fichero `planos.json` con los documentos y revisiones, que alimenta la web |
| **Emitir** | Meter el QR en el PDF y anotar la revisión. Paso 1 |
| **Publicar** | Subir el registro a la web para que los QR respondan. Paso 2 |

---

## Documentación relacionada

- [DECISIONES.md](DECISIONES.md) — por qué el sistema es así y qué se descartó
- [../README.md](../README.md) — resumen del proyecto y estado actual
