# Registro de decisiones

Este documento recoge **todas las decisiones tomadas al diseñar la herramienta, por
qué se tomaron y qué alternativas se descartaron**. Está escrito para que alguien
que llegue nuevo dentro de dos años entienda no solo cómo funciona el sistema, sino
por qué funciona así y no de otra manera.

Cada decisión lleva un código (D-01, D-02...) para poder citarla desde el resto de
la documentación.

Última actualización: 3 de septiembre de 2026 (D-14 y D-15 añadidas al construir la herramienta)

---

## Resumen

| Código | Decisión | Estado |
|---|---|---|
| D-01 | SharePoint es el archivo oficial de los PDF | Cerrada |
| D-02 | La verificación es pública, sin contraseña | Cerrada |
| D-03 | La web es una página estática con un fichero de datos. Sin base de datos | Cerrada |
| D-04 | Sin Power Automate: publica la propia herramienta | Cerrada |
| D-05 | El QR se estampa sobre el PDF, no se dibuja en el CAD | Cerrada |
| D-06 | La unidad de control es el documento, no la hoja suelta | Cerrada |
| D-07 | El identificador es legible: `OBRA-NNN-Rxx` | Cerrada |
| D-08 | El número del identificador es un correlativo interno | Cerrada |
| D-09 | Sin código de verificación (hash) | Cerrada |
| D-10 | El número de índice y las hojas se guardan por revisión | Cerrada |
| D-11 | El listado público es indexable por buscadores | Cerrada |
| D-12 | El correlativo no aparece en el nombre del fichero | Cerrada |
| D-13 | La web se aloja en GitHub Pages | Cerrada |
| D-14 | Solo librerías con licencia permisiva | Cerrada |
| D-15 | El QR mide 20 mm y va en la banda sobre el cajetín | Cerrada · ensayo en papel superado |
| D-16 | Accesos directos, no ficheros `.bat` | Cerrada |

---

## Los hechos de partida

Antes de las decisiones conviene dejar constancia de lo que se comprobó, porque
varias decisiones se apoyan directamente en ello. Se analizó un plano real de la
obra de Seseña (`01_DESVIOS_PROVISIONALES.pdf`, 4 páginas, 47 MB) en el ordenador
local, sin subirlo a ningún servicio externo.

| Lo que se comprobó | Resultado |
|---|---|
| Formato | 4 páginas, A3 apaisado (420 × 297 mm), todas iguales |
| Programa de origen | Autodesk Civil 3D 2025 |
| ¿El texto del PDF es legible por un programa? | Sí. Expediente, fecha, escala y designación se pueden leer automáticamente |
| ¿Hay casilla de revisión en el cajetín? | **No. Ninguna.** Se buscó «rev» en las cuatro páginas completas: cero resultados |
| ¿Cada página tiene un identificador propio? | **No.** La casilla `Nº:` vale `01` en las cuatro |
| ¿Se puede leer el `HOJA 1 DE 4` automáticamente? | **No.** Está dibujado como geometría, no como texto (típico de las tipografías SHX de AutoCAD) |
| ¿Hay sitio libre para el QR? | Sí. La banda encima del cajetín, a la derecha, está libre en las cuatro páginas |

El cajetín es el de la Comunidad de Madrid (Dirección General de Carreteras), no uno
de INES. La Comunidad de Madrid ha confirmado que **añadir el QR no supone ningún
problema**, lo que permite estamparlo sobre el entregable oficial sin necesidad de
mantener una copia de obra aparte.

---

## D-01 · SharePoint es el archivo oficial de los PDF

**Decisión.** Los planos siguen guardándose en SharePoint, en una biblioteca propia
dentro del sitio de cada obra. No se cambia de sistema de archivo.

**Por qué.** Ya está en uso, tiene control de permisos e historial, y no cuesta nada
adicional. Cambiar de repositorio sería un proyecto en sí mismo y no aporta nada al
problema que estamos resolviendo.

**Un matiz que conviene tener claro:** el historial de versiones de SharePoint (ese
«1.7» que aparece en las propiedades del archivo) **no tiene nada que ver con la
revisión de ingeniería.** Son dos cosas distintas que casualmente se llaman
parecido. La revisión es un dato que gestionamos nosotros; no se puede delegar en el
historial de SharePoint.

