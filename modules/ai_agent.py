import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from modules.logger import get_logger

load_dotenv()
log = get_logger("ai_agent")

# Configurazione Google Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash-lite')

class AIAgent:
    def __init__(self):
        self.context = """
        Sei un esperto di analisi sportiva in tempo reale per scommesse su Azuro.
        Il tuo compito è analizzare i dati dei match live, inclusi punteggio, tempo di gioco,
        volume di scommesse (turnover) e andamento delle quote.
        Devi decidere se un esito è "value" (ha valore) rispetto alla probabilità reale.
        Fornisci la tua risposta in formato JSON con i seguenti campi:
        - confidence: (float, 0.0-1.0)
        - outcomeId: (int, l'ID dell'esito consigliato)
        - recommendation: (string, spiegazione tecnica basata sulle stats e l'andamento)
        - risk_level: (string, 'Low', 'Medium', 'High')
        """

    async def analyze_match(self, match_data: dict):
        """
        Analizza un match live usando Gemini.
        match_data deve contenere: {sport, league, teams, conditions, score, etc.}
        """
        prompt = f"""
        {self.context}
        
        Analizza questo match live:
        Sport: {match_data.get('sport')}
        League: {match_data.get('league')}
        Match: {' vs '.join(match_data.get('teams', []))}
        Status/Score: {match_data.get('score', 'N/A')}
        
        Mercati disponibili (Condition ID: {match_data.get('conditionId')}):
        {json.dumps(match_data.get('outcomes', []), indent=2)}
        
        Qual è l'esito più probabile considerando lo stato attuale del match e le quote (odds)?
        Rispondi SOLO in JSON.
        """
        
        try:
            response = model.generate_content(prompt)
            # Pulizia della risposta per estrarre solo il JSON (alcuni modelli includono ```json ... ```)
            text = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(text)
            log.info(f"AI Prediction for {match_data.get('teams')}: {result.get('confidence')} confidence.")
            return result
        except Exception as e:
            log.error(f"Errore analisi Gemini: {e}")
            return {"confidence": 0.0, "outcomeId": None, "recommendation": "Errore AI", "risk_level": "Unknown"}

if __name__ == "__main__":
    # Test veloce
    import asyncio
    agent = AIAgent()
    test_match = {
        "sport": "Football",
        "league": "Premier League",
        "teams": ["Manchester City", "Liverpool"],
        "score": "1-1 (65')",
        "conditionId": "12345",
        "outcomes": [
            {"outcomeId": 1, "name": "Man City", "odds": 2.1},
            {"outcomeId": 2, "name": "Draw", "odds": 3.4},
            {"outcomeId": 3, "name": "Liverpool", "odds": 4.5}
        ]
    }
    async def run_test():
        res = await agent.analyze_match(test_match)
        print(json.dumps(res, indent=2))
    
    asyncio.run(run_test())
