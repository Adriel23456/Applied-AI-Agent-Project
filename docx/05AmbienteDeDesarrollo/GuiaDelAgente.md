# Guía del agente

Cómo usar el modelo de probabilidad de victoria desde Claude Desktop o Claude Code. La arquitectura está en `docx/03Evidencia/07-11-26_ArquitecturaDelAgente.md`.

---

## 1. Requisitos

| Requisito | Para qué |
|---|---|
| **Python 3.12** (la misma versión de Colab) | Correr el servidor MCP y el modelo. Con versiones muy nuevas (3.15) no hay paquetes precompilados de `scikit-learn==1.7.2` y la instalación intenta compilarlo y falla |
| Dependencias de `requirements.txt` | Incluyen `scikit-learn==1.7.2` (la versión del modelo), `shap` y `mcp` |
| Token de Kaggle con acceso al dataset del equipo | Bajar el modelo final una sola vez |
| Claude Code (se instala aparte, sección 3.1) o Claude Desktop, con la membresía del equipo | Usar el agente |

Antes de la primera instalación, alguien del equipo debe haber ejecutado en Colab las partes 1 y 2 de `notebooks/07_agente.ipynb`, que publican `agente/dominio.json` y los ejemplos en Kaggle.

---

## 2. Instalación (una vez)

Desde la raíz del repositorio.

**Windows (PowerShell):** primero confirma que tienes Python 3.12 con `py -0`. Si no aparece, instálalo con `winget install Python.Python.3.12` (o desde python.org) y abre una terminal nueva.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python --version   # debe decir 3.12
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m ptcg_agente.artefactos
```

**Linux o macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m ptcg_agente.artefactos
```

El último comando baja a `artefactos_agente/` el modelo final, su ficha, el perfil del dominio, las métricas de prueba, el veredicto y las repeticiones de ejemplo, y verifica el SHA-256 de cada archivo. El token se lee de la variable `KAGGLE_API_TOKEN` o de `secrets.txt` en la raíz del repositorio (mismo formato de los cuadernos); si no está, se pide sin mostrarlo.

Resultado esperado: `Listo: 7 archivos verificados en ...` y una línea por ejemplo.

`artefactos_agente/` y `registros/` están en el `.gitignore`.

---

## 3. Claude Code

Claude Code es un programa aparte de Claude Desktop y de `requirements.txt`: hay que instalarlo una vez en la PC. Si `claude` responde "is not recognized", es que falta este paso.

**3.1 Instalar Claude Code (una vez)**

Windows (PowerShell, sin permisos de administrador):

```powershell
irm https://claude.ai/install.ps1 | iex
```

Linux o macOS:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Cierra la terminal y abre una nueva (el instalador agrega `claude` al PATH, y solo las terminales nuevas lo ven). Comprueba:

```powershell
claude --version
```

Se recomienda tener Git for Windows instalado; si no está, Claude Code usa PowerShell. No hace falta Node.js. Si algo falla, `claude doctor` muestra un diagnóstico.

**3.2 Abrir Claude Code en el repositorio**

En la terminal nueva, desde la raíz del repositorio, activa el entorno y abre Claude Code:

```powershell
.venv\Scripts\Activate.ps1
claude
```

La primera vez se abre el navegador para iniciar sesión con la cuenta de Claude del equipo (plan Pro o superior). Si no se abre, presiona `c` en la terminal para copiar el enlace.

**3.3 Aprobar y comprobar el servidor**

1. La primera vez aparece el aviso **"New MCP server found in this project: ptcg-victoria"** con tres opciones. Elige la primera, **"Use this MCP server"**, y presiona Enter. Aprueba solo este servidor, que es el del proyecto (`.mcp.json`).
   - No elijas "Use this and all future MCP servers in this project": aprobaría también cualquier servidor que se agregue después al repositorio, sin revisarlo.
   - "Continue without using this MCP server" deja el agente sin herramientas.
2. Escribe `/mcp`: debe aparecer `ptcg-victoria` conectado, con 7 herramientas.
3. Cada vez que Claude llame a una herramienta, Claude Code pide permiso. Revisa el nombre de la herramienta y aprueba. Si eliges permitirla siempre para este proyecto, no vuelve a preguntar por esa herramienta.