**Se descartó** crear un sitio de SharePoint separado solo para planos: partiría la
documentación de una misma obra en dos sitios con permisos independientes.

---

## D-02 · La verificación es pública, sin contraseña

**Decisión.** La página que responde «vigente» o «superado» es accesible para
cualquiera, sin cuenta y sin contraseña.

**Por qué.** Esta decisión se cambió a mitad del diseño, y el cambio fue acertado.
La idea inicial era usar una vista filtrada de SharePoint como página de
verificación. El problema es evidente en cuanto se piensa en quién escanea el QR:
el encargado de la contrata, el jefe de producción de la constructora o la
asistencia técnica del cliente. **Ninguno de ellos tiene licencia de Microsoft 365
de INES.** Una página que pide iniciar sesión les deja sin respuesta justo en el
momento en que la necesitan, y el sistema entero no sirve para nada.

**Consecuencia.** La página pública no puede enseñar los planos, solo el veredicto.
Ver D-11 sobre qué información queda visible.

---

## D-03 · La web es una página estática con un fichero de datos. Sin base de datos

**Decisión.** La web se compone de una página HTML (`index.html`) y un fichero de
datos con el listado de planos y revisiones (`planos.json`). Los dos van en la
**raíz del repositorio**, porque GitHub Pages publica la raíz y el QR impreso
apunta a la raíz del dominio. La comparación entre lo que dice el QR y lo que está
vigente **la hace el propio navegador del móvil**. No hay servidor, ni base de
datos, ni programa ejecutándose en la nube.

**Por qué.** Lo que hay que publicar son unos cientos de filas, de solo lectura, que
cambian cuando se emite un plano. Eso es un fichero, no una base de datos. Las
ventajas son concretas:

- **Carga con mala cobertura.** El fichero pesa unos pocos kilobytes.
- **Funciona casi sin red.** El móvil guarda el fichero en memoria caché, así que un
  segundo escaneo responde aunque la conexión se haya caído. Esto importa mucho: en
  túneles, viaductos y zonas ferroviarias no hay datos, y es justo donde hay planos.
- **No se puede caer.** No hay nada que mantener funcionando.
- **Coste cero.**

**Se descartó Firebase.** Firebase (concretamente Firestore) está pensado para datos
que cambian en tiempo real, con escrituras desde el móvil y permisos por usuario.
Aquí no hace falta ninguna de esas tres cosas. Meterlo obligaría a mantener un
proyecto de Google, reglas de seguridad y una librería adicional, y dejaría el dato
duplicado en dos sitios que se pueden desincronizar.

**Cuándo sí haría falta Firebase.** Si en el futuro se quiere **registrar los
escaneos** (quién consultó qué plano y cuándo, para poder demostrar que el sistema
avisó de que un plano estaba superado), entonces sí: una página estática no puede
escribir en ningún sitio y haría falta algo como Firebase. Queda apuntado como
posible fase 2.

---

## D-04 · Sin Power Automate: publica la propia herramienta

**Decisión.** No se usa Power Automate. La misma herramienta que estampa el QR es la
que actualiza el registro y lo publica en la web.

**Por qué.** Dos razones, y la segunda es la de fondo.

La primera es práctica: **Power Automate no sabe estampar una imagen dentro de un
PDF.** No es una de sus acciones. Eso significa que va a existir una herramienta
propia en el momento de emitir el plano, sí o sí. Y si esa herramienta ya existe,
añadir un segundo mecanismo que vigile SharePoint es duplicar trabajo.

La segunda es de criterio: con un flujo automático que reacciona a «ha aparecido un
fichero nuevo en la carpeta», **un borrador subido por error se convierte en plano
vigente a ojos de la obra.** Publicar una revisión tiene que ser un acto deliberado
de una persona, no un efecto secundario de guardar un archivo.

---

## D-05 · El QR se estampa sobre el PDF, no se dibuja en el CAD

**Decisión.** El QR se añade al PDF ya generado, como paso posterior al ploteo. No se
inserta como bloque en AutoCAD ni en Civil 3D.

**Por qué.** Cuatro razones, de menor a mayor importancia:

