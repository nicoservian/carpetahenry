# Robot de Proveedores — Arquitectura

Objetivo: todos los días a las 10:00 el agente se ejecuta solo, descarga las
listas de todos los proveedores, detecta cambios, actualiza ComercioCity (sin
API, por navegador), verifica que se haya aplicado y entrega un reporte.

## 1. Idea central

**Un solo agente + un plugin por proveedor + motores comunes.**

El agente (`agent.py`) no sabe nada de ningún proveedor en particular. Recorre
la carpeta `proveedores/`, y cada subcarpeta es un proveedor. Agregar el
proveedor 31 = copiar la carpeta `_plantilla`, completar `config.yaml` y
(solo si el sitio es raro) escribir un `descarga.py` chico. No se toca el resto
del programa.

Todo lo que es igual para los 30 proveedores (leer Excel/CSV, detectar
columnas, validar, comparar, guardar histórico, reportar, actualizar
ComercioCity) vive **una sola vez** en `core/` y `comerciocity/`.

## 2. Estructura final de carpetas

```
C:\ROBOT_PROVEEDORES\
│
├── agent.py                  ← programa principal (lo que ejecuta el Programador de tareas)
├── ejecutar_agente.bat       ← (etapa 6) atajo para el Programador de tareas
├── requirements.txt          ← librerías de Python
├── .env                      ← credenciales (NO se sube a git)  [o Windows Credential Manager]
│
├── config\
│   └── settings.yaml         ← configuración general: headless, reintentos, límites por defecto, modo simulación
│
├── core\                     ← MOTORES COMUNES (código)
│   ├── config.py             ← lee settings.yaml + config.yaml de cada proveedor
│   ├── logs.py               ← logs/AAAA-MM-DD.log
│   ├── bloqueo.py            ← impide dos ejecuciones simultáneas
│   ├── credenciales.py       ← Windows Credential Manager / .env
│   ├── red.py                ← verifica Internet
│   ├── reintentos.py         ← reintentos con espera creciente
│   ├── navegador.py          ← (etapa 2) abre Chrome con Playwright, screenshots de error
│   ├── descarga.py           ← (etapa 2) login + descarga genérica por "receta" del config
│   ├── lectura.py            ← (etapa 2) abre xlsx/xls/csv/txt, detecta fila de encabezados
│   ├── normalizacion.py      ← (etapa 2) columnas del proveedor → estructura estándar
│   ├── validacion.py         ← (etapa 4) reglas de seguridad
│   ├── comparacion.py        ← (etapa 2) nuevo vs. anterior → cambios
│   ├── historico.py          ← (etapa 2) base SQLite historico/historico.db
│   └── reportes.py           ← (etapa 2) reporte_AAAA-MM-DD.html / .xlsx
│
├── comerciocity\             ← MÓDULO DEL ERP (etapa 3)
│   ├── sesion.py             ← login y navegación
│   ├── importador.py         ← subir archivo, esperar, leer resultado, filas rechazadas
│   ├── exportador.py         ← backup: exportar precios actuales antes de modificar
│   └── verificacion.py       ← busca N productos al azar y confirma precio/stock
│
├── proveedores\              ← UN PLUGIN POR PROVEEDOR
│   ├── _plantilla\config.yaml
│   ├── dimac\
│   │   ├── config.yaml       ← URL, login, columnas, reglas, límites
│   │   └── descarga.py       ← (opcional) solo si la receta genérica no alcanza
│   └── ...
│
│   ─── carpetas de DATOS (se crean solas, no van a git) ───
├── descargas\<proveedor>\<fecha>\<hora>_<archivo original>   ← nunca se sobrescribe
├── procesados\<proveedor>\<fecha>\normalizado.xlsx
├── comerciocity\salida\<fecha>\  ← archivos de importación generados para el ERP
├── historico\historico.db        ← SQLite con todo el histórico auditable
├── backups\<fecha>\              ← export de ComercioCity antes de tocarlo + copia de la DB
├── reportes\reporte_<fecha>.html / .xlsx
└── logs\<fecha>.log   +  logs\capturas\<fecha>\<proveedor>_<etapa>_<hora>.png
```

