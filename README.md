# Robot de Proveedores

Actualiza todos los días precios y stock de los proveedores en ComercioCity,
por automatización del navegador (sin API). Diseño completo en
[ARQUITECTURA.md](ARQUITECTURA.md).

---

# ETAPA 1 — Estructura base

Al terminar esta etapa vas a tener el robot instalado en `C:\ROBOT_PROVEEDORES`,
con un agente que recorre dos proveedores **de prueba** (uno anda bien y otro
falla a propósito), reintenta, sigue de largo, escribe el log y muestra la
duración. Todavía no entra a ningún sitio real.

## Paso 1 — Instalar Python

1. Entrá a https://www.python.org/downloads/ y descargá **Python 3.12** (o más nuevo).
2. Ejecutá el instalador. **MUY IMPORTANTE:** en la primera pantalla tildá
   **"Add python.exe to PATH"**. Después "Install Now".
3. Comprobá: abrí **PowerShell** (tecla Windows → escribí `powershell` → Enter) y ejecutá:

```bash
python --version
```

Deberías ver algo como `Python 3.12.7`.

> **Si dice "no se reconoce como comando"**: no tildaste "Add to PATH".
> Volvé a ejecutar el instalador → "Modify" → tildá "Add Python to environment variables".
> Cerrá y abrí PowerShell de nuevo.

## Paso 2 — Instalar Git y bajar el proyecto

Git guarda el historial de cambios del programa: si algo se rompe, se puede volver atrás.

1. Descargá Git de https://git-scm.com/download/win e instalalo (dejá todas las opciones por defecto).
2. Cerrá y abrí PowerShell. Ejecutá (una línea por vez):

```bash
cd C:\
```

```bash
git clone -b claude/dazzling-einstein-yg4j2o https://github.com/nicoservian/carpetahenry.git ROBOT_PROVEEDORES
```

```bash
cd C:\ROBOT_PROVEEDORES
```

Te va a pedir iniciar sesión en GitHub la primera vez (el repositorio es tuyo).
Deberías ver las carpetas `config`, `core`, `proveedores`, `herramientas` y el archivo `agent.py`.

> **Más adelante, para traer las actualizaciones** que vayamos haciendo:
> `cd C:\ROBOT_PROVEEDORES` y luego `git pull`.

## Paso 3 — Crear el entorno virtual e instalar librerías

Un *entorno virtual* es una carpeta (`.venv`) con las librerías del robot,
separadas del resto de tu PC.

```bash
python -m venv .venv
```

```bash
.venv\Scripts\Activate.ps1
```

Ahora el renglón de PowerShell empieza con `(.venv)`. **Cada vez que abras
PowerShell para trabajar con el robot, hacé `cd C:\ROBOT_PROVEEDORES` y este
`Activate.ps1`.**

> **Si aparece "la ejecución de scripts está deshabilitada en este sistema"**, ejecutá
> esto una sola vez y volvé a intentar el Activate:
> ```bash
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> (respondé `S` o `Y`).

Instalá las librerías:

```bash
pip install -r requirements.txt
```

Tarda uno o dos minutos. Al final dice `Successfully installed ... playwright ... pandas ...`.

Instalá el navegador de Playwright (respaldo por si falla Chrome):

```bash
playwright install chromium
```

## Paso 4 — Probar que el robot puede abrir Chrome

```bash
python herramientas/probar_navegador.py
```

**Qué deberías ver:** se abre una ventana de Chrome, entra a "Example Domain",
se cierra sola, y en PowerShell aparece:

```
OK: el navegador funciona. Captura guardada en C:\ROBOT_PROVEEDORES\logs\capturas\prueba_navegador.png
```

Abrí esa imagen para comprobarlo.

> **Si dice `No pude abrir 'chrome'`** y después funciona igual: no encontró tu
> Google Chrome y usó el Chromium de Playwright. Funciona igual; si querés, en
> `config\settings.yaml` cambiá `canal: chrome` por `canal: chromium`.
> **Si dice `Executable doesn't exist`**: faltó el paso `playwright install chromium`.

## Paso 5 — Ejecutar el agente

```bash
python agent.py
```