1. **Habría que hacerlo una vez por programa.** AutoCAD y Civil 3D comparten el mismo
   motor de bloques, pero Revit no. Serían dos desarrollos.
2. **Obligaría a instalar un complemento** en cada puesto para poder generar la imagen
   del QR dentro de AutoCAD. En un Windows corporativo sin permisos de administrador
   eso es una petición a informática y una dependencia permanente. Un programa en
   Python que se ejecuta en local, no.
3. **Habría que abrir y guardar el DWG**, con el riesgo que eso supone sobre ficheros
   que están en uso.
4. **La revisión no se conoce cuando se dibuja, sino cuando se emite.** Esta es la
   razón de fondo. El QR depende del número de revisión, que se asigna al emitir. Si
   el QR viviera en el cajetín del CAD, alguien tendría que acordarse de actualizarlo
   antes de plotear, y ese es exactamente el paso manual que falla y que estamos
   tratando de eliminar.

**Ventaja añadida.** A la herramienta le da igual qué programa generó el PDF. Recibe
un PDF, estampa, registra y publica. Los casos excepcionales de Revit no cuestan nada
extra, y nadie vuelve a abrir un DWG por este motivo.

**Dónde se estampa.** En la banda libre encima del cajetín, a la derecha
(aproximadamente entre 330 y 412 mm desde el borde izquierdo, y entre 25 y 45 mm
desde el borde inferior, en A3). **No se toca ni una casilla del cajetín del
cliente.** Junto al QR se imprime también el código en texto legible, para que sirva
de algo cuando no haya cobertura.

---

## D-06 · La unidad de control es el documento, no la hoja suelta

**Decisión.** Lo que se controla y se registra es el **documento PDF numerado
completo**, no cada hoja por separado. Un documento tiene una revisión, un código y
un QR, que se estampa en todas sus hojas.

**Por qué.** Se intentó hacerlo por hoja y no es posible con el cajetín actual: la
casilla `Nº:` vale lo mismo en las cuatro páginas y el `HOJA 1 DE 4` no se puede leer
automáticamente porque está dibujado como geometría (ver «Los hechos de partida»). No
hay ningún dato en el PDF que distinga una hoja de otra de forma fiable.

Pero además, mirándolo bien, **es el modelo correcto**: es el que ya usa el propio
cajetín del cliente, que numera `Nº: 01` y luego dice `HOJA 1 DE 4`. El documento es
la unidad que se emite, y las hojas son sus páginas.

**Detalle importante.** El QR se estampa en **todas** las hojas, no solo en la
primera. Así una hoja que se haya separado del conjunto sigue siendo verificable, que
es exactamente lo que pasa en obra.

---

## D-07 · El identificador es legible: `OBRA-NNN-Rxx`

**Decisión.** Cada revisión de cada documento se identifica con un código como:

```
SESENA-014-R00
  │     │    └── número de revisión (dos cifras, empieza en 00)
  │     └─────── correlativo del documento dentro de la obra
  └───────────── código corto de la obra, sin eñes ni tildes
```

**Por qué legible y no un código aleatorio.** La propuesta inicial era usar un
identificador opaco (un GUID, del tipo `8f3a7c2e-...`). Se descartó por tres motivos:

1. **Se puede dictar por teléfono.** Si el móvil no escanea, si la cámara está rota,
   si no hay cobertura o si el papel está tan sucio que el QR no se lee, el encargado
   puede llamar a la oficina y decir «Seseña, cero catorce, erre cero cero». Con un
   GUID eso es imposible, y es precisamente cuando más falta hace.
2. **El QR se genera sin consultar al servidor**, porque el código se puede calcular a
   partir de la obra, el documento y la revisión.
3. **Es más corto.** Y la longitud del código no es una cuestión estética: cuantos más
   caracteres lleva un QR, más denso es el dibujo. Ese QR va impreso a unos 18 mm en un
   A3 que en obra acaba doblado, fotocopiado y a veces mojado. **La longitud del código
   es la diferencia entre que el móvil lea o no lea.**

**Por qué el código corto de obra.** El `Nº 01` se va a repetir en todas las obras que
haga INES. Sin el prefijo de obra, el registro público se rompería en cuanto entrase
la segunda.

