from fastapi import FastAPI, HTTPException  # Importa FastAPI para crear la API y HTTPException para manejar errores HTTP
from pydantic import BaseModel  # Define un modelo de datos para validar y documentar la API
from typing import Dict  # Tipo de dato para definir que se devolverá un diccionario
import requests  # Librería para realizar solicitudes HTTP
from bs4 import BeautifulSoup  # Librería para parsear HTML
import ssl  # Módulo para manejar SSL
from requests.adapters import HTTPAdapter  # Adaptador para personalizar las conexiones HTTP
from requests.packages.urllib3.poolmanager import PoolManager  # Necesario para sobreescribir SSL
import re  # Librería para usar expresiones regulares

app = FastAPI()  # Instancia de FastAPI para definir los endpoints

BESTIARY_URL = "https://clayadavis.gitlab.io/osr-bestiary/bestiary/bfrpg/field-guide-1/"  # URL base del bestiario

class Enemy(BaseModel):
    # Clase que define el modelo del enemigo a devolver
    nombre: str
    armor_class: int
    hit_dice: str
    number_of_attacks: str
    damage: str
    movement: str
    number_of_appearing: str
    save_as: str
    morale: int
    treasure_type: str
    xp: int
    descripcion: str

class SSLAdapter(HTTPAdapter):
    # Adaptador para permitir conexiones SSL personalizadas
    def __init__(self, *args, **kwargs):
        self.context = ssl.create_default_context()
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # Configura el uso de SSL
        kwargs['ssl_context'] = self.context
        return super().init_poolmanager(*args, **kwargs)


def obtener_estadisticas(nombre: str) -> Dict:
    try:
        # Limpia el nombre para que sea compatible con URL
        nombre_url = re.sub(r'[^a-zA-Z0-9\- ]', '', nombre).lower().replace(' ', '-')
        url = f"{BESTIARY_URL}{nombre_url}.html"

        # Inicia la sesión con un adaptador SSL para permitir conexiones HTTPS
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        response = session.get(url)

        if response.status_code != 200:
            # Error si no encuentra la página del monstruo
            raise HTTPException(status_code=404, detail=f"Enemigo '{nombre}' no encontrado en el bestiario. URL: {url}")

        # Convierte la respuesta en un árbol de elementos HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Extrae la tabla de estadísticas del HTML
        stats_table = soup.find("table")
        stats = {}
        if stats_table:
            rows = stats_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) == 2:
                    # Procesa cada fila de la tabla, asigna clave-valor
                    key = cells[0].get_text(strip=True).lower().replace(' ', '_').replace('.', '').replace(':', '')
                    value = cells[1].get_text(strip=True)
                    stats[key] = value

        # Extrae la descripción del monstruo
        descripcion = ''
        try:
            descripcion_p = soup.find("div", class_="e-content entry-content").find_all("p")[-1]
            if descripcion_p:
                descripcion = descripcion_p.get_text(strip=True)
        except:
            descripcion = 'Descripción no disponible.'

        # Devuelve la información recopilada en un diccionario
        enemigo = {
            "nombre": nombre,
            "armor_class": int(stats.get('armor_class', '0')),  
            "hit_dice": stats.get('hit_dice', 'Unknown'),
            "number_of_attacks": stats.get('no_of_attacks', 'Unknown'),
            "damage": stats.get('damage', 'Unknown'),
            "movement": stats.get('movement', 'Unknown'),
            "number_of_appearing": stats.get('no_appearing', 'Unknown'),
            "save_as": stats.get('save_as', 'Unknown'),
            "morale": int(stats.get('morale', '0')),  
            "treasure_type": stats.get('treasure_type', 'Unknown'),
            "xp": int(stats.get('xp', '0')),  
            "descripcion": descripcion
        }

        return enemigo

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # Error si ocurre cualquier otro problema

@app.get("/")
def read_root():
    return {"message": "API is funcionando correctamente"}
    
@app.post("/consultar-enemigo/")
def consultar_enemigo(nombre: str):
    # Endpoint para consultar la información del enemigo
    enemigo = obtener_estadisticas(nombre)
    return {"enemigo": enemigo}  # Devuelve la información en formato JSON
