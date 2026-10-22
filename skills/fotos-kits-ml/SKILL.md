---
name: "fotos-kits-ml"
description: "Arma las fotos de las publicaciones de kits de LaRepuestera para MercadoLibre (kit de service, tren delantero, distribución, amortiguadores, etc.) con Canva: portada en fondo blanco y fotos secundarias de 'qué incluye', compatibilidad y envío. Revisa cada foto contra las reglas de fotos de ML y avisa si alguna no cumple, y avisa si algún producto queda estirado, aplastado o cortado al armar el collage. Usala siempre que el usuario pida fotos, imágenes, portadas o collages para publicaciones de ML, aunque no diga 'skill' ni 'Canva'."
---

# Fotos de kits para MercadoLibre (LaRepuestera)

Arma las fotos de una publicación de kit y las controla antes de entregarlas. Lo importante es que la foto **no le traiga problemas con ML** (publicación con baja exposición o pausada) y que **el comprador vea exactamente lo que recibe** (si no, hay reclamos y se pierde reputación).

## Datos que pedir (solo los que falten)
- Nombre del kit y qué piezas trae (marca y código de cada una, litros de aceite)
- Autos compatibles: modelo, motor y años
- Fotos reales de cada pieza o del kit armado. Sirven fotos de celular sobre la mesa: el fondo se saca después
- Logo de LaRepuestera (una sola vez; si ya está en Canva, usar ese)

Cómo usar cada tipo de foto que suele mandar:
- **Pieza con su caja** (ej. filtro Wega con la caja al lado): ideal para la portada, porque muestra la marca real.
- **Fotos de catálogo del fabricante**: sirven, pero muchas tienen fondo gris claro o sombra, no blanco puro. Siempre sacarles el fondo antes de usarlas.
- **Foto del auto** (ej. un Cronos): solo en la foto "Compatible con", nunca en la portada, porque el auto no viene en el kit.

Si el usuario no tiene fotos reales, decirlo claro: **no se inventan fotos del producto con IA**. Una imagen generada de un filtro o un bidón no es el producto que se entrega y ML lo toma como engañoso. Sí se puede usar IA para fondos o íconos de las fotos secundarias.

## Fotos que se arman por publicación
1. **Portada**: el kit completo sobre fondo blanco puro, sin textos, logos ni marcas de agua. Todas las piezas a la vista, juntas, como si fuera una sola foto.
2. **Qué incluye**: cada pieza con su nombre y marca, cantidad (ej. "4 litros"). Puede llevar el logo de LaRepuestera.
3. **Compatible con**: modelos, motores y años, en letra grande.
4. **Envío**: "Despacho en el día", "Factura A y B", lo que aplique y sea cierto.
5. Opcional: foto real de cada pieza con su código visible.

Formato de todas: cuadrada, 1200 × 1200 px, JPG.

## Pasos
1. **Sacar el fondo** de cada foto real con `remove-background` de Canva (o pedir la foto ya recortada).
2. **Armar la portada** con el script, que solo escala proporcionalmente y por eso no puede deformar:
   ```bash
   python scripts/armar_portada.py --salida portada.jpg pieza1.png pieza2.png ...
   ```
   Imprime cuánto se achicó cada pieza. Si una pieza quedó mucho más chica que las otras (por ejemplo un filtro de habitáculo al lado de un bidón), está bien; si quedó tan chica que no se reconoce, avisar y proponer otra distribución o una foto aparte.
3. **Fotos secundarias** en Canva con `create-design` (formato cuadrado, 1200 × 1200). La primera vez armar una plantilla con el logo; para los demás kits, copiarla con `copy-design` y cambiar solo textos y fotos con `edit-design`. Mostrar la vista previa y pedir aprobación antes de guardar (commit).
4. **Exportar** cada diseño como JPG 1200 × 1200 con `export-design` y descargarlo.
5. **Revisar todas las fotos** (siempre, también las que armó Canva):
   ```bash
   python scripts/revisar_fotos.py --portada portada.jpg secundaria1.jpg secundaria2.jpg ...
   ```
   Además mirar cada imagen con la herramienta de lectura de imágenes, porque el script no lee texto: buscar en la portada cualquier texto, logo o marca de agua, y en todas teléfonos, redes, links o direcciones.
6. **Revisar deformación** de cada foto colocada en Canva: comparar el tamaño original de la foto con el tamaño del cuadro donde quedó (lo da `read-design`):
   ```bash
   python scripts/revisar_fotos.py --deformacion 3024x4032:600x800 1200x1200:900x700
   ```
   Formato: `ancho_original x alto_original : ancho_en_diseño x alto_en_diseño`. Si Canva recorta la foto en vez de estirarla, revisar en la vista previa que no se haya cortado parte de la pieza.

## Cuándo avisar (y cómo)
Avisar en una lista corta, una línea por problema, diciendo **qué foto**, **qué pasa** y **cómo se arregla**. Separar:
- **No cumple ML** (hay que arreglarlo antes de publicar): ver `references/politicas-ml.md`.
- **Deformada** (hay que arreglarlo): una pieza estirada o aplastada más de 2%, o cortada.
- **Conviene mejorar** (se puede publicar igual): foto chica pero aceptable, pieza que ocupa poco, poco contraste.

Si todo está bien, decir solo "Las N fotos cumplen y ninguna pieza está deformada".

## Cómo responder
- Corto y en español simple, sin palabras técnicas
- Entregar las fotos finales (archivos JPG) y el link de Canva de cada diseño
- No publicar ni subir nada a ML: eso lo hace el usuario