**Se descartó usar el expediente del cliente** (`A/OBR-036768/2026`) como
identificador. Es único de verdad, pero lleva barras, es largo, queda mal en una
dirección web y es aún peor de dictar. Se guarda como dato del registro, no como
identificador.

---

## D-08 · El número del identificador es un correlativo interno

**Decisión.** El número que aparece en el identificador (`014`) es un correlativo que
asigna la herramienta, **no el número del índice de planos**. Nunca cambia y nunca se
reutiliza.

**Por qué.** El número del índice de planos se asigna al elaborar el índice y, aunque
se procura que sea rígido, está sujeto a cambios: si se reordena el índice, un
documento que hoy es el `01` puede pasar a ser el `03`. Si ese número formara parte del
identificador, **cada reordenación del índice invalidaría todos los QR ya impresos y
repartidos por la obra.**

También se consideró meter la denominación del plano en el identificador, que es más
estable que el número. Se descartó por lo mismo y por longitud: `SESENA-PLANOS
SENALIZACION PROVISIONAL-01-R00` son 45 caracteres, que en una dirección web se
convierten en 57 porque los espacios se codifican. Y la denominación tampoco es
inmutable: basta con que alguien escriba «SEÑALIZ. PROVIS.» o le corrija una tilde.

**La regla que resume todo esto:**

> En el QR va solo lo que no puede cambiar nunca. Todo lo demás es un dato del
> registro y se muestra en la pantalla.

**Consecuencias que hay que conocer:**

- **Habrá huecos en la numeración.** Si un documento se anula, su correlativo se retira
  y no se vuelve a usar. Es intencionado: reutilizar un número haría que un QR antiguo
  apuntase a un documento distinto, que es el fallo más grave posible.
- **El correlativo refleja el orden en que se emitieron los documentos**, no el orden
  del índice. La página los ordena por índice al mostrarlos, así que en el uso diario
  no se nota.
- **El correlativo no significa nada para una persona**, y no hace falta que
  signifique: es una matrícula. El contexto humano (denominación, título, número de
  índice) lo pone la pantalla al escanear.
- **Riesgo a vigilar:** el correlativo y el `Nº` del cajetín se pueden confundir. Por
  eso **la serie arranca en 101**, no en 001: un `101` no se parece a un `Nº 01`. Y la
  pantalla etiqueta los dos por separado, indicando expresamente que el nº de índice
  que muestra es «según el cajetín de este papel».

---

## D-09 · Sin código de verificación (hash)

**Decisión.** El identificador no lleva ningún código de comprobación añadido.

**Por qué.** Se propuso inicialmente añadir cuatro caracteres de verificación
(`SESENA-014-R00-7F3A`) y se descartó tras revisarlo: no aportaba nada.

- Un código inventado ya devuelve «CÓDIGO NO VÁLIDO» simplemente porque no está en el
  registro.
- Falsificar un QR a mano sobre un plano impreso no es un escenario real.

Solo añadía complejidad y cuatro caracteres más que dictar por teléfono.

---

## D-10 · El número de índice y las hojas se guardan por revisión

**Decisión.** El registro se organiza por documento, y dentro de cada documento hay una
lista de revisiones. El número de índice y el número de hojas se guardan **dentro de
cada revisión**, no en el documento.

```json
{
  "id": "SESENA-014",
  "denominacion": "PLANOS SEÑALIZACIÓN PROVISIONAL",
  "titulo": "Planta general zona de obra",
  "expediente": "A/OBR-036768/2026",
  "vigente": "01",
  "revisiones": [
    {"rev": "00", "fecha": "2026-09-02", "n_indice": "01", "hojas": 4,
     "estado": "superado"},
    {"rev": "01", "fecha": "2026-09-20", "n_indice": "03", "hojas": 5,
     "estado": "vigente", "motivo": "Ampliación de la zona de obra"}
  ]
}
```

**Por qué.** Si el número de índice se guardara una sola vez por documento, al
reordenar el índice pasaría lo siguiente: el papel que el encargado tiene en la mano
sigue diciendo `Nº: 01` en el cajetín, pero la pantalla le diría `Nº de índice: 03`.
**La pantalla contradiría al papel**, y eso destruye la confianza en el sistema aunque
el veredicto vigente/superado sea correcto.