## 3. El flujo de un día

```
10:00  Programador de tareas → agent.py
       ├─ Toma el BLOQUEO (si ya hay otro agente corriendo, sale)
       ├─ Verifica Internet
       ├─ Carga settings.yaml + proveedores habilitados (ordenados por prioridad)
       │
       ├─ FASE A — por cada proveedor (aislado: si falla, sigue con el próximo)
       │    DESCARGA      login + bajar archivo (con reintentos)
       │    LECTURA       abrir el archivo, ¿está vacío / corrupto?
       │    NORMALIZACIÓN columnas propias → provider_code, oem, description,
       │                  brand, price, stock, iva, applications
       │    VALIDACIÓN    reglas de seguridad → OK / ADVERTENCIA / BLOQUEADO
       │    COMPARACIÓN   contra la última lista APROBADA del proveedor
       │    PREPARACIÓN   arma las filas a enviar a ComercioCity
       │
       ├─ FASE B — ComercioCity (una sola sesión, solo proveedores aprobados)
       │    BACKUP        exportar precios actuales
       │    IMPORTACIÓN   subir archivo por proveedor, esperar fin, leer errores
       │    VERIFICACIÓN  buscar muestra de productos y comparar
       │
       ├─ Guarda histórico (SQLite) y marca la lista como "aplicada"
       ├─ Genera reporte HTML + Excel
       └─ Libera el bloqueo, registra inicio/fin/duración
```

### ¿Por qué dos fases (A y B)?

- La descarga de proveedores es lo que más falla (sitios caídos, timeouts).
  ComercioCity es lo más delicado (es tu sistema real). Separarlos hace que
  un proveedor caído nunca deje ComercioCity a medio actualizar.
- ComercioCity se abre **una sola vez** por día, no 30.
- Permite el **modo simulación**: correr la fase A completa y generar los
  archivos para ComercioCity **sin subirlos**. Las primeras semanas el robot
  trabaja así y vos revisás el reporte; cuando confiás, se activa la subida.

## 4. Decisiones importantes y por qué

| Tema | Decisión | Por qué |
|---|---|---|
| Configuración | YAML por proveedor | Se lee como texto, admite comentarios, un principiante puede editarlo. |
| Sitios distintos | **Receta genérica** en YAML (URL, campos de login, texto del botón de descarga) **+ `descarga.py` opcional** | El 70% de los sitios se resuelven con la receta; los raros (como Dimac) llevan un poco de código propio, aislado en su carpeta. |
| Detección de columnas | Mapeo explícito en el config **+** detección automática por sinónimos ("SKU", "Código Artículo", "Cod." → `provider_code`) | La detección automática ayuda a dar de alta; el mapeo explícito garantiza que mañana no cambie de opinión. Si falta una columna obligatoria → se detiene ese proveedor. |
| Histórico | **SQLite** (`historico.db`, un archivo, sin instalar nada) | Permite consultar "¿cuándo cambió el precio de X?" y comparar rápido. Los archivos originales igual quedan guardados. |
| Comparación | Contra la última lista **aprobada**, no la última descargada | Si ayer llegó una lista rota y se bloqueó, hoy no hay que compararse contra la lista rota. |
| ComercioCity | **Importación de archivo** por su pantalla de importación, no edición producto por producto | 1 importación de 10.000 filas tarda minutos; editar 10.000 productos a mano con el robot tardaría horas y fallaría más. Si alguna actualización solo se puede hacer por pantalla, el módulo lo soporta como caso aparte. |
| Selectores | `get_by_role`, `get_by_label`, `get_by_text`, IDs estables; CSS solo como último recurso. Esperas con `expect(...)`, `wait_for_load_state`, `expect_download()` | Nada de coordenadas ni `sleep(10)`. |
| Credenciales | Windows Credential Manager (librería `keyring`), con `.env` como alternativa | La contraseña queda cifrada por Windows, atada a tu usuario. Nunca en el código ni en git. |
| Errores | Errores **temporales** (timeout, caída, descarga incompleta) se reintentan; errores **definitivos** (contraseña incorrecta, columnas faltantes) NO | Reintentar una contraseña incorrecta 3 veces puede bloquearte la cuenta del proveedor. |
| Doble ejecución | Archivo de bloqueo que el sistema operativo libera solo si el proceso muere | Si el robot de ayer quedó colgado, hoy no se pisan. No queda un bloqueo "huérfano" tras un corte de luz. |
| Sesiones | Un contexto de navegador separado por proveedor, guardando cookies (`storage_state`) | Menos logins diarios (menos captchas), y un proveedor no "ensucia" la sesión del otro. |
| Archivos | `descargas/<prov>/<fecha>/<hora>_<nombre>` + hash SHA-256 | Nunca se sobrescribe; si el archivo de hoy es idéntico al de ayer, se detecta. |
| Versionado | Git (este repositorio) | Si un cambio rompe algo, se vuelve atrás. Los datos y el `.env` quedan fuera de git. |

