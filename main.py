from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

conn = psycopg2.connect(
    host="localhost",
    database="auto_helper",
    user="postgres",
    password="1234"
)

@app.get("/code/{code}")
def get_error(code: str):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT code, description, danger_level, specific_advice FROM error_codes WHERE code = %s",
        [code]
    )
    result = cursor.fetchone()
    cursor.close()
    
    if result is None:
        return {"error": f"Код {code} не найден в базе"}
    
    return result