Guardando el número de índice dentro de cada revisión, cada revisión recuerda el número
que tenía cuando se emitió, y la pantalla siempre coincide con el papel que se está
escaneando.

Lo mismo se aplica al número de hojas: una revisión puede añadir o quitar hojas.

**Extra que se gana.** El campo `motivo` permite que el encargado vea *por qué* cambió
el plano, que es información que hoy no llega a la obra de ninguna manera.

---

## D-11 · El listado público es indexable por buscadores

**Decisión.** La web se publica sin restricciones y se deja indexar por los buscadores.
INES lo ha aceptado expresamente.

**Qué queda visible para cualquiera:** nombre de la obra, denominación de cada
documento, título, número de índice, número de revisión y fecha de emisión.

**Qué NO queda visible:** los PDF, la geometría, las cotas, los detalles constructivos
y cualquier contenido técnico. La web solo contiene el listado.

**Lo que hay que entender antes de aceptarlo.** Aunque no haya contenido técnico, el
listado sí revela que la obra existe, cómo está estructurada su documentación y con qué
frecuencia se revisan los planos.

**Por qué se acepta.** Es la contrapartida directa de D-02: si el sistema tiene que
funcionar para quien no tiene cuenta de INES, la información tiene que ser accesible
sin cuenta. Además permite usar alojamiento gratuito (GitHub Pages), donde el
repositorio público es la única opción sin pasar a un plan de pago.

**Consecuencia práctica y crítica.** El repositorio va a ser público. **Por tanto,
ningún plano puede subirse nunca a él.** La carpeta `muestras/` está excluida en
`.gitignore` por este motivo, junto con los `.dwg` y la carpeta de salida.

---

## D-12 · El correlativo no aparece en el nombre del fichero

**Decisión.** Los ficheros siguen nombrándose como hasta ahora, por número de índice:
`01_DESVIOS_PROVISIONALES_R00.pdf`. El correlativo interno vive solo en el registro y
dentro del QR.

**Por qué.** Si el correlativo fuera lo primero del nombre del fichero, la carpeta de
SharePoint se ordenaría por orden de emisión en lugar de por índice, que es como los
delineantes esperan verla. **La decisión D-08 no debe cambiarle la forma de trabajar a
nadie.**

---

## D-13 · La web se aloja en GitHub Pages

**Decisión.** La web se publica en GitHub Pages, con la dirección que da GitHub por
defecto, sin dominio propio de momento.

**Por qué.** Es gratis, no hay que pedir nada a nadie y se puede montar hoy. Es una
decisión consciente de arrancar rápido.

**Lo que hay que entender: la dirección de la web es el dato más irreversible de todo
el sistema**, porque va impresa en papel que va a estar años en la caseta de obra. Un
plano impreso no se puede actualizar.

**Condición obligatoria que se deriva de esto.** El repositorio **tiene que estar en
una cuenta de organización de INES**, no en la cuenta personal de nadie. Si los QR
apuntasen a la cuenta personal de un empleado y esa persona dejase la empresa o
cerrase la cuenta, **todos los planos impresos en obra dejarían de verificarse y no
habría forma de repararlos.**

**Cómo se migra a un dominio propio más adelante, si se quiere.** No hay que reimprimir
nada: se deja vivo el sitio de GitHub redirigiendo al nuevo dominio y los QR antiguos
siguen funcionando. Por eso esta decisión no encierra al proyecto, siempre que se
cumpla la condición de la cuenta de organización.

**Se descartó de momento** un subdominio propio (`planos.inesingenieros.com`), que
sería técnicamente mejor: más corto (y por tanto mejor lectura del QR) e independiente
del proveedor. Requiere un registro DNS de quien administre el dominio. Queda como
mejora futura, no como bloqueo.

---

## D-14 · Solo librerías con licencia permisiva

**Decisión.** La herramienta usa `pypdf`, `reportlab`, `qrcode`, `pillow` y `PyYAML`,
todas con licencia BSD o MIT.

