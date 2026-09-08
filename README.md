# 🚢 Titanic ML: Producción, Dashboard & Asistente Conversacional

Plataforma interactiva para la exploración, inferencia y análisis de los datos y modelos del Titanic. Incluye una API REST construida con Flask, un pipeline de inferencia optimizado para usuarios finales, una interfaz de usuario moderna diseñada con **Tailwind CSS**, animaciones con **Anime.js**, estética visual inspirada en **Bklit UI**, un dashboard de métricas históricas y un asistente conversacional de consultas en lenguaje natural.

---

## 🌟 Características Principales

1. **Pipeline de Producción Simplificado (`pipeline.py`)**:
   - Abstrae toda la complejidad técnica (escalado con `StandardScaler`, transformación `log1p` en tarifas, y codificación con `OneHotEncoder`).
   - Entrada amigable: edad, género, clase, acompañantes, tarifa y puerto.
   - Deducción inteligente de títulos sociales (`Mr`, `Mrs`, `Miss`, `Master`, `Otro`) a partir del nombre o de la edad/género.
   - Cálculo automático del tamaño familiar (`familiares = sibsp + parch`).
   - Explicabilidad instantánea con factores clave de riesgo o beneficio.
   - Selección de modelo: **Random Forest** (82.1% Accuracy), **Regresión Logística** (80.4% Accuracy) o **Comparación Simultánea**.

2. **Dashboard de Insights Analíticos (`dashboard_service.py`)**:
   - KPIs globales en tiempo real (Pasajeros, Sobrevivientes, Víctimas, Boleto Récord, Puerto Mayoritario).
   - Tasa de supervivencia por género (Mujeres 74.2% vs Hombres 18.9%).
   - Tasa de supervivencia por clase social (1ª: 63.0%, 2ª: 47.3%, 3ª: 24.2%).
   - Distribución de pasaje por puerto de embarque (Southampton 72.5%, Cherburgo 18.9%, Queenstown 8.6%).
   - Impacto del tamaño familiar (viajar solo vs familia pequeña vs familia numerosa).
   - Tabla interactiva de los pasajeros de mayor edad que murieron (encabezada por Johan Svensson, 74 años).
   - Tabla de los boletos récord más caros (£512.33 en Suite Parlor).

3. **Asistente Conversacional / Chat de Consultas (`query_engine.py`)**:
   - Procesamiento de lenguaje natural tolerante a tildes, mayúsculas y variantes lingüísticas.
   - Respuestas con formato enriquecido, cifras destacadas y chips de sugerencias dinámicas.
   - Preguntas clave soportadas:
     - *"¿Cuál fue el lugar de mayor embarcación?"*
     - *"¿Cuál fue el ticket más alto?"*
     - *"¿Cuántos sobrevivientes hubo en total?"*
     - *"¿Cuáles fueron las personas de mayor edad que murieron?"*
     - *"¿Supervivencia de mujeres frente a hombres?"*
     - *"¿Cuántos niños sobrevivieron?"*
     - Búsqueda directa de pasajeros por apellido o nombre.

4. **Frontend Moderno (Tailwind CSS + Anime.js + Bklit UI Style)**:
   - Single Page Application (SPA) con navegación por pestañas fluidas.
   - Sliders interactivos con recálculo en tiempo real o manual.
   - Presets arquetípicos listos para probar (Rose DeWitt, Jack Dawson, Niño de 2ª clase, Caballero de 1ª clase, Familia numerosa).
   - Animaciones continuas de porcentajes y barras de probabilidad con **Anime.js**.

---

## 🚀 Cómo Ejecutar la Aplicación

### 1. Activar el entorno virtual o instalar dependencias
El entorno `.llm` ya cuenta con todas las dependencias necesarias. Si deseas instalarlo en un entorno nuevo:
```bash
pip install -r requirements-dev.txt
```

### 2. Iniciar el servidor Flask
```bash
./.llm/bin/python app.py
```
El servidor arrancará en:
```
http://127.0.0.1:5000
```
Abre esa URL en tu navegador preferido (Chrome, Safari, Edge, Firefox).

---

## 📡 API REST Endpoints

### `POST /api/predict`
Realiza la predicción de supervivencia para un pasajero.

**Payload de ejemplo:**
```json
{
  "sex": "female",
  "pclass": 1,
  "age": 25.0,
  "fare": 80.0,
  "embarked": "C",
  "sibsp": 0,
  "parch": 1,
  "model_type": "rf"
}
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "primary": {
      "model": "Random Forest",
      "survived": true,
      "survival_label": "Sobrevive",
      "probability_survival": 94.2,
      "probability_death": 5.8,
      "confidence": "Alta"
    },
    "factors": [
      {
        "factor": "Género Femenino",
        "impact": "positive",
        "text": "La prioridad de evacuación 'mujeres y niños primero' otorga alta probabilidad (+)."
      }
    ]
  }
}
```

### `POST /api/chat`
Procesa una pregunta en lenguaje natural.

**Payload de ejemplo:**
```json
{
  "query": "¿Cuál fue el ticket más alto?"
}
```

### `GET /api/dashboard`
Retorna todas las métricas, KPIs y tablas analíticas del dataset precalculadas para visualización.

### `GET /api/health`
Verifica el estado del servicio y la carga de los modelos entrenados.

---

## 🧪 Pruebas Automatizadas

Para ejecutar la suite de pruebas unitarias y de integración:
```bash
./.llm/bin/python -m pytest tests/ -v
```
Todas las 13 pruebas validan la lógica de predicción, el motor de consultas, la agregación del dashboard y las rutas de Flask.