Si elegiste mal o quieres revisar la decisión, ejecuta `claude mcp reset-project-choices` en la raíz del repositorio y vuelve a abrir `claude`.

El servidor se lanza con el `python` del entorno activo; por eso hay que activar `.venv` **antes** de escribir `claude`. No hace falta `PYTHONPATH`: el servidor agrega `src/` por su cuenta.

---

## 4. Claude Desktop

1. Abre **Settings → Developer → Edit Config**. Se abre `claude_desktop_config.json`.
2. Agrega el servidor con **rutas absolutas** (ejemplo en Windows; ajusta la ruta del repositorio):
   ```json
   {
     "mcpServers": {
       "ptcg-victoria": {
         "command": "D:\\Ruta\\Applied-AI-Agent-Project\\.venv\\Scripts\\python.exe",
         "args": ["D:\\Ruta\\Applied-AI-Agent-Project\\src\\ptcg_agente\\servidor_mcp.py"]
       }
     }
   }
   ```
   En Linux o macOS: `".../.venv/bin/python"` y `".../src/ptcg_agente/servidor_mcp.py"`.
3. Reinicia Claude Desktop. En el chat, el menú de herramientas debe mostrar `ptcg-victoria`.

---

## 5. Consultas de ejemplo

Los ejemplos están en `artefactos_agente/agente/ejemplos/`. Con Claude Desktop, usa la ruta absoluta del archivo.

- *"Usa ptcg-victoria para analizar `artefactos_agente/agente/ejemplos/partida_XXXX.json`: ¿quién iba ganando en cada turno y cuáles fueron los momentos decisivos?"*
- *"En el paso 60 de esa partida, ¿qué probabilidad tiene el jugador que actúa y por qué?"*
- *"¿Qué tan confiable es el modelo al inicio de la partida? Usa describir_modelo."*
- *"Compara el estado real del paso 60 con el mismo estado pero con el rival sin cartas en el mazo."*

El servidor también ofrece el prompt `consulta_ptcg`, que pide a Claude seguir el flujo completo: planificar, ejecutar, redactar y verificar.

---

## 6. Registros (evidencia)

Cada invocación queda en `registros/agente_AAAA-MM-DD.jsonl`. Para guardar una sesión como evidencia, copia el archivo a `docx/03Evidencia/` con un nombre descriptivo y agrega una captura de la conversación.

---

## 7. Si algo falla

| Síntoma | Causa | Solución |
|---|---|---|
| `no hay manifiesto.json` | No se bajaron los artefactos | Ejecutar `python -m ptcg_agente.artefactos` (sección 2) |
| `el SHA-256 no coincide` | Un archivo local cambió o quedó incompleto | Borrar `artefactos_agente/` y volver a bajarlo |
| `el modelo se guardo con scikit-learn 1.7.2 y hay ...` | Otra versión instalada | `pip install -r requirements.txt` en el entorno del servidor |
| `faltan archivos del agente en Kaggle` | No se ejecutaron las partes 1 y 2 del cuaderno 07 | Ejecutarlas en Colab |
| `/mcp` no muestra `ptcg-victoria` o aparece deshabilitado | Se eligió "Continue without using this MCP server" | `claude mcp reset-project-choices`, volver a abrir `claude` y elegir "Use this MCP server" |
| `claude : The term 'claude' is not recognized` | Claude Code no está instalado, o la terminal se abrió antes de instalarlo | Instalarlo (sección 3.1) y abrir una terminal nueva |
| El servidor no aparece en Claude Code | `.venv` no estaba activo o Claude Code no se abrió en la raíz | Activar `.venv` y abrir `claude` desde la raíz |
| El servidor no aparece en Claude Desktop | Rutas relativas o barras sin escapar en el JSON | Usar rutas absolutas con `\\` en Windows y reiniciar |
| `Failed to build 'scikit-learn'` al instalar | La versión de Python es demasiado nueva y no hay paquete precompilado | Borrar `.venv` y crearlo con Python 3.12 (sección 2) |
| Pruebas | — | `python -m pytest -q tests/test_agente.py` |