**Por qué.** La librería más cómoda para este trabajo es PyMuPDF: hace en una línea lo
que aquí ocupa un módulo entero. Pero tiene **licencia AGPL**, que obliga a publicar el
código de cualquier cosa que la use y se distribuya. Para una consultora eso es una
carga jurídica que no compensa por ahorrar unas líneas, sobre todo si algún día esto se
reparte a otras oficinas o se ofrece a un cliente.

**Coste de la decisión.** El estampado ocupa más código del que ocuparía con PyMuPDF.
Es un coste asumido a cambio de no tener que pensar nunca más en la licencia.

---

## D-15 · El QR mide 20 mm y va en la banda sobre el cajetín

**Decisión.** El sello se coloca en la banda libre entre el techo del cajetín y el
borde inferior de la ortofoto, con el QR de 20 mm de lado. Medidas sobre el plano real
de Seseña (A3 apaisado):

| Referencia | Cota |
|---|---|
| Borde derecho del marco del plano | 399,7 mm desde el borde izquierdo |
| Techo del cajetín | 21,8 mm desde el borde inferior |
| Borde inferior de la ortofoto | 43,9 mm desde el borde inferior |
| **Banda limpia disponible** | **22 mm de alto** |
| QR: lado / margen derecho / margen inferior | 20 / 24 / 23 mm |

Así el sello **no toca ninguna casilla del cajetín, no se sale del marco y no tapa el
dibujo**.

**El problema que apareció al construirlo, y que no habíamos previsto.** Un QR tiene
tantos módulos como información lleva, y cuanto más pequeño es cada módulo, más difícil
es que un móvil lo lea sobre papel. Por debajo de unos **0,60 mm de lado de módulo** los
lectores empiezan a fallar con papel impreso, fotocopiado, doblado o mojado.

Con la dirección de GitHub Pages y 20 mm de QR, el módulo sale de **0,54 mm**: por
debajo del umbral. Las combinaciones medidas, todas con corrección de errores Q (25 %):

| Dirección | Caracteres | Módulos | mm/módulo a 20 mm |
|---|---|---|---|
| `https://inesingenieros.github.io/control-planos/?p=…` | 65 | 45 | 0,44 |
| `https://inesingenieros.github.io/?p=…` | 50 | 41 | 0,49 |
| `HTTPS://INESINGENIEROS.GITHUB.IO/?P=…` | 50 | 37 | **0,54** |

**Dos hallazgos que se derivan de esto:**

1. **La dirección en MAYÚSCULAS reduce la densidad del QR.** El formato QR tiene un modo
   alfanumérico que solo admite mayúsculas y cifras, y comprime bastante más que el modo
   general. El esquema y el dominio de una dirección web son insensibles a mayúsculas, y
   del parámetro nos encargamos nosotros: la web acepta tanto `?p=` como `?P=`. Es un
   truco sin coste que ahorra cuatro módulos.
2. **La longitud de la dirección dejó de ser una cuestión estética.** El repositorio debe
   ser el sitio raíz de la organización (`inesingenieros.github.io`), sin nombre de
   repositorio en la ruta. Y esto **refuerza con números el subdominio propio** que se
   descartó en la D-13: `HTTPS://PLANOS.INES.ES/?P=…` bajaría a 0,65 mm y quedaría con
   holgura.

**Resultado del ensayo en papel (3 de septiembre de 2026): el QR se lee bien.** Se
imprimió una hoja A3 sellada a tamaño real y se escaneó con móvil sin dificultad. Los
0,54 mm de lado de módulo son suficientes, así que **se mantienen los 20 mm de QR y la
dirección de GitHub Pages**.

Esto confirma que el umbral de 0,60 mm era prudente, no un límite: se deja configurado
como aviso, no como impedimento, porque sigue siendo útil para detectar el día en que
alguien alargue la dirección o encoja el QR sin darse cuenta.

**Lo que queda por comprobar, sin urgencia:** el mismo ensayo **sobre una fotocopia** de
la hoja, que es lo que de verdad acaba circulando por la obra, y con un móvil viejo. Si
alguno de esos casos falla, la salida ya está identificada y medida: un subdominio
propio corto sube el módulo a 0,65 mm sin tocar nada más.

