"""
pipeline.py - Pipeline de Inferencia en Producción para el Titanic
==================================================================
Permite a cualquier usuario interactuar con los modelos (Random Forest y
Regresión Logística) sin preocuparse por la complejidad de preprocesamiento,
escalado, OneHotEncoding ni ingeniería de variables intermedias.
"""

import os
import re
from typing import Any, Dict, Optional
import joblib
import numpy as np
import pandas as pd

# Mapeo de tarifas típicas (medianas históricas) por clase para rellenado automático
DEFAULT_FARES = {
    1: 60.28,
    2: 14.25,
    3: 8.05
}

TITULOS_VALIDOS = {'Mr', 'Mrs', 'Miss', 'Master', 'Otro'}


class ProductionPipeline:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        rf_path = os.path.join(base_dir, "model_rf.joblib")
        lr_path = os.path.join(base_dir, "model_lr.joblib")

        if not os.path.exists(rf_path):
            raise FileNotFoundError(f"No se encontró el modelo Random Forest en: {rf_path}")
        if not os.path.exists(lr_path):
            raise FileNotFoundError(f"No se encontró el modelo Regresión Logística en: {lr_path}")

        self.model_rf = joblib.load(rf_path)
        self.model_lr = joblib.load(lr_path)

        # Extraer características esperadas
        self.feature_names = list(self.model_rf.feature_names_in_)

    def extract_or_deduce_title(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        sex: str = "male",
        age: float = 30.0,
        sibsp: int = 0,
        parch: int = 0
    ) -> str:
        """
        Deduce de forma inteligente el título social:
        1. Si el usuario seleccionó un título explícito válido, se usa.
        2. Si el usuario ingresó un nombre (ej. 'Mr. John' o 'Miss Elizabeth'), se extrae con regex.
        3. Si no hay nada, se deduce a partir del sexo, edad y familiares.
        """
        if title and title in TITULOS_VALIDOS:
            return title

        if name:
            match = re.search(r' ([A-Za-z]+)\.', name)
            if match:
                extracted = match.group(1)
                if extracted in TITULOS_VALIDOS:
                    return extracted
                return 'Otro'

        # Deducción heurística para usuarios que no ingresen título ni nombre
        if sex == 'female':
            # Si es mayor o viaja con hijos/esposo suele ser Mrs, de lo contrario Miss
            if age >= 25 and (parch > 0 or sibsp > 0):
                return 'Mrs'
            return 'Miss'
        else:
            # En la época, niños varones eran 'Master'
            if age < 14:
                return 'Master'
            return 'Mr'

    def clean_input(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Transforma el input sencillo del usuario en un DataFrame estructurado
        exactamente con las 9 columnas que espera el Pipeline de scikit-learn.
        """
        # 1. Sexo
        raw_sex = str(raw_data.get("sex", "male")).strip().lower()
        sex = "female" if "fem" in raw_sex or raw_sex == "f" or raw_sex == "mujer" else "male"

        # 2. Clase (1, 2, 3)
        try:
            pclass = int(raw_data.get("pclass", 3))
            if pclass not in (1, 2, 3):
                pclass = 3
        except (ValueError, TypeError):
            pclass = 3

        # 3. Edad (0 a 100)
        try:
            age = float(raw_data.get("age", 29.7))
            age = max(0.42, min(90.0, age))
        except (ValueError, TypeError):
            age = 29.7

        # 4. Familiares (sibsp y parch)
        try:
            sibsp = max(0, int(raw_data.get("sibsp", 0)))
        except (ValueError, TypeError):
            sibsp = 0

        try:
            parch = max(0, int(raw_data.get("parch", 0)))
        except (ValueError, TypeError):
            parch = 0

        familiares = sibsp + parch

        # 5. Tarifa (Fare)
        fare = raw_data.get("fare")
        if fare is None or fare == "" or float(fare) < 0:
            fare = DEFAULT_FARES.get(pclass, 15.0)
        else:
            try:
                fare = float(fare)
                fare = max(0.0, min(600.0, fare))
            except (ValueError, TypeError):
                fare = DEFAULT_FARES.get(pclass, 15.0)

        # 6. Puerto de Embarque
        raw_emb = str(raw_data.get("embarked", "S")).strip().upper()
        if "CHER" in raw_emb or raw_emb.startswith("C"):
            embarked = "C"
        elif "QUEEN" in raw_emb or raw_emb.startswith("Q"):
            embarked = "Q"
        else:
            embarked = "S"

        # 7. Título
        raw_title = raw_data.get("titulo")
        raw_name = raw_data.get("name")
        titulo = self.extract_or_deduce_title(
            name=raw_name,
            title=raw_title,
            sex=sex,
            age=age,
            sibsp=sibsp,
            parch=parch
        )

        record = {
            "age": float(age),
            "sibsp": int(sibsp),
            "parch": int(parch),
            "familiares": int(familiares),
            "fare": float(fare),
            "sex": str(sex),
            "embarked": str(embarked),
            "titulo": str(titulo),
            "pclass": int(pclass)
        }

        # Asegurar orden exacto de columnas
        df = pd.DataFrame([record])[self.feature_names]
        return df

    def _get_factors(self, df: pd.DataFrame, proba: float) -> list:
        """
        Genera explicaciones legibles de los factores clave que influyeron
        en la predicción del pasajero.
        """
        factors = []
        sex = df["sex"].iloc[0]
        pclass = df["pclass"].iloc[0]
        age = df["age"].iloc[0]
        fare = df["fare"].iloc[0]
        familiares = df["familiares"].iloc[0]

        # Género
        if sex == "female":
            factors.append({
                "factor": "Género Femenino",
                "impact": "positive",
                "text": "La prioridad de evacuación 'mujeres y niños primero' otorga alta probabilidad (+)."
            })
        else:
            factors.append({
                "factor": "Género Masculino",
                "impact": "negative",
                "text": "Los hombres adultos tuvieron una tasa histórica de mortalidad superior al 80% (-)."
            })

        # Clase social
        if pclass == 1:
            factors.append({
                "factor": "Primera Clase",
                "impact": "positive",
                "text": "Ubicación en cubiertas superiores y acceso preferente a botes (+)."
            })
        elif pclass == 3:
            factors.append({
                "factor": "Tercera Clase",
                "impact": "negative",
                "text": "Ubicación en cubiertas bajas y dificultades de acceso inicial (-)."
            })

        # Edad
        if age < 12:
            factors.append({
                "factor": f"Infante / Niño ({age:.0f} años)",
                "impact": "positive",
                "text": "Prioridad directa de abordaje (+)."
            })
        elif age >= 60:
            factors.append({
                "factor": f"Adulto Mayor ({age:.0f} años)",
                "impact": "negative",
                "text": "Dificultades físicas en la evacuación nocturna (-)."
            })

        # Familia
        if familiares == 0:
            factors.append({
                "factor": "Viajero Solitario",
                "impact": "neutral",
                "text": "Movilidad rápida sin dependientes a cargo."
            })
        elif 1 <= familiares <= 3:
            factors.append({
                "factor": f"Familia Pequeña ({familiares} pers.)",
                "impact": "positive",
                "text": "Apoyo mutuo sin entorpecer el rescate (+)."
            })
        else:
            factors.append({
                "factor": f"Familia Numerosa ({familiares} pers.)",
                "impact": "negative",
                "text": "Retraso crítico intentando reunir a todo el grupo familiar (-)."
            })

        return factors

    def predict(self, raw_data: Dict[str, Any], model_name: str = "rf") -> Dict[str, Any]:
        """
        Ejecuta la inferencia sobre los datos crudos del usuario.
        model_name: 'rf' (Random Forest), 'lr' (Regresión Logística), o 'both'.
        """
        df = self.clean_input(raw_data)

        def _predict_single(model, name: str):
            prediction = int(model.predict(df)[0])
            probas = model.predict_proba(df)[0]
            prob_survive = float(probas[1])
            prob_die = float(probas[0])

            confidence = "Alta" if abs(prob_survive - 0.5) > 0.25 else "Moderada"

            return {
                "model": name,
                "survived": bool(prediction == 1),
                "survival_label": "Sobrevive" if prediction == 1 else "No sobrevive",
                "probability_survival": round(prob_survive * 100, 1),
                "probability_death": round(prob_die * 100, 1),
                "confidence": confidence
            }

        response = {
            "input_processed": df.to_dict(orient="records")[0],
            "factors": []
        }

        if model_name == "both":
            rf_res = _predict_single(self.model_rf, "Random Forest")
            lr_res = _predict_single(self.model_lr, "Regresión Logística")
            response["results"] = {
                "rf": rf_res,
                "lr": lr_res
            }
            response["primary"] = rf_res
            response["factors"] = self._get_factors(df, rf_res["probability_survival"])
        elif model_name == "lr":
            res = _predict_single(self.model_lr, "Regresión Logística")
            response["primary"] = res
            response["factors"] = self._get_factors(df, res["probability_survival"])
        else:
            res = _predict_single(self.model_rf, "Random Forest")
            response["primary"] = res
            response["factors"] = self._get_factors(df, res["probability_survival"])

        return response


_pipeline_instance: Optional[ProductionPipeline] = None


def get_pipeline() -> ProductionPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ProductionPipeline()
    return _pipeline_instance
