"""
app.py - Servidor Web Flask y API REST para la Aplicación Interactiva del Titanic
================================================================================
Expositor de endpoints REST para:
1. Inferencia del modelo (Predict Pipeline)
2. Asistente conversacional de consultas históricas (Chat Query Engine)
3. Dashboard de estadísticas e insights (Dashboard Service)
4. Renderizado de la SPA en HTML/Tailwind/Anime.js/Bklit UI
"""

import os
from flask import Flask, jsonify, render_template, request
from pipeline import get_pipeline
from query_engine import get_query_engine
from dashboard_service import get_dashboard_service

app = Flask(__name__, template_folder="templates", static_folder="static")

# Inicializar servicios en el arranque
pipeline = get_pipeline()
query_engine = get_query_engine()
dashboard_service = get_dashboard_service()


@app.route("/")
def index():
    """Renderiza la aplicación web unificada (Simulador + Dashboard + Chat)."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Chequeo de salud del servicio y estado de los modelos."""
    return jsonify({
        "status": "healthy",
        "models": {
            "random_forest": "loaded",
            "logistic_regression": "loaded"
        },
        "features": pipeline.feature_names
    })


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Endpoint para realizar predicciones con input simplificado.
    Acepta parámetros como age, sex, pclass, fare, embarked, sibsp, parch, name, model_type.
    """
    try:
        data = request.get_json() or {}
        model_name = data.get("model_type", "rf")  # 'rf', 'lr' o 'both'

        result = pipeline.predict(data, model_name=model_name)
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Endpoint del asistente de consultas en lenguaje natural.
    Responde preguntas sobre sobrevivientes, tickets récords, puertos, etc.
    """
    try:
        data = request.get_json() or {}
        query_text = data.get("query") or data.get("message") or ""

        if not query_text.strip():
            return jsonify({
                "status": "error",
                "message": "La consulta no puede estar vacía."
            }), 400

        result = query_engine.process_query(query_text)
        return jsonify({
            "status": "success",
            "response": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    """
    Endpoint con todos los KPIs, gráficos e insights analíticos del dataset.
    """
    try:
        data = dashboard_service.get_dashboard_data()
        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


def find_available_port(default_port=5001):
    import socket
    # Si el usuario especificó un PORT en las variables de entorno, respetarlo
    if "PORT" in os.environ:
        return int(os.environ["PORT"])
    
    # Probar puertos empezando en 5001 (en macOS el 5000 lo usa AirPlay Receiver)
    for port in [5001, 8080, 8000, 5002]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return default_port


if __name__ == "__main__":
    port = find_available_port()
    print("\n" + "=" * 60)
    print(f"🚢 Servidor Titanic ML activo en:")
    print(f"👉 http://127.0.0.1:{port}")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)