**La herramienta avisa sola.** Si el módulo baja del umbral configurado, la emisión
sigue adelante pero imprime una advertencia con el tamaño real y el que haría falta. No
falla en silencio.

---

## D-16 · Accesos directos, no ficheros `.bat`

**Decisión.** La herramienta se usa desde dos accesos directos (`Emitir plano.lnk` y
`Publicar en la web.lnk`) que apuntan a `python.exe`. No hay ficheros `.bat`.

**Por qué.** Se construyeron primero como `.bat`, que es lo natural para arrastrar un
fichero encima. No funcionaron: **en el Windows corporativo de INES está prohibido
ejecutar `.bat`.** Al arrastrar el PDF, Windows responde:

> «Windows no tiene acceso al dispositivo, ruta de acceso o archivo especificado.
> Puede que no tenga los permisos apropiados para tener acceso al elemento.»

Se comprobó que no era un problema del fichero: **un `.bat` de dos líneas que solo hace
`echo` falla igual**, con «Acceso denegado». Se descartaron una por una las causas
habituales:

| Sospecha | Comprobación |
|---|---|
| Marca de «fichero descargado» | No hay flujos alternativos en el fichero |
| Permisos de la carpeta | `INTRANET\pia` tiene control total |
| Reglas ASR de Defender | Ninguna configurada |
| Asociación de `.bat` rota | Correcta (`batfile="%1" %*`) |
| Codificación del fichero | ASCII plano, sin BOM |
| Que falte `cmd.exe` | Existe |

Queda por tanto una **política del equipo** que bloquea la ejecución de scripts `.bat`,
que es exactamente el tipo de restricción que había que prever en un entorno
corporativo.

**La solución.** Un acceso directo **no es un script**: es un puntero a un ejecutable,
y `python.exe` sí está permitido (se comprobó). Y conserva lo único que hacía falta:
**arrastrar un fichero sobre un acceso directo le pasa su ruta como argumento**, igual
que con un `.bat`.

**Consecuencias:**

- La lógica de publicar, que estaba escrita en el `.bat`, se ha reescrito en Python
  (`src/control_planos/publicar.py`). Mejor sitio: ahora se puede probar.
- La herramienta acepta `--pausar`, que espera a que se pulse Intro antes de cerrar.
  Sin eso, al lanzarse desde el explorador la ventana se cerraría de golpe y no se
  leería el resultado.
- Los `.lnk` llevan rutas absolutas, así que **no se suben al repositorio**. En un
  puesto nuevo se regeneran con `py crear_accesos.py`, que también deja constancia de
  por qué existen.

**Lección que conviene recordar.** El entorno de destino no se supone: se prueba. Este
fallo no lo habría detectado ningún test, porque no está en el código.

---

## Pendiente de decidir

Cosas identificadas pero todavía sin resolver. Se irán incorporando a este documento a
medida que se cierren.

| Tema | Qué hay que decidir |
|---|---|
| Cuenta de GitHub | Crear la organización de INES en GitHub. El repositorio debe ser el sitio raíz (`inesingenieros.github.io`), no uno con nombre, para que la dirección sea corta (ver D-15) |
| Ensayo sobre fotocopia | El QR ya se ha validado sobre impresión directa. Falta probarlo sobre una fotocopia y con un móvil viejo (ver D-15) |
| Disparador automático | Si la emisión se lanza desde SharePoint en vez de a mano. Viable, pero el disparador no puede ser «ha aparecido un fichero» (ver D-04) |
| Tipografía alojada | Montserrat se carga hoy de Google. Alojar el `.woff2` en el repositorio quitaría esa dependencia |
| Replicación entre obras | Cómo se configura una obra nueva sin repetir el montaje a mano cada vez. La vía correcta es un tipo de contenido centralizado en SharePoint, no recrear las columnas una por una |
| Planos ya emitidos | Qué revisión se asigna a los planos que ya están en obra sin QR |
| Registro de escaneos | Si interesa saber quién consultó qué y cuándo. Ver D-03 |
| Anulación de documentos | Cómo se marca un documento retirado que no ha sido sustituido por otro |
| Código de obra | Quién asigna el código corto de cada obra y dónde se anota para que no se repita |