**Qué deberías ver** (tarda ~1:30 porque espera entre reintentos):

```
10:00:03 | INFO    | AGENTE       | Inicio del agente ...
10:00:03 | INFO    | AGENTE       | MODO SIMULACIÓN activo: ComercioCity NO se va a modificar
10:00:03 | INFO    | AGENTE       | Conexión a Internet OK
10:00:03 | INFO    | AGENTE       | Proveedores a procesar: 2 → demo_ok, demo_error
10:00:03 | INFO    | demo_ok      | Proveedor OK
10:00:03 | WARNING | demo_error   | Descarga: falló el intento 1 de 3 (...). Reintento en 30 s.
10:00:33 | WARNING | demo_error   | Descarga: falló el intento 2 de 3 (...). Reintento en 60 s.
10:01:33 | ERROR   | demo_error   | ERROR en etapa 'descarga': ErrorTemporal: timeout simulado ...
...
10:01:33 | INFO    | AGENTE       | PROVEEDORES PROCESADOS: 2
10:01:33 | INFO    | AGENTE       | CORRECTOS: 1
10:01:33 | INFO    | AGENTE       | CON ERROR: 1
10:01:33 | INFO    | AGENTE       |   - Demo con error [ERROR] etapa 'descarga': ...
```

Ese ERROR es **a propósito**: demuestra que un proveedor que falla se reintenta
y **no frena** a los demás.

## Paso 6 — Comprobar que funciona

1. Abrí `C:\ROBOT_PROVEEDORES\logs\` → tiene que existir `2026-11-10.log`
   (con la fecha de hoy) con lo mismo que viste en pantalla.
2. Probá un solo proveedor:
   ```bash
   python agent.py --proveedor demo_ok
   ```
   Debe terminar con `CORRECTOS: 1` y `CON ERROR: 0` en pocos segundos.
3. Probá el bloqueo: abrí **dos** PowerShell, activá el entorno en los dos y
   lanzá `python agent.py` en ambos casi a la vez. El segundo tiene que decir
   `Ya hay un robot ejecutándose ... Se cancela esta ejecución.`
4. Probá una credencial (Administrador de credenciales de Windows):
   ```bash
   python herramientas/guardar_credencial.py DIMAC
   ```
   Escribí usuario y clave (la clave no se ve al escribir, es normal).
   Debe responder `Credencial DIMAC guardada.`

## Qué hacer si aparece un error

| Mensaje | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'yaml'` (u otro) | No activaste el entorno: `.venv\Scripts\Activate.ps1` y repetí. Si sigue: `pip install -r requirements.txt`. |
| `No hay conexión a Internet` | Revisá la conexión. Para probar sin Internet: en `config\settings.yaml` poné `verificar_internet: false`. |
| `Config inválida en proveedores/...` | Ese `config.yaml` tiene un error de escritura. Revisá que los `:` y las sangrías (espacios, no TAB) estén igual que en la plantilla. |
| Cualquier otro | Copiame el mensaje completo y las últimas líneas de `logs\<fecha>.log`. |

---

## Comandos útiles

| Comando | Para qué |
|---|---|
| `python agent.py` | Ejecución completa |
| `python agent.py --proveedor NOMBRE` | Solo un proveedor (nombre de su carpeta) |
| `python agent.py --forzar` | Ignora los días configurados |
| `python herramientas/guardar_credencial.py NOMBRE` | Guarda usuario/clave en Windows |
| `python herramientas/probar_navegador.py` | Prueba Chrome + Playwright |

## Carpetas

| Carpeta | Contenido |
|---|---|
| `config/` | `settings.yaml`: configuración general |
| `core/` | Motores comunes (no hace falta tocarlos para agregar proveedores) |
| `proveedores/` | Una carpeta por proveedor; `_plantilla` para copiar |
| `herramientas/` | Utilidades sueltas |
| `dimac/` | Scripts anteriores de Dimac (se migran a `proveedores/dimac` en la Etapa 2) |
| `descargas/`, `procesados/`, `historico/`, `logs/`, `reportes/`, `backups/` | Datos: se crean solos, no se suben a git |
