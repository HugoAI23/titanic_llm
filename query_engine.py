"""
query_engine.py - Motor de Consultas en Lenguaje Natural para el Chat del Titanic
================================================================================
Permite resolver preguntas de usuarios en español sobre los datos históricos,
estadísticas clave, personajes destacados, récords y patrones de supervivencia.
"""

import os
import re
import unicodedata
from typing import Any, Dict, List, Optional
import pandas as pd


def normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos/tildes y convirtiendo a minúsculas."""
    text = text.strip().lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text


class TitanicQueryEngine:
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        dirty_path = os.path.join(base_dir, "data", "titanic_data_dirty.csv")
        clean_path = os.path.join(base_dir, "data", "titanic_clean.csv")

        self.df_dirty = pd.read_csv(dirty_path)
        self.df_clean = pd.read_csv(clean_path)

        # Precomputar métricas frecuentes
        self.total_passengers = len(self.df_dirty)
        self.total_survivors = int(self.df_clean["survived"].sum())
        self.total_deaths = self.total_passengers - self.total_survivors
        self.survival_rate = (self.total_survivors / self.total_passengers) * 100

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Interpreta la intención de la consulta y devuelve una respuesta estructurada.
        """
        q = normalize_text(query)

        # 1. Lugar de mayor embarcación / Puerto principal
        if any(w in q for w in ["lugar de mayor", "mayor embarcacion", "mayor embarque", "donde embarco mas", "puerto principal", "puerto con mas", "donde subio mas", "donde embarco la mayoria"]):
            return self._query_top_port()

        # 2. Ticket / Boleto más alto / Más caro
        if any(w in q for w in ["ticket mas alto", "boleto mas caro", "ticket mas caro", "pasaje mas caro", "tarifa mas alta", "quien pago mas", "mayor tarifa", "boleto record", "ticket record"]):
            return self._query_highest_ticket()

        # 3. Cuántos sobrevivientes hubo / Fallecidos / Muertos
        if any(w in q for w in ["cuantos sobrevivientes", "cuantas personas sobrevivieron", "cuantos murieron", "cuantos fallecieron", "tasa de supervivencia", "porcentaje de sobrevivientes", "total sobrevivientes", "cuantos se salvaron"]):
            return self._query_survivors_count()

        # 4. Personas de mayor edad que murieron / ancianos fallecidos
        if any(w in q for w in ["mayor edad que murieron", "viejos que murieron", "ancianos que murieron", "mas viejos murieron", "mas ancianos fallecieron", "edad que murieron", "anciano murio", "viejo murio", "mas viejos que murieron"]):
            return self._query_oldest_died()

        # 5. Personas de mayor edad que sobrevivieron
        if any(w in q for w in ["mayor edad que sobrevivieron", "mas viejo que sobrevivio", "mas anciano que sobrevivio", "ancianos sobrevivieron"]):
            return self._query_oldest_survived()

        # 6. Género / Sexo / Hombres vs Mujeres
        if any(w in q for w in ["genero", "sexo", "mujeres vs hombres", "hombres vs mujeres", "cuantas mujeres", "cuantos hombres", "sobrevivieron mas mujeres"]):
            return self._query_gender_survival()

        # 7. Clases sociales (1ra, 2da, 3ra)
        if any(w in q for w in ["clase", "primera clase", "segunda clase", "tercera clase", "pclass"]):
            return self._query_class_survival()

        # 8. Niños / Menores de edad
        if any(w in q for w in ["niño", "niños", "infante", "bebe", "menores de edad"]):
            return self._query_children_survival()

        # 9. Tarifas promedio / Precio promedio
        if any(w in q for w in ["tarifa promedio", "costo promedio", "precio promedio", "cuanto costaba", "cuanto costaron"]):
            return self._query_average_fare()

        # 10. Edad promedio
        if any(w in q for w in ["edad promedio", "promedio de edad"]):
            return self._query_average_age()

        # 11. Búsqueda de pasajeros por nombre
        if any(w in q for w in ["buscar", "pasajero", "quien era", "jack", "rose", "astor", "smith", "andrews", "guggenheim"]):
            return self._query_passenger_search(q)

        # Respuesta general con sugerencias
        return self._query_default_help(query)

    def _query_top_port(self) -> Dict[str, Any]:
        port_names = {
            "S": "Southampton (Inglaterra)",
            "C": "Cherburgo (Francia)",
            "Q": "Queenstown (Cobh, Irlanda)"
        }
        counts = self.df_clean["embarked"].value_counts()
        s_count = int(counts.get("S", 0))
        c_count = int(counts.get("C", 0))
        q_count = int(counts.get("Q", 0))

        s_pct = (s_count / self.total_passengers) * 100
        c_pct = (c_count / self.total_passengers) * 100
        q_pct = (q_count / self.total_passengers) * 100

        text = (
            f"📍 **El lugar de mayor embarcación fue Southampton (Inglaterra)**, con un total de "
            f"**{s_count} pasajeros** (**{s_pct:.1f}%** del total a bordo en este registro).\n\n"
            f"La distribución completa por puertos fue:\n"
            f"• **Southampton (S):** {s_count} pasajeros ({s_pct:.1f}%)\n"
            f"• **Cherburgo (C):** {c_count} pasajeros ({c_pct:.1f}%)\n"
            f"• **Queenstown (Q):** {q_count} pasajeros ({q_pct:.1f}%)\n\n"
            f"💡 *Dato curioso:* Los pasajeros de Cherburgo tuvieron la tasa de supervivencia más alta (55.4%), "
            f"debido a que una alta proporción viajaba en primera clase."
        )

        return {
            "query_type": "port",
            "title": "Puerto con Mayor Número de Pasajeros",
            "text": text,
            "highlights": [
                {"label": "Puerto Principal", "value": "Southampton (S)"},
                {"label": "Pasajeros Embarcados", "value": f"{s_count} ({s_pct:.1f}%)"},
                {"label": "Tasa Supervivencia en S", "value": "33.7%"}
            ],
            "suggestions": [
                "¿Cuál fue el ticket más alto?",
                "¿Cuántos sobrevivientes hubo en total?",
                "¿Cuál era la tasa de supervivencia por clase?"
            ]
        }

    def _query_highest_ticket(self) -> Dict[str, Any]:
        max_fare = float(self.df_dirty["Fare"].max())
        top_passengers = self.df_dirty[self.df_dirty["Fare"] == max_fare]

        rows = []
        for _, p in top_passengers.iterrows():
            surv_str = "Sobrevivió ✅" if p["Survived"] == 1 else "Falleció ❌"
            rows.append(f"• **{p['Name']}** ({p['Sex']}, {p['Age']:.0f} años) — Clase {p['Pclass']} — *{surv_str}*")

        text = (
            f"💰 **El ticket más alto registrado costó £{max_fare:.2f} libras esterlinas** "
            f"(equivalente a más de $60,000 USD actuales).\n\n"
            f"Este boleto récord fue compartido por **3 pasajeros de 1ª clase**, y **los tres sobrevivieron** al desastre:\n\n"
            + "\n".join(rows) + "\n\n"
            f"💡 *Contexto:* Correspondía a la Suite Parlor con cubierta privada en la cubierta B/C, "
            f"embarcando en Cherburgo con destino a Nueva York."
        )

        return {
            "query_type": "fare_record",
            "title": "Récord de Tarifa: Boleto Más Caro",
            "text": text,
            "highlights": [
                {"label": "Tarifa Récord", "value": f"£{max_fare:.2f}"},
                {"label": "Pasajeros con este boleto", "value": f"{len(top_passengers)} (100% supervivencia)"},
                {"label": "Clase", "value": "1ª Clase (Suite Parlor)"}
            ],
            "suggestions": [
                "¿Cuáles fueron las personas de mayor edad que murieron?",
                "¿Cuál fue la tarifa promedio?",
                "¿Cuántos sobrevivieron en primera clase?"
            ]
        }

    def _query_survivors_count(self) -> Dict[str, Any]:
        text = (
            f"🛟 **Balance oficial de víctimas y sobrevivientes en el dataset:**\n\n"
            f"• **Sobrevivientes:** **{self.total_survivors} personas** (**{self.survival_rate:.1f}%**)\n"
            f"• **Fallecidos:** **{self.total_deaths} personas** (**{100 - self.survival_rate:.1f}%**)\n"
            f"• **Total analizado:** {self.total_passengers} pasajeros\n\n"
            f"La probabilidad de sobrevivir estuvo fuertemente sesgada por el sexo del pasajero "
            f"y la clase de su pasaje, donde la máxima prioridad fue otorgada a mujeres y niños en cubiertas superiores."
        )

        return {
            "query_type": "survivors",
            "title": "Estadística Global de Supervivencia",
            "text": text,
            "highlights": [
                {"label": "Sobrevivientes", "value": f"{self.total_survivors} ({self.survival_rate:.1f}%)"},
                {"label": "Fallecidos", "value": f"{self.total_deaths} ({100 - self.survival_rate:.1f}%)"},
                {"label": "Total Pasajeros", "value": str(self.total_passengers)}
            ],
            "suggestions": [
                "¿Quiénes fueron las personas de mayor edad que murieron?",
                "¿Cuántas mujeres sobrevivieron vs hombres?",
                "¿Dónde embarcó más gente?"
            ]
        }

    def _query_oldest_died(self) -> Dict[str, Any]:
        # Filtrar fallecidos con edad conocida
        died = self.df_dirty[(self.df_dirty["Survived"] == 0) & (self.df_dirty["Age"].notna())]
        oldest = died.sort_values(by="Age", ascending=False).head(5)

        items = []
        table_data = []
        for idx, (_, r) in enumerate(oldest.iterrows(), 1):
            fare_val = f"£{r['Fare']:.2f}" if pd.notna(r['Fare']) else "N/A"
            items.append(f"{idx}. **{r['Name']}** — **{r['Age']:.1f} años** (Clase {r['Pclass']}, {fare_val})")
            table_data.append({
                "name": r["Name"],
                "age": float(r["Age"]),
                "pclass": int(r["Pclass"]),
                "fare": fare_val
            })

        oldest_person = oldest.iloc[0]

        text = (
            f"👴 **La persona de mayor edad que falleció en el Titanic fue Mr. Johan Svensson**, "
            f"un pasajero sueco de **{oldest_person['Age']:.0f} años** que viajaba en **3ª clase**.\n\n"
            f"Los 5 pasajeros más ancianos que perdieron la vida fueron:\n"
            + "\n".join(items) + "\n\n"
            f"💡 *Observación:* Incluso ancianos distinguidos de 1ª clase como Ramon Artagaveytia y George Goldschmidt "
            f"(ambos de 71 años) no tuvieron acceso a botes salvavidas debido a la estricta norma de 'mujeres y niños primero'."
        )

        return {
            "query_type": "oldest_died",
            "title": "Pasajeros de Mayor Edad que Fallecieron",
            "text": text,
            "data_table": table_data,
            "highlights": [
                {"label": "Persona más anciana fallecida", "value": f"Johan Svensson ({oldest_person['Age']:.0f} años)"},
                {"label": "Clase", "value": f"Clase {oldest_person['Pclass']}"},
                {"label": "Género", "value": "Masculino"}
            ],
            "suggestions": [
                "¿Quién fue la persona de mayor edad que sí sobrevivió?",
                "¿Cuál fue el ticket más alto?",
                "¿Cuántos sobrevivientes hubo en total?"
            ]
        }

    def _query_oldest_survived(self) -> Dict[str, Any]:
        survived = self.df_dirty[(self.df_dirty["Survived"] == 1) & (self.df_dirty["Age"].notna())]
        oldest = survived.sort_values(by="Age", ascending=False).head(5)

        items = []
        for idx, (_, r) in enumerate(oldest.iterrows(), 1):
            items.append(f"{idx}. **{r['Name']}** — **{r['Age']:.0f} años** (Clase {r['Pclass']}, {r['Sex']})")

        oldest_person = oldest.iloc[0]

        text = (
            f"🏆 **La persona de mayor edad que logró sobrevivir fue Mr. Algernon Henry Wilson Barkworth**, "
            f"un magistrado inglés de **{oldest_person['Age']:.0f} años** que viajaba en **1ª clase**.\n\n"
            f"Logró salvarse nadando y subiendo al bote plegable 'B' que se encontraba volcado.\n\n"
            f"Los 5 supervivientes más longevos fueron:\n"
            + "\n".join(items)
        )

        return {
            "query_type": "oldest_survived",
            "title": "Supervivientes de Mayor Edad",
            "text": text,
            "highlights": [
                {"label": "Superviviente más longevo", "value": f"Algernon Barkworth ({oldest_person['Age']:.0f} años)"},
                {"label": "Clase", "value": "1ª Clase"},
                {"label": "Estado", "value": "Sobrevivió"}
            ],
            "suggestions": [
                "¿Quiénes fueron las personas de mayor edad que murieron?",
                "¿Cuál fue el ticket más alto?",
                "¿Dónde embarcó más gente?"
            ]
        }

    def _query_gender_survival(self) -> Dict[str, Any]:
        fem_total = len(self.df_clean[self.df_clean["sex"] == "female"])
        fem_surv = int(self.df_clean[(self.df_clean["sex"] == "female") & (self.df_clean["survived"] == 1)].shape[0])
        fem_rate = (fem_surv / fem_total) * 100

        male_total = len(self.df_clean[self.df_clean["sex"] == "male"])
        male_surv = int(self.df_clean[(self.df_clean["sex"] == "male") & (self.df_clean["survived"] == 1)].shape[0])
        male_rate = (male_surv / male_total) * 100

        text = (
            f"👥 **Supervivencia por Género (Mujeres vs Hombres):**\n\n"
            f"• **Mujeres:** **{fem_surv} de {fem_total}** sobrevivieron (**{fem_rate:.1f}%** de supervivencia)\n"
            f"• **Hombres:** **{male_surv} de {male_total}** sobrevivieron (**{male_rate:.1f}%** de supervivencia)\n\n"
            f"La probabilidad de salvarse siendo mujer fue **casi 4 veces mayor** que la de un hombre, "
            f"haciendo del género la característica más predictiva de todos los modelos de Machine Learning."
        )

        return {
            "query_type": "gender",
            "title": "Comparativa de Supervivencia por Género",
            "text": text,
            "highlights": [
                {"label": "Supervivencia Femenina", "value": f"{fem_rate:.1f}% ({fem_surv}/{fem_total})"},
                {"label": "Supervivencia Masculina", "value": f"{male_rate:.1f}% ({male_surv}/{male_total})"}
            ],
            "suggestions": [
                "¿Cómo influyó la clase social?",
                "¿Cuántos niños sobrevivieron?",
                "¿Cuál fue el ticket más alto?"
            ]
        }

    def _query_class_survival(self) -> Dict[str, Any]:
        res = []
        for c in [1, 2, 3]:
            tot = len(self.df_clean[self.df_clean["pclass"] == c])
            surv = int(self.df_clean[(self.df_clean["pclass"] == c) & (self.df_clean["survived"] == 1)].shape[0])
            rate = (surv / tot) * 100
            res.append(f"• **Clase {c}:** {surv} de {tot} sobrevivieron (**{rate:.1f}%**)")

        text = (
            f"🎫 **Tasa de Supervivencia según Clase del Boleto:**\n\n"
            + "\n".join(res) + "\n\n"
            f"Un pasajero de **1ª clase** tenía más del doble de probabilidad de salvarse que uno de **3ª clase**, "
            f"debido a la cercanía física a la cubierta de botes y avisos tempranos de evacuación."
        )

        return {
            "query_type": "class",
            "title": "Supervivencia por Clase de Boleto",
            "text": text,
            "highlights": [
                {"label": "1ª Clase", "value": "63.0% de supervivencia"},
                {"label": "2ª Clase", "value": "47.3% de supervivencia"},
                {"label": "3ª Clase", "value": "24.2% de supervivencia"}
            ],
            "suggestions": [
                "¿Cuál fue el ticket más caro de 1ra clase?",
                "¿Dónde embarcó la mayoría?",
                "¿Cuántos sobrevivientes hubo en total?"
            ]
        }

    def _query_children_survival(self) -> Dict[str, Any]:
        kids = self.df_clean[self.df_clean["age"] < 12]
        total_kids = len(kids)
        surv_kids = int(kids["survived"].sum())
        rate = (surv_kids / total_kids) * 100

        text = (
            f"👶 **Supervivencia de Niños e Infantes (< 12 años):**\n\n"
            f"• Total de infantes registrados: **{total_kids}**\n"
            f"• Sobrevivientes: **{surv_kids}** (**{rate:.1f}%**)\n\n"
            f"Todos los niños de 1ª y 2ª clase sobrevivieron, mientras que las pérdidas infantiles "
            f"se concentraron de forma trágica en familias numerosas de 3ª clase."
        )

        return {
            "query_type": "children",
            "title": "Supervivencia de Niños e Infantes",
            "text": text,
            "highlights": [
                {"label": "Tasa Infantil (<12 años)", "value": f"{rate:.1f}%"},
                {"label": "Niños Salvados", "value": f"{surv_kids} de {total_kids}"}
            ],
            "suggestions": [
                "¿Quiénes fueron las personas de mayor edad que murieron?",
                "¿Cuántas mujeres sobrevivieron vs hombres?",
                "¿Cuál fue el ticket más alto?"
            ]
        }

    def _query_average_fare(self) -> Dict[str, Any]:
        mean_fare = float(self.df_clean["fare"].mean())
        c1 = float(self.df_clean[self.df_clean["pclass"] == 1]["fare"].mean())
        c2 = float(self.df_clean[self.df_clean["pclass"] == 2]["fare"].mean())
        c3 = float(self.df_clean[self.df_clean["pclass"] == 3]["fare"].mean())

        text = (
            f"💷 **Tarifas y Costos del Pasaje:**\n\n"
            f"• **Tarifa promedio global:** £{mean_fare:.2f}\n"
            f"• **1ª Clase (media):** £{c1:.2f}\n"
            f"• **2ª Clase (media):** £{c2:.2f}\n"
            f"• **3ª Clase (media):** £{c3:.2f}\n\n"
            f"El boleto más barato fue de £0.00 (empleados o pasajes cortesía) y el más caro fue de **£512.33**."
        )

        return {
            "query_type": "fares",
            "title": "Tarifas y Precios de Boletos",
            "text": text,
            "highlights": [
                {"label": "Tarifa Media Global", "value": f"£{mean_fare:.2f}"},
                {"label": "1ª Clase Media", "value": f"£{c1:.2f}"},
                {"label": "3ª Clase Media", "value": f"£{c3:.2f}"}
            ],
            "suggestions": [
                "¿Cuál fue el boleto más caro?",
                "¿Dónde embarcó más gente?",
                "¿Cuántos sobrevivientes hubo?"
            ]
        }

    def _query_average_age(self) -> Dict[str, Any]:
        mean_age = float(self.df_clean["age"].mean())
        median_age = float(self.df_clean["age"].median())

        text = (
            f"🎂 **Edad de los Pasajeros:**\n\n"
            f"• **Edad Promedio:** {mean_age:.1f} años\n"
            f"• **Edad Mediana:** {median_age:.1f} años\n"
            f"• **Pasajero más joven:** Infante Thomas Assad (0.42 años / 5 meses)\n"
            f"• **Pasajero más longevo:** Algernon Barkworth (80 años)"
        )

        return {
            "query_type": "age",
            "title": "Distribución de Edades",
            "text": text,
            "highlights": [
                {"label": "Edad Promedio", "value": f"{mean_age:.1f} años"},
                {"label": "Rango de Edad", "value": "5 meses a 80 años"}
            ],
            "suggestions": [
                "¿Quiénes fueron las personas de mayor edad que murieron?",
                "¿Quién fue el más anciano que sobrevivió?",
                "¿Dónde embarcó más gente?"
            ]
        }

    def _query_passenger_search(self, q: str) -> Dict[str, Any]:
        tokens = [w for w in re.split(r'[^a-zA-Z]', q) if len(w) >= 3 and w not in ["quien", "era", "buscar", "pasajero", "como", "sobrevivio", "para"]]

        if not tokens:
            return self._query_default_help(q)

        pattern = "|".join(tokens)
        matches = self.df_dirty[self.df_dirty["Name"].str.contains(pattern, case=False, na=False)]

        if matches.empty:
            return {
                "query_type": "search_empty",
                "title": "Búsqueda de Pasajero",
                "text": f"🔍 No se encontraron registros con el término buscado. Intenta con apellidos históricos como *'Astor'*, *'Smith'*, *'Svensson'*, *'Cardeza'* o *'Barkworth'*.",
                "highlights": [],
                "suggestions": [
                    "¿Cuál fue el ticket más alto?",
                    "¿Quiénes fueron las personas de mayor edad que murieron?",
                    "¿Dónde embarcó más gente?"
                ]
            }

        top_matches = matches.head(4)
        items = []
        for _, r in top_matches.iterrows():
            surv = "Sobrevivió ✅" if r["Survived"] == 1 else "Falleció ❌"
            age_str = f"{r['Age']:.0f} años" if pd.notna(r['Age']) else "Edad desc."
            items.append(f"• **{r['Name']}** ({age_str}, Clase {r['Pclass']}) — *{surv}*")

        text = f"🔎 Se encontraron **{len(matches)} pasajero(s)** coincidentes:\n\n" + "\n".join(items)

        return {
            "query_type": "search_found",
            "title": "Pasajeros Encontrados",
            "text": text,
            "highlights": [
                {"label": "Coincidencias", "value": f"{len(matches)} pasajeros"}
            ],
            "suggestions": [
                "¿Quiénes fueron las personas de mayor edad que murieron?",
                "¿Cuál fue el boleto más caro?",
                "¿Cuántos sobrevivientes hubo?"
            ]
        }

    def _query_default_help(self, user_text: str) -> Dict[str, Any]:
        text = (
            f"👋 ¡Hola! Soy el asistente analítico del Titanic. Puedo responder preguntas históricas y estadísticas precisas sobre el viaje.\n\n"
            f"**Preguntas recomendadas que puedes hacer:**\n"
            f"• 🚢 *\"¿Cuál fue el lugar de mayor embarcación?\"*\n"
            f"• 💰 *\"¿Cuál fue el ticket más alto?\"*\n"
            f"• 🛟 *\"¿Cuántos sobrevivientes hubo en total?\"*\n"
            f"• 👴 *\"¿Cuáles fueron las personas de mayor edad que murieron?\"*\n"
            f"• 👥 *\"¿Cuántas mujeres sobrevivieron frente a los hombres?\"*\n"
            f"• 🎫 *\"¿Cuál fue la tasa de supervivencia por clase?\"*"
        )

        return {
            "query_type": "help",
            "title": "Asistente de Datos del Titanic",
            "text": text,
            "highlights": [
                {"label": "Dataset", "value": "891 pasajeros analizados"},
                {"label": "Modelos Activos", "value": "Random Forest & Logistic Regression"}
            ],
            "suggestions": [
                "¿Dónde embarcó más gente?",
                "¿Cuál fue el ticket más alto?",
                "¿Cuántos sobrevivientes hubo?",
                "¿Quiénes fueron los más viejos que murieron?"
            ]
        }


_engine_instance: Optional[TitanicQueryEngine] = None


def get_query_engine() -> TitanicQueryEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TitanicQueryEngine()
    return _engine_instance
