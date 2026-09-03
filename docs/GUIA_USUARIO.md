# Guía de usuario

Última actualización: 3 de septiembre de 2026

---

## En treinta segundos

Cada plano lleva un **código QR** impreso al lado del cajetín. Si escaneas ese QR con
la cámara del móvil, se abre una página que te dice si el papel que tienes en la mano
es la última revisión o si ya hay una posterior.

No hace falta instalar ninguna aplicación. No hace falta usuario ni contraseña. No
hace falta ser de INES.

> **Aviso sobre el estado del sistema.** El diseño está terminado, pero **la
> herramienta todavía no está construida**. La Parte 1 de esta guía describe cómo va a
> funcionar para quien esté en obra. La Parte 2 describe el procedimiento previsto para
> quien emite los planos, y está aquí para poder revisarlo antes de construirlo.

---

# Parte 1 · Estás en obra con un plano en la mano

## Cómo se comprueba

1. Busca el **código QR**. Está en la esquina inferior derecha, justo encima del
   cajetín.
2. Abre la **cámara** del móvil y apúntale. No hace falta hacer foto: casi todos los
   móviles detectan el QR solos y muestran un aviso para abrir el enlace.
3. Toca el aviso. Se abre la página con la respuesta.

Debajo del QR está impreso también el código en letra normal, algo así como
`SESENA-014-R00`. Sirve para cuando el escaneo no funciona (más abajo se explica).

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
  puede estar anticuada.
- **Si no responde nada**, sal a una zona con cobertura y vuelve a escanear. O usa el
  método de abajo.

## Si el QR no se lee

Porque está roto, borrado, mojado o mal fotocopiado. Para eso está el **código en
letra normal** impreso al lado.

Llama a la oficina técnica y dicta el código tal cual:

> «Seseña, cero catorce, erre cero cero»

Con eso pueden comprobarlo en un segundo. Esta es la razón de que el código sea legible
y corto en lugar de una ristra de letras y números al azar.

---

# Parte 2 · Eres quien emite los planos

> Este procedimiento está **diseñado pero no construido todavía**. Se describe aquí
> para poder revisarlo antes de programarlo.

## Lo que no cambia en tu trabajo

- Sigues dibujando y ploteando **igual que ahora**, desde AutoCAD o Civil 3D.
- **No se toca ningún DWG** por este motivo. Ni el cajetín, ni la referencia externa,
  ni nada.
- Los ficheros se siguen llamando **igual que ahora** y ordenados por número de índice
  (`01_DESVIOS_PROVISIONALES.pdf`).
- Los PDF se siguen guardando en **SharePoint**, en la biblioteca de la obra.
- Puedes **reordenar el índice de planos** cuando haga falta, sin que eso invalide
  ningún QR ya impreso. El sistema está diseñado específicamente para aguantar eso.

## Lo que cambia: un paso más antes de imprimir

El flujo previsto es este:

```
1. Ploteas el PDF como siempre
        ↓
2. Pasas el PDF por la herramienta, indicando:
     · de qué obra es
     · qué documento es (si es nuevo, se le asigna un número)
     · qué revisión es
     · el motivo del cambio (si no es la primera emisión)
        ↓
3. La herramienta te devuelve el PDF con el QR estampado
   en todas las hojas, y actualiza el registro público
        ↓
4. Ese PDF con QR es el que se guarda en SharePoint y el que se imprime
```

El paso 2 es el único añadido. El resto ya lo haces.

## Las tres reglas que hay que respetar

**1. Solo se imprime lo que ha pasado por la herramienta.**
Un plano sin QR no se puede comprobar en obra, y ese es justo el problema que estamos
resolviendo. Si un plano sale a obra sin pasar por aquí, el sistema no ha fallado: se
ha esquivado.

**2. Una revisión nueva es una pasada nueva por la herramienta.**
Cada vez que se emite una revisión, se vuelve a pasar el PDF. La herramienta le pone el
QR nuevo y marca la anterior como superada automáticamente. No hay que ir a cambiar
nada a mano en ningún sitio.

**3. Publicar es un acto deliberado.**
El sistema **no** vigila carpetas ni publica cosas por su cuenta. Nada se convierte en
«vigente» porque hayas guardado un archivo. Esto es intencionado: evita que un borrador
subido por error aparezca en obra como plano bueno.

## Lo que no debes hacer

- **No subas planos al repositorio de código.** El repositorio del proyecto es público
  en internet. Los planos van a SharePoint, nunca al repositorio. Las carpetas de
  muestras y de salida están excluidas expresamente por este motivo.
- **No renombres a mano un PDF que ya lleva QR.** El QR apunta a un código concreto; el
  nombre del fichero es indiferente para el sistema, pero cambiarlo genera confusión al
  cotejar.
- **No reutilices el número de un documento anulado.** La herramienta no lo hará sola,
  pero conviene saber por qué: un QR antiguo apuntaría a un documento distinto, que es
  el peor fallo posible en un sistema de este tipo.

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
No. Tal como está diseñado hoy, la página no guarda ningún dato de quién consulta ni
desde dónde. Si en el futuro se quisiera registrar los escaneos habría que añadir una
pieza más al sistema, y sería una decisión consciente y documentada.

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
| **Correlativo** | El número interno del código QR (`014`). No cambia nunca. No es el número de índice |
| **Registro** | El listado de documentos y revisiones que alimenta la web pública |

---

## Documentación relacionada

- [DECISIONES.md](DECISIONES.md) — por qué el sistema es así y qué se descartó
- [../README.md](../README.md) — resumen del proyecto y estado actual
