# Guía del agente

Cómo usar el modelo de probabilidad de victoria desde Claude Desktop o Claude Code. La arquitectura está en `docx/03Evidencia/07-11-26_ArquitecturaDelAgente.md`.

---

## 1. Requisitos

| Requisito | Para qué |
|---|---|
| Python 3.11 o superior | Correr el servidor MCP y el modelo |
| Dependencias de `requirements.txt` | Incluyen `scikit-learn==1.7.2` (la versión del modelo), `shap` y `mcp` |
| Token de Kaggle con acceso al dataset del equipo | Bajar el modelo final una sola vez |
| Claude Desktop o Claude Code con la membresía del equipo | Usar el agente |

Antes de la primera instalación, alguien del equipo debe haber ejecutado en Colab las partes 1 y 2 de `notebooks/07_agente.ipynb`, que publican `agente/dominio.json` y los ejemplos en Kaggle.

---

## 2. Instalación (una vez)

Desde la raíz del repositorio.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m ptcg_agente.artefactos
```

**Linux o macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m ptcg_agente.artefactos
```

El último comando baja a `artefactos_agente/` el modelo final, su ficha, el perfil del dominio, las métricas de prueba, el veredicto y las repeticiones de ejemplo, y verifica el SHA-256 de cada archivo. El token se lee de la variable `KAGGLE_API_TOKEN` o de `secrets.txt` en la raíz del repositorio (mismo formato de los cuadernos); si no está, se pide sin mostrarlo.

Resultado esperado: `Listo: 7 archivos verificados en ...` y una línea por ejemplo.

`artefactos_agente/` y `registros/` están en el `.gitignore`.

---

## 3. Claude Code

1. Activa el entorno virtual y abre Claude Code en la raíz del repositorio:
   ```bash
   claude
   ```
2. El archivo `.mcp.json` registra el servidor `ptcg-victoria`. La primera vez, Claude Code pide aprobarlo.
3. Comprueba la conexión con `/mcp`: debe aparecer `ptcg-victoria` conectado con 7 herramientas.

El servidor se lanza con el `python` del entorno activo; por eso hay que activar `.venv` antes de abrir Claude Code.

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
| El servidor no aparece en Claude Code | `.venv` no estaba activo o Claude Code no se abrió en la raíz | Activar `.venv` y abrir `claude` desde la raíz |
| El servidor no aparece en Claude Desktop | Rutas relativas o barras sin escapar en el JSON | Usar rutas absolutas con `\\` en Windows y reiniciar |
| Pruebas | — | `PYTHONPATH=src python -m pytest -q tests/test_agente.py` |