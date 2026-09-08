"""
test_api.py - Pruebas automatizadas de la API, Pipeline y Query Engine
======================================================================
"""

import json
import pytest
from app import app
from pipeline import get_pipeline
from query_engine import get_query_engine
from dashboard_service import get_dashboard_service


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestPipeline:
    def test_pipeline_basic_prediction(self):
        p = get_pipeline()
        res = p.predict({
            "sex": "female",
            "pclass": 1,
            "age": 25.0,
            "fare": 80.0
        })
        assert "primary" in res
        assert res["primary"]["survived"] is True
        assert res["primary"]["probability_survival"] > 50.0
        assert len(res["factors"]) > 0

    def test_pipeline_both_models(self):
        p = get_pipeline()
        res = p.predict({
            "sex": "male",
            "pclass": 3,
            "age": 22.0,
            "fare": 7.5
        }, model_name="both")
        assert "results" in res
        assert "rf" in res["results"]
        assert "lr" in res["results"]
        assert res["results"]["rf"]["survived"] is False
        assert res["results"]["lr"]["survived"] is False

    def test_title_deduction_and_family(self):
        p = get_pipeline()
        df = p.clean_input({
            "sex": "male",
            "age": 8,
            "sibsp": 1,
            "parch": 1
        })
        # Un niño varón debe ser deducido como 'Master'
        assert df["titulo"].iloc[0] == "Master"
        assert df["familiares"].iloc[0] == 2


class TestQueryEngine:
    def test_top_port_query(self):
        qe = get_query_engine()
        res = qe.process_query("¿Cuál fue el lugar de mayor embarcación?")
        assert "Southampton" in res["text"]
        assert any("Southampton" in h["value"] for h in res["highlights"])

    def test_highest_ticket_query(self):
        qe = get_query_engine()
        res = qe.process_query("¿Cuál fue el ticket más alto?")
        assert "512.33" in res["text"]
        assert any("512.33" in h["value"] for h in res["highlights"])

    def test_survivors_count_query(self):
        qe = get_query_engine()
        res = qe.process_query("¿Cuántos sobrevivientes hubo?")
        assert "342" in res["text"]
        assert any("342" in h["value"] for h in res["highlights"])

    def test_oldest_died_query(self):
        qe = get_query_engine()
        res = qe.process_query("¿Cuáles fueron las personas de mayor edad que murieron?")
        assert "Johan Svensson" in res["text"]
        assert "74" in res["text"]


class TestDashboardService:
    def test_dashboard_data_structure(self):
        ds = get_dashboard_service()
        data = ds.get_dashboard_data()
        assert "kpis" in data
        assert len(data["kpis"]) == 5
        assert len(data["gender_data"]) == 2
        assert len(data["class_data"]) == 3
        assert len(data["oldest_died"]) == 5
        assert len(data["top_fares"]) == 5
        assert len(data["insights"]) == 4


class TestFlaskEndpoints:
    def test_index_route(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert b"TITANIC" in res.data
        assert b"Simulador" in res.data

    def test_health_route(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "healthy"

    def test_predict_endpoint(self, client):
        payload = {
            "sex": "female",
            "pclass": 1,
            "age": 30,
            "fare": 75,
            "model_type": "rf"
        }
        res = client.post(
            "/api/predict",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert json_data["data"]["primary"]["survived"] is True

    def test_chat_endpoint(self, client):
        payload = {"query": "¿Cuál fue el ticket más alto?"}
        res = client.post(
            "/api/chat",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert "512.33" in json_data["response"]["text"]

    def test_dashboard_endpoint(self, client):
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data["status"] == "success"
        assert "kpis" in json_data["data"]