## 5. Estructura interna estándar (después de normalizar)

| Campo | Descripción |
|---|---|
| `provider_code` | Código del proveedor (CLAVE para comparar) |
| `oem` | Código original / interno |
| `description` | Descripción |
| `brand` | Marca |
| `price` | Precio (número, con la regla de IVA del proveedor aplicada) |
| `iva` | Alícuota de IVA (21 / 10.5) |
| `stock` | Stock numérico o disponibilidad (`SI/NO` → 1/0 según regla) |
| `applications` | Vehículos / aplicaciones |
| `extra` | Cualquier otra columna útil, se conserva |

## 6. Reglas de seguridad (configurables por proveedor)

| Regla | Acción por defecto |
|---|---|
| Archivo vacío / corrupto / no descargado | DETENER proveedor |
| Columnas obligatorias faltantes | DETENER proveedor |
| Cantidad de productos < X% de lo habitual | DETENER ("POSIBLE ERROR EN LISTA DEL PROVEEDOR") |
| Variación de precio > X% en un producto | ADVERTENCIA (no se actualiza ese producto) |
| Más del X% de productos con variación grande | DETENER (probable cambio de columna/moneda/IVA) |
| Códigos duplicados | ADVERTENCIA |
| Precio en cero | ADVERTENCIA (no se actualiza ese producto) |
| Stock negativo | ADVERTENCIA |
| Cantidad de registros anormal (> X% de lo habitual) | ADVERTENCIA |

"Lo habitual" = promedio de las últimas listas aprobadas (sale del histórico).

## 7. Plan de construcción (progresivo)

| Etapa | Qué se construye | Cómo sabemos que funciona |
|---|---|---|
| **1** | Estructura base: config, logs, bloqueo, reintentos, credenciales, agente que recorre proveedores de prueba | `python agent.py` muestra 1 OK y 1 ERROR, con log y duración |
| **2** | Primer proveedor real (Dimac): descarga → lectura → normalización → comparación → histórico → reporte | Aparece la lista en `descargas/`, el normalizado en `procesados/` y el reporte HTML |
| **3** | ComercioCity: login, backup, importación, lectura de errores, verificación — primero en modo simulación | Se genera el archivo de importación; con simulación apagada, el reporte muestra filas aceptadas/rechazadas |
| **4** | Validaciones completas y alertas | Una lista "rota" a propósito queda bloqueada |
| **5** | 2 → 5 → 10 → 30 proveedores | Cada alta = una carpeta nueva |
| **6** | Programador de tareas de Windows (10:00) | Corre solo y deja el reporte |
