# Importamos las librerías necesarias
from fastapi import FastAPI, HTTPException, Body  # FastAPI para crear la API, HTTPException para manejar errores, y Body para definir datos del cuerpo en solicitudes POST
from pydantic import BaseModel  # Define un modelo de datos para validar y documentar la API
from typing import Dict, List  # Tipos para definir que se devolverán diccionarios y listas
import requests  # Librería para realizar solicitudes HTTP
from bs4 import BeautifulSoup  # Librería para parsear HTML
import ssl  # Módulo para manejar SSL
from requests.adapters import HTTPAdapter  # Adaptador para personalizar las conexiones HTTP
from requests.packages.urllib3.poolmanager import PoolManager  # Necesario para sobreescribir SSL
import re  # Librería para usar expresiones regulares


# Creamos la instancia de la aplicación FastAPI
app = FastAPI()  

# URL base del bestiario
BESTIARY_URL = "https://clayadavis.gitlab.io/osr-bestiary/bestiary/bfrpg/field-guide-1/"


class SSLAdapter(HTTPAdapter):
    #Clase para permitir conexiones SSL personalizadas al iniciar una sesión HTTP
    def __init__(self, *args, **kwargs):
        self.context = ssl.create_default_context()  # Crea un contexto SSL por defecto
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.context
        return super().init_poolmanager(*args, **kwargs)


def obtener_estadisticas(nombre: str) -> Dict:
    try:
        nombre_url = re.sub(r'[^a-zA-Z0-9\- ]', '', nombre).lower().replace(' ', '-')
        url = f"{BESTIARY_URL}{nombre_url}/"

        session = requests.Session()
        session.mount('https://', SSLAdapter())
        response = session.get(url)

        if response.status_code != 200:  
            raise HTTPException(status_code=404, detail=f"Enemigo '{nombre}' no encontrado en el bestiario. URL: {url}")

        soup = BeautifulSoup(response.content, "html.parser")

        stats_table = soup.find("table")
        stats = {}
        if stats_table:
            rows = stats_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) == 2:  
                    key = cells[0].get_text(strip=True).lower().replace(' ', '_').replace('.', '').replace(':', '')
                    value = cells[1].get_text(strip=True)
                    stats[key] = value if value else 'Unknown'

        descripcion = ''
        try:
            descripcion_p = soup.find("div", class_="e-content entry-content").find_all("p")[-1]
            if descripcion_p:
                descripcion = descripcion_p.get_text(strip=True)
        except:
            descripcion = 'Descripción no disponible.'

        enemigo = {
            "nombre": nombre,
            "armor_class": int(stats.get('armor_class', '0')) if stats.get('armor_class', '0').isdigit() else stats.get('armor_class', 'Unknown'),
            "hit_dice": stats.get('hit_dice', 'Unknown'),
            "number_of_attacks": stats.get('no_of_attacks', 'Unknown'),
            "damage": stats.get('damage', 'Unknown'),
            "movement": stats.get('movement', 'Unknown'),
            "number_of_appearing": stats.get('no_appearing', 'Unknown'),
            "save_as": stats.get('save_as', 'Unknown'),
            "morale": int(stats.get('morale', '0')) if stats.get('morale', '0').isdigit() else stats.get('morale', 'Unknown'),
            "treasure_type": stats.get('treasure_type', 'Unknown'),
            "xp": int(stats.get('xp', '0')) if stats.get('xp', '0').isdigit() else stats.get('xp', 'Unknown'),
            "descripcion": descripcion
        }

        return enemigo

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def obtener_lista_enemigos() -> List[Dict[str, str]]:
    try:
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        response = session.get(BESTIARY_URL)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudo acceder al bestiario principal.")

        soup = BeautifulSoup(response.content, "html.parser")
        enemigos = []

        postlist_div = soup.find('div', class_='postlist')
        if postlist_div:
            for a in postlist_div.find_all('a'):
                href = a.get('href')
                if href and href.endswith('/') and not href.startswith('../'):
                    enemigos.append({'nombre': a.get_text(strip=True), 'ruta': href.strip('/')})

        return enemigos

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
    return {"message": "API funcionando correctamente"}
    

@app.post("/consultar-enemigo/")
def consultar_enemigo(nombre: str = Body(..., embed=True)):
    enemigo = obtener_estadisticas(nombre)
    return {"enemigo": enemigo}


@app.get("/listar-enemigos/")
def listar_enemigos():
    enemigos = obtener_lista_enemigos()
    return {"enemigos": enemigos}
