import pygame
import os
import sys
import json
import math
import random
import time

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_minijuegos = os.path.join(ruta_actual, "..", "minijuegos")
sys.path.append(os.path.normpath(ruta_minijuegos))

pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

ancho = 800
alto = 600


def crear_ventana():
    """Crea la ventana (escalable). Debe existir ANTES de cargar imágenes."""
    try:
        return pygame.display.set_mode((ancho, alto), pygame.SCALED | pygame.RESIZABLE)
    except (pygame.error, AttributeError):
        return pygame.display.set_mode((ancho, alto))


crear_ventana()

# Cada cuántos ms baja 1 punto cada barra (antes 1000). Más alto = más lento.
TIEMPO_DISMINUCION = 4500
# Pantallas en las que las barras NO bajan (todos los minijuegos, actuales y futuros).
# Para un minijuego nuevo basta usar alguna de estas subpantallas o añadir su nombre aquí.
SUBPANTALLAS_PAUSA = {"minijuegos", "minijuego"}
DURACION_NOCHE = 3000

# --- Ausencia / guardado -----------------------------------------------------
OFFLINE_SEGUNDOS_POR_PUNTO = 120    # 1 punto cada 120 s de ausencia
OFFLINE_MAX_PERDIDA = 60            # como máximo se pierden 60 puntos
NECESIDAD_MINIMA_OFFLINE = 10       # ausente, ninguna barra baja de 10
INTERVALO_AUTOGUARDADO = 10000      # ms
BONUS_DIARIO = 20                   # monedas por entrar un día nuevo
DURACION_AVISO = 1800               # ms que se ve cada aviso

CARPETAS = [
    "", "FONDOS", "objetos", "personajes", "imagenes", "sonidos",
    "..", os.path.join("..", "FONDOS"), os.path.join("..", "objetos"),
    os.path.join("..", "sonidos"),
]


def buscar_ruta(nombre):
    for carpeta in CARPETAS:
        ruta = os.path.normpath(os.path.join(ruta_actual, carpeta, nombre))
        if os.path.isfile(ruta):
            return ruta
    return None


def cargar_imagen(nombre, tamaño=None, maximo=None, opaca=False):
    ruta = buscar_ruta(nombre)
    if ruta is None:
        print(f"[AVISO] No se encontró la imagen: {nombre}")
        return None
    try:
        img = pygame.image.load(ruta)
        img = img.convert() if opaca else img.convert_alpha()
    except pygame.error as e:
        print(f"[AVISO] No se pudo cargar {nombre}: {e}")
        return None
    if tamaño:
        return pygame.transform.smoothscale(img, tamaño)
    if maximo:
        w, h = img.get_size()
        esc = min(maximo / w, maximo / h)
        return pygame.transform.smoothscale(img, (int(w * esc), int(h * esc)))
    return img


def fondo_o_color(nombre, color):
    img = cargar_imagen(nombre, tamaño=(ancho, alto), opaca=True)
    if img is None:
        img = pygame.Surface((ancho, alto)).convert()
        img.fill(color)
    return img


def _ajustar(img, maximo):
    """Escala una imagen para que entre en un cuadrado de 'maximo' px."""
    w, h = img.get_size()
    esc = min(maximo / w, maximo / h)
    tam = (max(1, int(w * esc)), max(1, int(h * esc)))
    try:
        return pygame.transform.smoothscale(img, tam)
    except ValueError:
        return pygame.transform.scale(img, tam)


# --- Sonidos (opcionales: si no existe el archivo, simplemente no suena) ----
config = {"sonido": True}
SONIDOS_ARCHIVOS = {
    "comer": "comer.wav", "moneda": "moneda.wav", "click": "click.wav",
    "nivel": "nivel.wav", "error": "error.wav", "logro": "logro.wav",
}
sonidos = {}
if pygame.mixer.get_init():
    for _n, _a in SONIDOS_ARCHIVOS.items():
        _r = buscar_ruta(_a)
        if _r:
            try:
                sonidos[_n] = pygame.mixer.Sound(_r)
                sonidos[_n].set_volume(0.5)
            except pygame.error:
                pass


def sonar(nombre):
    if config["sonido"] and nombre in sonidos:
        sonidos[nombre].play()


def alternar_sonido():
    config["sonido"] = not config["sonido"]
    guardar()


ARCHIVO_GUARDADO = os.path.join(ruta_actual, "guardado.json")

# (nombre, archivo, precio, cuánto sube COMER)
COMIDAS = [
    ("Manzana", "manzana.png", 3, 10),
    ("Pizza", "pizza.png", 6, 20),
    ("Sushi", "sushi.png", 8, 25),
    ("Hamburguesa", "hamburguesa.png", 10, 30),
    ("Zanahoria", "zanahoria.png", 2, 8),
    ("Helado", "helado.png", 5, 12),
    ("Dona", "dona.png", 4, 12),
    ("Sopa", "sopa.png", 7, 18),
    ("Tacos", "tacos.png", 9, 26),
    ("Sandía", "sandia.png", 6, 16),
    ("Pastel", "pastel.png", 12, 30),
    ("Pollo", "pollo.png", 11, 32),
]

# Efectos extra al comer (además de subir COMER). Negativo = ensucia.
EFECTOS = {
    "Helado": {"jugar": 12},
    "Dona": {"jugar": 8},
    "Pastel": {"jugar": 15},
    "Sopa": {"dormir": 10},
    "Pizza": {"baño": -3},
    "Tacos": {"baño": -3},
    "Pollo": {"baño": -4},
    "Hamburguesa": {"baño": -5},
}

# Jardín: segundos de crecimiento, cuánto se cosecha y precio de la semilla.
CULTIVOS = {
    "Manzana": {"tiempo": 40, "cosecha": 2, "semilla": 1},
    "Zanahoria": {"tiempo": 60, "cosecha": 3, "semilla": 1},
    "Sandía": {"tiempo": 120, "cosecha": 2, "semilla": 3},
}

# Misiones diarias (se reinician cada día).
MISIONES = [
    {"id": "comer", "texto": "Dale de comer a Pau 3 veces", "meta": 3, "premio": 15},
    {"id": "banar", "texto": "Báñala una vez", "meta": 1, "premio": 15},
    {"id": "dormir", "texto": "Haz que duerma una vez", "meta": 1, "premio": 10},
    {"id": "caricias", "texto": "Hazle 10 caricias", "meta": 10, "premio": 12},
    {"id": "minijuegos", "texto": "Juega 2 minijuegos", "meta": 2, "premio": 20},
    {"id": "cosechar", "texto": "Cosecha 2 veces en el jardín", "meta": 2, "premio": 20},
]
MISIONES_POR_ID = {m["id"]: m for m in MISIONES}

# Logros permanentes: se cobran solos al cumplirse.
LOGROS = [
    {"id": "bocado", "nombre": "Primer bocado", "desc": "Dale de comer 1 vez", "stat": "comidas", "meta": 1, "premio": 10},
    {"id": "glotona", "nombre": "Glotona", "desc": "Dale de comer 30 veces", "stat": "comidas", "meta": 30, "premio": 40},
    {"id": "limpia", "nombre": "Limpia y fresca", "desc": "Báñala 5 veces", "stat": "banos", "meta": 5, "premio": 25},
    {"id": "granjera", "nombre": "Granjera", "desc": "Cosecha 10 veces", "stat": "cosechas", "meta": 10, "premio": 40},
    {"id": "mimosa", "nombre": "Mimosa", "desc": "Hazle 100 caricias", "stat": "caricias", "meta": 100, "premio": 35},
    {"id": "jugona", "nombre": "Jugona", "desc": "Juega 15 minijuegos", "stat": "minijuegos", "meta": 15, "premio": 50},
    {"id": "regalos", "nombre": "Cazaregalos", "desc": "Atrapa 5 regalos", "stat": "regalos", "meta": 5, "premio": 30},
    {"id": "suerte", "nombre": "Suertuda", "desc": "Gira la ruleta 5 veces", "stat": "ruleta", "meta": 5, "premio": 30},
    {"id": "nivel5", "nombre": "Crecidita", "desc": "Llega al nivel 5", "stat": "nivel", "meta": 5, "premio": 60},
    {"id": "racha3", "nombre": "Constante", "desc": "Racha de 3 días", "stat": "racha", "meta": 3, "premio": 50},
]

# ---------------------------------------------------------------------------
# ROPA Y ACCESORIOS
# Para agregar una prenda nueva: añade una línea a PRENDAS y copia su PNG
# (fondo transparente) a la carpeta "personajes". Si el PNG todavía no existe,
# el juego funciona igual: la tarjeta se ve con un "?" y la prenda no se dibuja.
#   nombre : nombre que se muestra (debe ser único)
#   archivo: imagen PNG
#   slot   : una prenda por slot; prendas de slots distintos se combinan
#   precio : monedas (0 = ya viene en el armario)
# Opcionales:
#   offset : (dx, dy) respecto del centro de Pau (y negativo = más arriba)
#   tam    : tamaño máximo en px (se mantiene la proporción, sin deformar).
#            Sin "tam", la imagen es una capa del tamaño de Pau (como las
#            prendas originales).
#   escala : multiplica el tamaño final (1.0 = tal cual)
#   archivo_dormido: imagen alternativa para cuando Pau duerme
#
# SLOTS (de abajo hacia arriba, ver ORDEN_CAPAS):
#   cuerpo, cuello, mano, cara, vello (bigote/barba), boca, pelo,
#   cabeza (gorros), adorno (moños, cuernos, antenas), extra, efecto
# Los accesorios nuevos usan "tam" y "offset": se ven bien con PNG recortados
# al objeto; si alguno queda corrido, ajusta solo su offset o su tam.
# ---------------------------------------------------------------------------
PRENDAS = [
    # --- Prendas originales ---
    {"nombre": "Gorra", "archivo": "gorra.png", "slot": "cabeza", "precio": 0},
    {"nombre": "Lentes", "archivo": "lentes.png", "slot": "cara", "precio": 30},
    {"nombre": "Sombrero", "archivo": "sombrero.png", "slot": "cabeza", "precio": 40},
    {"nombre": "Camiseta", "archivo": "camiseta.png", "slot": "cuerpo", "precio": 50},
    {"nombre": "Bufanda", "archivo": "bufanda.png", "slot": "cuello", "precio": 60},
    {"nombre": "Vestido", "archivo": "vestido.png", "slot": "cuerpo", "precio": 80},
    {"nombre": "Corona", "archivo": "corona.png", "slot": "cabeza", "precio": 150},

    # --- Accesorios y disfraces ---
    {"nombre": "Tutú de ballet", "archivo": "tutu.png", "slot": "cuerpo", "precio": 90,
     "offset": (0, 70), "tam": 150},
    {"nombre": "Moño rosa", "archivo": "mono_rosa.png", "slot": "adorno", "precio": 25,
     "offset": (45, -95), "tam": 55},
    {"nombre": "Cuerno de unicornio", "archivo": "cuerno_unicornio.png", "slot": "adorno",
     "precio": 70, "offset": (0, -112), "tam": 75},
    {"nombre": "Ojos de alien", "archivo": "ojos_alien.png", "slot": "cara", "precio": 45,
     "offset": (0, -25), "tam": 120},
    {"nombre": "Antenas de alien", "archivo": "antenas_alien.png", "slot": "adorno",
     "precio": 45, "offset": (0, -115), "tam": 100},
    {"nombre": "Caca", "archivo": "caca.png", "slot": "extra", "precio": 15,
     "offset": (0, -108), "tam": 60},
    {"nombre": "Barba de Papá Noel", "archivo": "barba_noel.png", "slot": "vello",
     "precio": 55, "offset": (0, 45), "tam": 130},
    {"nombre": "Gorrito de Navidad", "archivo": "gorro_navidad.png", "slot": "cabeza",
     "precio": 50, "offset": (0, -100), "tam": 120},
    {"nombre": "Ojos de Minion", "archivo": "ojos_minion.png", "slot": "cara", "precio": 50,
     "offset": (0, -25), "tam": 130},
    {"nombre": "Banana", "archivo": "banana.png", "slot": "mano", "precio": 20,
     "offset": (-95, 35), "tam": 70},
    {"nombre": "Pelo de Justin Bieber", "archivo": "pelo_bieber.png", "slot": "pelo",
     "precio": 75, "offset": (0, -85), "tam": 140},
    {"nombre": "Cadena de oro", "archivo": "cadena_oro.png", "slot": "cuello",
     "precio": 120, "offset": (0, 45), "tam": 110},
    {"nombre": "Lluvia de dinero", "archivo": "lluvia_dinero.png", "slot": "efecto",
     "precio": 100, "offset": (0, 0), "tam": 230},
    {"nombre": "Gorro de vaquero", "archivo": "gorro_vaquero.png", "slot": "cabeza",
     "precio": 60, "offset": (0, -100), "tam": 150},
    {"nombre": "Pistola", "archivo": "pistola.png", "slot": "mano", "precio": 70,
     "offset": (95, 35), "tam": 80},
    {"nombre": "Gorro de mariachi", "archivo": "gorro_mariachi.png", "slot": "cabeza",
     "precio": 80, "offset": (0, -100), "tam": 160},
    {"nombre": "Guitarra", "archivo": "guitarra.png", "slot": "mano", "precio": 90,
     "offset": (80, 40), "tam": 140},
    {"nombre": "Bigote", "archivo": "bigote.png", "slot": "vello", "precio": 25,
     "offset": (0, 15), "tam": 80},
    {"nombre": "Boina", "archivo": "boina.png", "slot": "cabeza", "precio": 35,
     "offset": (0, -98), "tam": 120},
    {"nombre": "Baguette", "archivo": "baguette.png", "slot": "mano", "precio": 30,
     "offset": (-90, 30), "tam": 130},
    {"nombre": "Gorro de Mario", "archivo": "gorro_mario.png", "slot": "cabeza",
     "precio": 60, "offset": (0, -98), "tam": 120},
    {"nombre": "Gorro de Luigi", "archivo": "gorro_luigi.png", "slot": "cabeza",
     "precio": 60, "offset": (0, -98), "tam": 120},
    {"nombre": "Corona de Peach", "archivo": "corona_peach.png", "slot": "cabeza",
     "precio": 130, "offset": (0, -105), "tam": 100},
    {"nombre": "Gorro de Kiko", "archivo": "gorro_kiko.png", "slot": "cabeza",
     "precio": 55, "offset": (0, -98), "tam": 120},
    {"nombre": "Paleta", "archivo": "paleta.png", "slot": "boca", "precio": 20,
     "offset": (25, 25), "tam": 60},
    {"nombre": "Cuernos de diablo", "archivo": "cuernos_diablo.png", "slot": "adorno",
     "precio": 55, "offset": (0, -105), "tam": 120},
    {"nombre": "Lentes PRO", "archivo": "lentes_pro.png", "slot": "cara", "precio": 90,
     "offset": (0, -25), "tam": 130},
]
PRENDAS_POR_NOMBRE = {p["nombre"]: p for p in PRENDAS}
# De abajo hacia arriba. Una prenda por slot; slots distintos se combinan.
ORDEN_CAPAS = ["cuerpo", "cuello", "mano", "cara", "vello", "boca",
               "pelo", "cabeza", "adorno", "extra", "efecto"]
PRENDAS_POR_PAGINA = 8
Y_ARMARIO = 150
Y_TIENDA = 200


# --- Estado persistente ------------------------------------------------------
def hoy():
    return time.strftime("%Y-%m-%d")


monedas = 100
inventario = {c[0]: 0 for c in COMIDAS}
ropa_puesta = {}
ropa_comprada = set()
records = {"atrapa": 0, "memoria": 0, "reflejos": 0, "simon": 0}
stats = {"comidas": 0, "banos": 0, "cosechas": 0, "caricias": 0,
         "minijuegos": 0, "regalos": 0, "ruleta": 0}
logros_hechos = []
ultimo_dia = hoy()
bonus_diario_pendiente = 0
racha = 1
xp = 0
nivel = 1
huerta = [None, None, None]
cultivo_elegido = "Manzana"
misiones_dia = {"dia": hoy(), "progreso": {}, "reclamadas": []}
ruleta_dia = ""         # día en que se usó el giro gratis

baño = 100
comer = 100
dormir = 100
jugar = 100


def es_poseida(nombre):
    prenda = PRENDAS_POR_NOMBRE[nombre]
    return prenda.get("precio", 0) == 0 or nombre in ropa_comprada


def prendas_poseidas():
    return [p for p in PRENDAS if es_poseida(p["nombre"])]


def _perder(valor, perdida):
    return max(min(valor, NECESIDAD_MINIMA_OFFLINE), valor - perdida)


def _aplicar_ausencia(ultima_vez):
    global baño, comer, dormir, jugar
    segundos = max(0.0, time.time() - ultima_vez)
    perdida = min(OFFLINE_MAX_PERDIDA, int(segundos // OFFLINE_SEGUNDOS_POR_PUNTO))
    if perdida <= 0:
        return
    baño = _perder(baño, perdida)
    comer = _perder(comer, perdida)
    dormir = _perder(dormir, perdida)
    jugar = _perder(jugar, perdida)


def _limitar(v):
    return max(0, min(100, int(v)))


def _procesar_nuevo_dia(dia_anterior):
    """Racha y bonus diario. Se usa al cargar y también si cambia el día jugando."""
    global racha, monedas, bonus_diario_pendiente, ultimo_dia
    if dia_anterior == hoy():
        return
    ayer = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
    racha = racha + 1 if dia_anterior == ayer else 1
    bonus = BONUS_DIARIO + 5 * min(racha - 1, 6)
    monedas += bonus
    bonus_diario_pendiente = bonus
    ultimo_dia = hoy()


def cargar_datos():
    global monedas, baño, comer, dormir, jugar
    global ultimo_dia, racha, xp, nivel, misiones_dia, ruleta_dia
    if os.path.isfile(ARCHIVO_GUARDADO):
        try:
            with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as f:
                datos = json.load(f)
            monedas = int(datos.get("monedas", 100))
            for k, v in datos.get("inventario", {}).items():
                if k in inventario:
                    inventario[k] = int(v)
            for nombre in datos.get("ropa_comprada", []):
                if nombre in PRENDAS_POR_NOMBRE:
                    ropa_comprada.add(nombre)
            for slot, nombre in datos.get("ropa", {}).items():
                prenda = PRENDAS_POR_NOMBRE.get(nombre)
                if prenda is not None and prenda["slot"] == slot:
                    ropa_puesta[slot] = nombre
                    ropa_comprada.add(nombre)
            for k in records:
                records[k] = int(datos.get("records", {}).get(k, 0))
            for k in stats:
                stats[k] = int(datos.get("stats", {}).get(k, 0))
            logros_hechos[:] = [k for k in datos.get("logros", [])
                                if any(l["id"] == k for l in LOGROS)]
            config["sonido"] = bool(datos.get("config", {}).get("sonido", True))
            ruleta_dia = str(datos.get("ruleta_dia", ""))

            nec = datos.get("necesidades", {})
            baño = _limitar(nec.get("baño", 100))
            comer = _limitar(nec.get("comer", 100))
            dormir = _limitar(nec.get("dormir", 100))
            jugar = _limitar(nec.get("jugar", 100))
            _aplicar_ausencia(float(datos.get("ultima_vez", time.time())))

            xp = max(0, int(datos.get("xp", 0)))
            nivel = max(1, int(datos.get("nivel", 1)))
            racha = max(1, int(datos.get("racha", 1)))
            for i, parcela in enumerate(datos.get("huerta", [])[:len(huerta)]):
                if (isinstance(parcela, dict) and parcela.get("cultivo") in CULTIVOS
                        and isinstance(parcela.get("inicio"), (int, float))):
                    huerta[i] = {
                        "cultivo": parcela["cultivo"],
                        "inicio": float(parcela["inicio"]),
                        "regada": bool(parcela.get("regada", False)),
                    }
            m = datos.get("misiones", {})
            if isinstance(m, dict) and m.get("dia") == hoy():
                misiones_dia = {
                    "dia": hoy(),
                    "progreso": {k: int(v) for k, v in m.get("progreso", {}).items()
                                 if k in MISIONES_POR_ID},
                    "reclamadas": [k for k in m.get("reclamadas", [])
                                   if k in MISIONES_POR_ID],
                }

            ultimo_dia = datos.get("ultimo_dia", hoy())
            _procesar_nuevo_dia(ultimo_dia)
            ultimo_dia = hoy()
            return
        except (OSError, ValueError, TypeError, AttributeError):
            # Archivo corrupto: se guarda una copia antes de empezar de cero.
            try:
                os.replace(ARCHIVO_GUARDADO, ARCHIVO_GUARDADO + ".bak")
            except OSError:
                pass

    monedas = 100
    guardar()


def guardar():
    tmp = ARCHIVO_GUARDADO + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "monedas": monedas,
                    "inventario": inventario,
                    "ropa": ropa_puesta,
                    "ropa_comprada": sorted(ropa_comprada),
                    "records": records,
                    "stats": stats,
                    "logros": logros_hechos,
                    "config": config,
                    "ruleta_dia": ruleta_dia,
                    "necesidades": {
                        "baño": baño, "comer": comer,
                        "dormir": dormir, "jugar": jugar,
                    },
                    "ultima_vez": time.time(),
                    "ultimo_dia": ultimo_dia,
                    "racha": racha,
                    "xp": xp,
                    "nivel": nivel,
                    "huerta": huerta,
                    "misiones": misiones_dia,
                },
                f,
            )
        os.replace(tmp, ARCHIVO_GUARDADO)     # escritura atómica
    except OSError as e:
        print(f"[AVISO] No se pudo guardar: {e}")


cargar_datos()

acum_descenso = 0.0       # ms acumulados hacia el próximo descenso de barras
ultimo_incremento_dormir = pygame.time.get_ticks()
ultimo_guardado = pygame.time.get_ticks()
ultimo_chequeo_dia = pygame.time.get_ticks()
ultimo_frame = pygame.time.get_ticks()
ultimo_zzz = 0
ultima_caricia = 0
inicio_noche = 0
modo_noche = False
muerta = False
mensaje_temporal = ""
tiempo_mensaje = 0
cola_avisos = []
habla = ("", 0)                 # (texto, ms hasta cuando se muestra)
habitacion_actual = 1
nombres_habitaciones = ["BAÑO", "SALA DE ESTAR", "HABITACIÓN", "COCINA", "JARDÍN"]
subpantalla = "normal"
pagina_armario = 0
pestaña_tienda = "comidas"
minijuego = None


def avisar(texto):
    """Pone un aviso en cola (así no se pisan entre sí)."""
    if len(cola_avisos) < 6 and (not cola_avisos or cola_avisos[-1] != texto):
        cola_avisos.append(texto)


def _procesar_avisos(ahora):
    global mensaje_temporal, tiempo_mensaje
    if cola_avisos and (not mensaje_temporal or ahora - tiempo_mensaje >= DURACION_AVISO):
        mensaje_temporal = cola_avisos.pop(0)
        tiempo_mensaje = ahora


def pau_dice(texto, ms=1800):
    global habla
    habla = (texto, pygame.time.get_ticks() + ms)


fondo_bano = fondo_o_color("bano.png", (173, 216, 230))
fondo_sala = fondo_o_color("principal.png", (240, 230, 140))
fondo_habitacion = fondo_o_color("habitacion.png", (230, 230, 250))
fondo_cocina = fondo_o_color("cocina.png", (255, 218, 185))
fondo_jardin = fondo_o_color("jardin.png", (150, 210, 150))

TAMAÑO_POU = 220

pou_base = cargar_imagen("pou.png", maximo=TAMAÑO_POU)
if pou_base is None:
    pou_base = pygame.Surface((150, 150), pygame.SRCALPHA)
    pou_base.fill((139, 69, 19))


def cargar_pou(nombre):
    img = cargar_imagen(nombre, maximo=TAMAÑO_POU)
    return img if img is not None else pou_base


pou_feliz = cargar_pou("paufeliz.png")
pou_maso = cargar_pou("paumaso.png")
pou_popo = cargar_pou("poupopo.png")
pou_triste = cargar_pou("poutriste.png")
pou_muerto = cargar_pou("paumuerto.png")
pou_dormido = cargar_pou("poudormido.png")

UMBRAL_SUCIO = 60


def _teñir_sucio(img):
    t = img.copy()
    t.fill((190, 160, 110), special_flags=pygame.BLEND_RGB_MULT)
    return t


pou_dormido_sucio = _teñir_sucio(pou_dormido)

TAMAÑO_OBJETO = 100
img_jabon = cargar_imagen("jabon.png", maximo=TAMAÑO_OBJETO)
img_ducha = cargar_imagen("ducha.png", maximo=TAMAÑO_OBJETO)
img_toalla = cargar_imagen("toalla.png", maximo=TAMAÑO_OBJETO)
img_almohada = cargar_imagen("almohada.png", maximo=TAMAÑO_OBJETO)

imagenes_comidas = {c[0]: cargar_imagen(c[1], maximo=90) for c in COMIDAS}
imgs_caida = {n: _ajustar(i, 48) for n, i in imagenes_comidas.items() if i is not None}
img_cesta = _ajustar(pou_feliz, 90)

# --- Decoración de la mesa de luz -------------------------------------------
# La almohada (almohada.png) ocupa el lugar donde estaba la lámpara.
# AJUSTAR posición y tamaño según el fondo "habitacion.png".
ALMOHADA_MESITA_BASE = (650, 400)   # punto donde se apoya (centro inferior)
TAMAÑO_ALMOHADA_MESITA = 80         # tamaño máximo en px (mantiene proporción)
img_almohada_mesita = cargar_imagen("almohada.png", maximo=TAMAÑO_ALMOHADA_MESITA)

# --- Velos reutilizables (se crean UNA vez, no en cada frame) ---------------
VELO_NOCHE = pygame.Surface((ancho, alto))
VELO_NOCHE.set_alpha(180)
VELO_NOCHE.fill((0, 0, 50))
VELO_MUERTE = pygame.Surface((ancho, alto))
VELO_MUERTE.set_alpha(150)
VELO_MUERTE.fill((20, 0, 0))


# --- Ropa: imágenes ----------------------------------------------------------
def cargar_prenda(archivo, escala=1.0, tam=None):
    img = cargar_imagen(archivo, maximo=tam or TAMAÑO_POU)
    if img is not None and escala != 1.0:
        w, h = img.get_size()
        img = pygame.transform.smoothscale(img, (int(w * escala), int(h * escala)))
    return img


def _miniatura(img, maximo=90):
    caja = img.get_bounding_rect()
    if caja.width == 0 or caja.height == 0:
        return img
    recorte = img.subsurface(caja).copy()
    return _ajustar(recorte, maximo)


imagenes_ropa = {
    p["nombre"]: cargar_prenda(p["archivo"], p.get("escala", 1.0), p.get("tam"))
    for p in PRENDAS
}
imagenes_ropa_dormido = {
    p["nombre"]: cargar_prenda(p["archivo_dormido"], p.get("escala", 1.0), p.get("tam"))
    for p in PRENDAS if "archivo_dormido" in p
}
miniaturas_ropa = {
    n: _miniatura(img) for n, img in imagenes_ropa.items() if img is not None
}

fuente = pygame.font.Font(None, 28)
fuente_grande = pygame.font.Font(None, 36)
fuente_numero = pygame.font.Font(None, 22)
flecha_izquierda = pygame.Rect(10, 270, 50, 60)
flecha_derecha = pygame.Rect(740, 270, 50, 60)
objeto_jabon = pygame.Rect(190, 450, 110, 110)
objeto_ducha = pygame.Rect(345, 450, 110, 110)
objeto_toalla = pygame.Rect(500, 450, 110, 110)
objetos_bano = [
    (objeto_jabon, img_jabon, "Jabón"),
    (objeto_ducha, img_ducha, "Ducha"),
    (objeto_toalla, img_toalla, "Toalla"),
]

fase_bano = 0
progreso_bano = [0.0, 0.0, 0.0]
FACTORES_BANO = [0.15, 0.20, 0.20]
PISTAS_BANO = [
    "1/3: Frota el jabón sobre Pau",
    "2/3: Pásale la ducha para enjuagarla",
    "3/3: Sécala con la toalla",
]

arrastrando = None
pos_arrastre = (0, 0)
zona_pou = pygame.Rect(0, 0, 200, 220)
zona_pou.center = (400, 320)
_azar = random.Random(7)
BURBUJAS = [
    (_azar.randint(-85, 85), _azar.randint(-95, 95), _azar.randint(10, 20))
    for _ in range(45)
]
GOTAS = [(_azar.randint(-90, 90), _azar.randint(-100, 100)) for _ in range(30)]
MANCHAS = [
    (_azar.randint(-70, 70), _azar.randint(-80, 80), _azar.randint(4, 9))
    for _ in range(14)
]


def _tenue(img):
    if img is None:
        return None
    t = img.copy()
    t.set_alpha(90)
    return t


imgs_bano_tenues = [_tenue(o[1]) for o in objetos_bano]

objeto_almohada = pygame.Rect(345, 450, 110, 110)
boton_armario = pygame.Rect(480, 480, 140, 50)
boton_comidas = pygame.Rect(325, 480, 150, 50)

# Sala de estar
boton_minijuegos = pygame.Rect(150, 480, 160, 50)
boton_tienda = pygame.Rect(320, 480, 160, 50)
boton_ruleta = pygame.Rect(490, 480, 160, 50)
boton_misiones = pygame.Rect(235, 540, 160, 40)
boton_logros = pygame.Rect(405, 540, 160, 40)

botones_minijuegos = [pygame.Rect(300, 150 + i * 65, 200, 45) for i in range(5)]

boton_volver = pygame.Rect(20, 20, 100, 40)
boton_revivir = pygame.Rect(300, 340, 200, 50)
boton_reintentar = pygame.Rect(300, 360, 200, 45)

boton_quitar_ropa = pygame.Rect(640, 545, 140, 40)
boton_pag_ant = pygame.Rect(250, 545, 80, 40)
boton_pag_sig = pygame.Rect(470, 545, 80, 40)
boton_tab_comidas = pygame.Rect(250, 148, 140, 40)
boton_tab_ropa = pygame.Rect(410, 148, 140, 40)

boton_semilla = pygame.Rect(20, 125, 200, 40)
parcelas = [pygame.Rect(190 + i * 155, 450, 110, 100) for i in range(3)]

pos_y_barras = 65
barra_baño = pygame.Rect(30, pos_y_barras, 170, 20)
barra_comer = pygame.Rect(220, pos_y_barras, 170, 20)
barra_dormir = pygame.Rect(410, pos_y_barras, 170, 20)
barra_jugar = pygame.Rect(600, pos_y_barras, 170, 20)


# ---------------------------------------------------------------------------
# FORMAS Y PARTÍCULAS
# ---------------------------------------------------------------------------
def dibujar_corazon(sup, centro, r, color):
    cx, cy = centro
    pygame.draw.circle(sup, color, (cx - r // 2, cy - r // 4), r // 2 + 1)
    pygame.draw.circle(sup, color, (cx + r // 2, cy - r // 4), r // 2 + 1)
    pygame.draw.polygon(
        sup, color, [(cx - r, cy - r // 6), (cx + r, cy - r // 6), (cx, cy + r)]
    )


def dibujar_estrella(sup, centro, r, color):
    puntos = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        puntos.append((centro[0] + rad * math.cos(ang), centro[1] + rad * math.sin(ang)))
    pygame.draw.polygon(sup, color, puntos)


particulas = []


def crear_particulas(tipo, pos, n=6):
    """tipo: corazon, estrella, moneda, burbuja o zzz."""
    for _ in range(n):
        if tipo == "zzz":
            vx, vy, dur = random.uniform(10, 25), random.uniform(-40, -25), 2.2
        else:
            vx, vy = random.uniform(-45, 45), random.uniform(-120, -50)
            dur = random.uniform(0.9, 1.5)
        particulas.append({
            "tipo": tipo,
            "x": pos[0] + random.randint(-15, 15),
            "y": pos[1] + random.randint(-10, 10),
            "vx": vx, "vy": vy, "edad": 0.0, "dur": dur,
            "tam": random.randint(8, 13),
        })
    del particulas[:-80]


def actualizar_particulas(dt):
    for p in particulas:
        p["edad"] += dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
    particulas[:] = [p for p in particulas if p["edad"] < p["dur"]]


def dibujar_particulas(ventana):
    for p in particulas:
        alfa = max(0, int(255 * (1 - p["edad"] / p["dur"])))
        r = p["tam"]
        if p["tipo"] == "zzz":
            s = fuente_grande.render("Z", True, (70, 70, 160))
        else:
            lado = r * 3
            s = pygame.Surface((lado, lado), pygame.SRCALPHA)
            c = (lado // 2, lado // 2)
            if p["tipo"] == "corazon":
                dibujar_corazon(s, c, r, (235, 70, 110))
            elif p["tipo"] == "estrella":
                dibujar_estrella(s, c, r, (255, 210, 50))
            elif p["tipo"] == "moneda":
                pygame.draw.circle(s, (255, 215, 0), c, r)
                pygame.draw.circle(s, (180, 130, 0), c, r, 2)
            else:
                pygame.draw.circle(s, (255, 255, 255), c, r, 2)
        s.set_alpha(alfa)
        ventana.blit(s, s.get_rect(center=(int(p["x"]), int(p["y"]))))


# ---------------------------------------------------------------------------
# DIBUJO BÁSICO
# ---------------------------------------------------------------------------
def color_barra(valor):
    if valor > 60:
        return (100, 200, 100)
    if valor > 30:
        return (235, 200, 60)
    return (220, 70, 70)


def dibujar_barra(ventana, rectangulo, nombre, valor):
    pygame.draw.rect(ventana, (220, 220, 220), rectangulo)
    ancho_barra = int(rectangulo.width * valor / 100)
    parte_llena = pygame.Rect(rectangulo.x, rectangulo.y, ancho_barra, rectangulo.height)
    pygame.draw.rect(ventana, color_barra(valor), parte_llena)
    alerta = valor <= 20 and (pygame.time.get_ticks() // 300) % 2 == 0
    pygame.draw.rect(ventana, (200, 0, 0) if alerta else (0, 0, 0), rectangulo, 2)

    texto_nombre = fuente.render(nombre, True, (0, 0, 0))
    ventana.blit(texto_nombre,
                 (rectangulo.centerx - texto_nombre.get_width() // 2, rectangulo.y - 22))
    texto_numero = fuente_numero.render(str(valor), True, (0, 0, 0))
    ventana.blit(texto_numero,
                 (rectangulo.centerx - texto_numero.get_width() // 2, rectangulo.bottom + 2))


def dibujar_boton(ventana, rectangulo, texto):
    sobre = rectangulo.collidepoint(pygame.mouse.get_pos())
    relleno = (225, 238, 255) if sobre else (255, 255, 255)
    pygame.draw.rect(ventana, relleno, rectangulo, border_radius=8)
    pygame.draw.rect(ventana, (0, 0, 0), rectangulo, 2, border_radius=8)
    texto_render = fuente.render(texto, True, (0, 0, 0))
    ventana.blit(texto_render, texto_render.get_rect(center=rectangulo.center))


def dibujar_objeto(ventana, rectangulo, imagen, texto):
    if imagen is None:
        dibujar_boton(ventana, rectangulo, texto)
    else:
        ventana.blit(imagen, imagen.get_rect(center=rectangulo.center))


def dibujar_monedas(ventana):
    txt = fuente_grande.render(f"Monedas: {monedas}", True, (0, 0, 0))
    ventana.blit(txt, (725 - txt.get_width(), 10))


def dibujar_burbuja_habla(ventana, texto, centro_x, y):
    t = fuente.render(texto, True, (0, 0, 0))
    r = t.get_rect(center=(centro_x, y)).inflate(24, 14)
    pygame.draw.rect(ventana, (255, 255, 255), r, border_radius=12)
    pygame.draw.rect(ventana, (0, 0, 0), r, 2, border_radius=12)
    cola = [(centro_x - 8, r.bottom - 1), (centro_x + 8, r.bottom - 1),
            (centro_x, r.bottom + 10)]
    pygame.draw.polygon(ventana, (255, 255, 255), cola)
    pygame.draw.lines(ventana, (0, 0, 0), False, [cola[0], cola[2], cola[1]], 2)
    ventana.blit(t, t.get_rect(center=r.center))


def frase_pau():
    necesidades = [
        (baño, "¡Necesito un baño!"),
        (comer, "¡Tengo hambre!"),
        (dormir, "¡Tengo sueño!"),
        (jugar, "¡Quiero jugar!"),
    ]
    valor, frase = min(necesidades, key=lambda n: n[0])
    return frase if valor < 50 else None


def dibujar_bano(ventana):
    cx, cy = zona_pou.center

    if fase_bano == 0:
        espuma = progreso_bano[0]
    elif fase_bano == 1:
        espuma = 100 - progreso_bano[1]
    else:
        espuma = 0
    n = int(len(BURBUJAS) * espuma / 100)
    for dx, dy, r in BURBUJAS[:n]:
        pygame.draw.circle(ventana, (255, 255, 255), (cx + dx, cy + dy), r)
        pygame.draw.circle(ventana, (190, 215, 240), (cx + dx, cy + dy), r, 2)

    if fase_bano == 1:
        mojado = progreso_bano[1]
    elif fase_bano == 2:
        mojado = 100 - progreso_bano[2]
    else:
        mojado = 0
    g = int(len(GOTAS) * mojado / 100)
    for dx, dy in GOTAS[:g]:
        pygame.draw.circle(ventana, (90, 160, 255), (cx + dx, cy + dy), 5)

    for i, (rect, img, texto) in enumerate(objetos_bano):
        if i == arrastrando:
            continue
        imagen = img if i == fase_bano else imgs_bano_tenues[i]
        dibujar_objeto(ventana, rect, imagen, texto)

    if arrastrando is not None:
        rect, img, texto = objetos_bano[arrastrando]
        r = rect.copy()
        r.center = pos_arrastre
        if arrastrando == 1:
            for k in range(-2, 3):
                x = pos_arrastre[0] + k * 14
                pygame.draw.line(ventana, (90, 160, 255),
                                 (x, pos_arrastre[1] + 45), (x - 4, pos_arrastre[1] + 85), 3)
        dibujar_objeto(ventana, r, img, texto)

    pista = f"{PISTAS_BANO[fase_bano]} ({int(progreso_bano[fase_bano])}%)"
    txt = fuente.render(pista, True, (0, 0, 0))
    fondo_txt = txt.get_rect(center=(ancho // 2, 120)).inflate(16, 8)
    pygame.draw.rect(ventana, (255, 255, 255), fondo_txt)
    pygame.draw.rect(ventana, (0, 0, 0), fondo_txt, 2)
    ventana.blit(txt, txt.get_rect(center=fondo_txt.center))


def rect_tarjeta_comida(i, y0):
    return pygame.Rect(70 + (i % 4) * 170, y0 + (i // 4) * 160, 150, 155)


def texto_efectos(nombre, valor):
    partes = [f"+{valor} comer"]
    for k, v in EFECTOS.get(nombre, {}).items():
        partes.append(f"{v:+d} {k}")
    return " ".join(partes)


def dibujar_catalogo(ventana, titulo, modo):
    ventana.fill((200, 220, 240))
    t = fuente_grande.render(titulo, True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 100))
    y0 = Y_TIENDA if modo == "tienda" else Y_ARMARIO

    for i, comida in enumerate(prendas_de_pagina(COMIDAS)):
        nombre, _, precio, valor = comida
        rect = rect_tarjeta_comida(i, y0)
        pygame.draw.rect(ventana, (255, 255, 255), rect)
        pygame.draw.rect(ventana, (0, 0, 0), rect, 2)

        dibujar_comida(ventana, nombre, (rect.centerx, rect.y + 45), imagenes_comidas, 28)

        n = fuente.render(nombre, True, (0, 0, 0))
        ventana.blit(n, (rect.centerx - n.get_width() // 2, rect.y + 92))

        sub = f"{precio} monedas" if modo == "tienda" else f"Tienes: {inventario[nombre]}"
        s_ = fuente_numero.render(sub, True, (0, 0, 0))
        ventana.blit(s_, (rect.centerx - s_.get_width() // 2, rect.y + 116))
        e = fuente_numero.render(texto_efectos(nombre, valor), True, (90, 90, 90))
        ventana.blit(e, (rect.centerx - e.get_width() // 2, rect.y + 134))

    dibujar_boton(ventana, boton_volver, "Volver")
    dibujar_paginacion(ventana, len(COMIDAS))


# --- Armario / tienda de ropa -----------------------------------------------
def total_paginas(cantidad):
    return max(1, math.ceil(cantidad / PRENDAS_POR_PAGINA))


def prendas_de_pagina(lista):
    ini = pagina_armario * PRENDAS_POR_PAGINA
    return lista[ini:ini + PRENDAS_POR_PAGINA]


def rect_tarjeta_ropa(i, y0):
    return pygame.Rect(70 + (i % 4) * 170, y0 + (i // 4) * 160, 150, 150)


def manejar_paginacion(posicion, cantidad):
    global pagina_armario
    paginas = total_paginas(cantidad)
    if paginas <= 1:
        return False
    if boton_pag_ant.collidepoint(posicion):
        pagina_armario = max(0, pagina_armario - 1)
        return True
    if boton_pag_sig.collidepoint(posicion):
        pagina_armario = min(paginas - 1, pagina_armario + 1)
        return True
    return False


def dibujar_paginacion(ventana, cantidad):
    paginas = total_paginas(cantidad)
    if paginas > 1:
        dibujar_boton(ventana, boton_pag_ant, "<")
        dibujar_boton(ventana, boton_pag_sig, ">")
        pag = fuente.render(f"{pagina_armario + 1}/{paginas}", True, (0, 0, 0))
        ventana.blit(pag, pag.get_rect(center=(400, 565)))


def dibujar_tarjeta_prenda(ventana, rect, prenda, borde_verde, subtitulo):
    nombre = prenda["nombre"]
    pygame.draw.rect(ventana, (255, 255, 255), rect)
    if borde_verde:
        pygame.draw.rect(ventana, (0, 160, 0), rect, 4)
    else:
        pygame.draw.rect(ventana, (0, 0, 0), rect, 2)

    mini = miniaturas_ropa.get(nombre)
    if mini is not None:
        ventana.blit(mini, mini.get_rect(center=(rect.centerx, rect.y + 55)))
    else:                       # todavía no hay imagen para esta prenda
        q = fuente_grande.render("?", True, (170, 170, 170))
        ventana.blit(q, q.get_rect(center=(rect.centerx, rect.y + 55)))

    n = fuente.render(nombre, True, (0, 0, 0))
    ventana.blit(n, (rect.centerx - n.get_width() // 2, rect.y + 105))
    s = fuente_numero.render(subtitulo, True, (0, 0, 0))
    ventana.blit(s, (rect.centerx - s.get_width() // 2, rect.y + 128))


def alternar_prenda(prenda):
    slot, nombre = prenda["slot"], prenda["nombre"]
    if ropa_puesta.get(slot) == nombre:
        del ropa_puesta[slot]
        avisar(f"Te quitaste: {nombre}")
    else:
        ropa_puesta[slot] = nombre
        avisar(f"Pau lleva: {nombre}")
        pau_dice("¡Qué linda me veo!")
    guardar()


def comprar_prenda(prenda):
    global monedas
    nombre = prenda["nombre"]
    if es_poseida(nombre):
        avisar(f"Ya tienes {nombre}")
        return False
    if monedas < prenda["precio"]:
        avisar("No te alcanzan las monedas")
        sonar("error")
        return False
    monedas -= prenda["precio"]
    ropa_comprada.add(nombre)
    guardar()
    avisar(f"Compraste {nombre}")
    sonar("moneda")
    return True


def dibujar_armario(ventana):
    ventana.fill((200, 220, 240))
    t = fuente_grande.render("ARMARIO", True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 100))

    lista = prendas_poseidas()
    if not lista:
        m = fuente.render("Aún no tienes ropa. ¡Compra en la Tienda!", True, (0, 0, 0))
        ventana.blit(m, m.get_rect(center=(400, 300)))

    for i, prenda in enumerate(prendas_de_pagina(lista)):
        puesta = ropa_puesta.get(prenda["slot"]) == prenda["nombre"]
        dibujar_tarjeta_prenda(ventana, rect_tarjeta_ropa(i, Y_ARMARIO), prenda, puesta,
                               "Puesta" if puesta else "Poner")

    dibujar_boton(ventana, boton_volver, "Volver")
    dibujar_boton(ventana, boton_quitar_ropa, "Quitar todo")
    dibujar_paginacion(ventana, len(lista))


def dibujar_tienda_ropa(ventana):
    ventana.fill((200, 220, 240))
    t = fuente_grande.render("TIENDA DE ROPA", True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 100))

    for i, prenda in enumerate(prendas_de_pagina(PRENDAS)):
        tiene = es_poseida(prenda["nombre"])
        sub = "Comprada" if tiene else f"{prenda['precio']} monedas"
        dibujar_tarjeta_prenda(ventana, rect_tarjeta_ropa(i, Y_TIENDA), prenda, tiene, sub)

    dibujar_boton(ventana, boton_volver, "Volver")
    dibujar_paginacion(ventana, len(PRENDAS))


def dibujar_tienda(ventana):
    if pestaña_tienda == "comidas":
        dibujar_catalogo(ventana, "TIENDA DE COMIDAS", "tienda")
    else:
        dibujar_tienda_ropa(ventana)
    for rect, texto, clave in (
        (boton_tab_comidas, "Comidas", "comidas"),
        (boton_tab_ropa, "Ropa", "ropa"),
    ):
        dibujar_boton(ventana, rect, texto)
        if pestaña_tienda == clave:
            pygame.draw.rect(ventana, (0, 120, 255), rect, 4, border_radius=8)


def dibujar_ropa(ventana, centro):
    for slot in ORDEN_CAPAS:
        nombre = ropa_puesta.get(slot)
        if nombre is None:
            continue
        prenda = PRENDAS_POR_NOMBRE[nombre]
        img = imagenes_ropa_dormido.get(nombre) if modo_noche else None
        if img is None:
            img = imagenes_ropa[nombre]
        if img is None:
            continue
        dx, dy = prenda.get("offset", (0, 0))
        ventana.blit(img, img.get_rect(center=(centro[0] + dx, centro[1] + dy)))


# --- Suciedad ---------------------------------------------------------------
def dibujar_suciedad(ventana, centro):
    """Mantiene visible la suciedad de Pau mientras duerme."""
    if baño >= UMBRAL_SUCIO:
        return
    n = max(1, math.ceil(len(MANCHAS) * (UMBRAL_SUCIO - baño) / UMBRAL_SUCIO))
    for dx, dy, r in MANCHAS[:n]:
        pygame.draw.circle(ventana, (110, 75, 40), (centro[0] + dx, centro[1] + dy), r)


def dibujar_almohada_mesita(ventana):
    if img_almohada_mesita is not None:
        ventana.blit(img_almohada_mesita,
                     img_almohada_mesita.get_rect(midbottom=ALMOHADA_MESITA_BASE))


def obtener_personaje():
    if modo_noche:
        return pou_dormido_sucio if baño < UMBRAL_SUCIO else pou_dormido

    peor = min(baño, comer, dormir, jugar)
    if peor <= 0:
        return pou_muerto
    if peor <= 30:
        return pou_triste
    if peor < 60:
        return pou_popo
    if peor < 80:
        return pou_maso
    return pou_feliz


# ---------------------------------------------------------------------------
# NIVELES, LOGROS, MISIONES, JARDÍN Y REGALOS
# ---------------------------------------------------------------------------
def xp_para_siguiente(n):
    return 40 + 20 * n


def ganar_xp(cantidad):
    global xp, nivel, monedas
    xp += cantidad
    while xp >= xp_para_siguiente(nivel):
        xp -= xp_para_siguiente(nivel)
        nivel += 1
        premio = 20 + 5 * nivel
        monedas += premio
        avisar(f"¡Nivel {nivel}! +{premio} monedas")
        sonar("nivel")
        crear_particulas("estrella", (400, 300), 14)


def dibujar_nivel(ventana):
    t = fuente.render(f"Nv. {nivel}", True, (0, 0, 0))
    ventana.blit(t, (30, 8))
    barra = pygame.Rect(95, 14, 110, 10)
    pygame.draw.rect(ventana, (220, 220, 220), barra)
    lleno = int(barra.width * xp / xp_para_siguiente(nivel))
    pygame.draw.rect(ventana, (120, 100, 230), (barra.x, barra.y, lleno, barra.height))
    pygame.draw.rect(ventana, (0, 0, 0), barra, 2)


def aplicar_efectos(nombre):
    global baño, dormir, jugar
    for k, v in EFECTOS.get(nombre, {}).items():
        if k == "baño":
            baño = _limitar(max(1, baño + v) if v < 0 else baño + v)
        elif k == "dormir":
            dormir = _limitar(dormir + v)
        elif k == "jugar":
            jugar = _limitar(jugar + v)


# --- Logros ---
def valor_logro(l):
    if l["stat"] == "nivel":
        return nivel
    if l["stat"] == "racha":
        return racha
    return stats.get(l["stat"], 0)


def revisar_logros():
    global monedas
    for l in LOGROS:
        if l["id"] not in logros_hechos and valor_logro(l) >= l["meta"]:
            logros_hechos.append(l["id"])
            monedas += l["premio"]
            avisar(f"¡Logro: {l['nombre']}! +{l['premio']}")
            sonar("logro")
            crear_particulas("estrella", (400, 250), 12)
            guardar()


def rect_logro(i):
    return pygame.Rect(40 + (i // 5) * 370, 140 + (i % 5) * 85, 350, 75)


def dibujar_logros(ventana):
    ventana.fill((200, 220, 240))
    t = fuente_grande.render("LOGROS", True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 95))
    c = fuente_numero.render(f"{len(logros_hechos)}/{len(LOGROS)} completados", True, (0, 0, 0))
    ventana.blit(c, c.get_rect(center=(400, 128)))

    for i, l in enumerate(LOGROS):
        r = rect_logro(i)
        hecho = l["id"] in logros_hechos
        pygame.draw.rect(ventana, (255, 255, 255), r, border_radius=10)
        pygame.draw.rect(ventana, (0, 160, 0) if hecho else (0, 0, 0), r,
                         3 if hecho else 2, border_radius=10)
        n = fuente.render(l["nombre"], True, (0, 0, 0))
        ventana.blit(n, (r.x + 12, r.y + 8))
        d = fuente_numero.render(l["desc"], True, (80, 80, 80))
        ventana.blit(d, (r.x + 12, r.y + 31))

        prog = min(l["meta"], valor_logro(l))
        barra = pygame.Rect(r.x + 12, r.bottom - 18, 230, 8)
        pygame.draw.rect(ventana, (220, 220, 220), barra)
        pygame.draw.rect(ventana, (120, 100, 230),
                         (barra.x, barra.y, int(barra.width * prog / l["meta"]), barra.height))
        pygame.draw.rect(ventana, (0, 0, 0), barra, 1)
        num = fuente_numero.render(f"{prog}/{l['meta']}", True, (0, 0, 0))
        ventana.blit(num, (barra.right + 8, barra.y - 5))

        if hecho:
            ok = fuente.render("¡Listo!", True, (0, 130, 0))
            ventana.blit(ok, ok.get_rect(midright=(r.right - 12, r.y + 22)))
        else:
            p = fuente_numero.render(f"+{l['premio']}", True, (160, 110, 0))
            ventana.blit(p, p.get_rect(midright=(r.right - 12, r.y + 22)))

    dibujar_boton(ventana, boton_volver, "Volver")


# --- Misiones diarias ---
def _revisar_dia_misiones():
    global misiones_dia
    if misiones_dia.get("dia") != hoy():
        misiones_dia = {"dia": hoy(), "progreso": {}, "reclamadas": []}


def progreso_mision(clave, n=1):
    _revisar_dia_misiones()
    meta = MISIONES_POR_ID[clave]["meta"]
    prog = misiones_dia["progreso"]
    prog[clave] = min(meta, prog.get(clave, 0) + n)


def mision_lista(m):
    return (misiones_dia["progreso"].get(m["id"], 0) >= m["meta"]
            and m["id"] not in misiones_dia["reclamadas"])


def hay_mision_lista():
    _revisar_dia_misiones()
    return any(mision_lista(m) for m in MISIONES)


def reclamar_mision(m):
    global monedas
    monedas += m["premio"]
    misiones_dia["reclamadas"].append(m["id"])
    ganar_xp(10)
    guardar()
    avisar(f"Misión cumplida: +{m['premio']} monedas")
    sonar("moneda")


def rect_fila_mision(i):
    return pygame.Rect(70, 145 + i * 65, 660, 55)


def rect_boton_mision(i):
    fila = rect_fila_mision(i)
    return pygame.Rect(fila.right - 140, fila.y + 8, 130, 39)


def dibujar_misiones(ventana):
    _revisar_dia_misiones()
    ventana.fill((200, 220, 240))
    t = fuente_grande.render("MISIONES DEL DÍA", True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 95))
    r = fuente_numero.render(f"Racha: {racha} día(s) seguidos", True, (0, 0, 0))
    ventana.blit(r, r.get_rect(center=(400, 133)))

    for i, m in enumerate(MISIONES):
        fila = rect_fila_mision(i)
        hecha = m["id"] in misiones_dia["reclamadas"]
        prog = misiones_dia["progreso"].get(m["id"], 0)
        pygame.draw.rect(ventana, (255, 255, 255), fila, border_radius=10)
        if hecha:
            pygame.draw.rect(ventana, (0, 160, 0), fila, 3, border_radius=10)
        else:
            pygame.draw.rect(ventana, (0, 0, 0), fila, 2, border_radius=10)

        txt = fuente.render(m["texto"], True, (0, 0, 0))
        ventana.blit(txt, (fila.x + 15, fila.centery - txt.get_height() // 2))
        det = fuente_numero.render(f"{prog}/{m['meta']}  (+{m['premio']} monedas)",
                                   True, (80, 80, 80))
        ventana.blit(det, (fila.x + 340, fila.centery - det.get_height() // 2))

        if hecha:
            ok = fuente.render("Reclamada", True, (0, 130, 0))
            ventana.blit(ok, ok.get_rect(center=rect_boton_mision(i).center))
        elif mision_lista(m):
            dibujar_boton(ventana, rect_boton_mision(i), "Reclamar")

    dibujar_boton(ventana, boton_volver, "Volver")


def click_misiones(posicion):
    global subpantalla
    if boton_volver.collidepoint(posicion):
        subpantalla = "normal"
        return
    for i, m in enumerate(MISIONES):
        if mision_lista(m) and rect_boton_mision(i).collidepoint(posicion):
            reclamar_mision(m)
            crear_particulas("moneda", rect_boton_mision(i).center, 8)


# --- Ruleta de la suerte ---
RULETA_PREMIOS = [
    ("+5", "monedas", 5), ("+10", "monedas", 10), ("Comida", "comida", 1),
    ("+20", "monedas", 20), ("+10 XP", "xp", 10), ("+50", "monedas", 50),
    ("+15", "monedas", 15), ("+100", "monedas", 100),
]
RULETA_PESOS = [20, 18, 14, 12, 14, 5, 15, 2]
RULETA_COLORES = [(240, 120, 120), (250, 200, 90), (130, 200, 130), (120, 170, 240),
                  (200, 140, 230), (250, 160, 100), (110, 210, 200), (250, 220, 70)]
COSTO_RULETA_EXTRA = 10
RULETA_CENTRO = (400, 320)
RULETA_RADIO = 150
boton_girar = pygame.Rect(300, 525, 200, 50)
ruleta = {"estado": "quieta", "ang": 0.0, "ini": 0.0, "fin": 0.0,
          "t0": 0, "dur": 4200, "idx": 0}


def ruleta_gratis():
    return ruleta_dia != hoy()


def girar_ruleta():
    global monedas, ruleta_dia
    if ruleta["estado"] == "girando":
        return
    if ruleta_gratis():
        ruleta_dia = hoy()
    elif monedas >= COSTO_RULETA_EXTRA:
        monedas -= COSTO_RULETA_EXTRA
    else:
        avisar("No te alcanzan las monedas")
        sonar("error")
        return
    idx = random.choices(range(len(RULETA_PREMIOS)), RULETA_PESOS)[0]
    objetivo = (-(idx * 45 + 22.5)) % 360
    ini = ruleta["ang"] % 360
    ruleta.update(estado="girando", ini=ini, idx=idx, t0=pygame.time.get_ticks(),
                  fin=ini + ((objetivo - ini) % 360) + 360 * random.randint(4, 6))
    guardar()


def actualizar_ruleta(ahora):
    global monedas
    if ruleta["estado"] != "girando":
        return
    t = (ahora - ruleta["t0"]) / ruleta["dur"]
    if t < 1:
        ruleta["ang"] = ruleta["ini"] + (ruleta["fin"] - ruleta["ini"]) * (1 - (1 - t) ** 3)
        return
    ruleta["ang"] = ruleta["fin"]
    ruleta["estado"] = "quieta"
    etiqueta, tipo, valor = RULETA_PREMIOS[ruleta["idx"]]
    if tipo == "monedas":
        monedas += valor
        avisar(f"¡Ruleta! +{valor} monedas")
    elif tipo == "comida":
        nombre = random.choice(COMIDAS)[0]
        inventario[nombre] += valor
        avisar(f"¡Ruleta! Ganaste {nombre}")
    else:
        avisar(f"¡Ruleta! +{valor} XP")
        ganar_xp(valor)
    stats["ruleta"] += 1
    sonar("moneda")
    crear_particulas("estrella", RULETA_CENTRO, 12)
    crear_particulas("moneda", RULETA_CENTRO, 6)
    guardar()


def _punto_circ(centro, radio, grados):
    a = math.radians(grados)
    return (centro[0] + radio * math.sin(a), centro[1] - radio * math.cos(a))


def dibujar_ruleta(ventana):
    ventana.fill((200, 220, 240))
    t = fuente_grande.render("RULETA DE LA SUERTE", True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 85))
    sub = "¡Giro gratis disponible hoy!" if ruleta_gratis() else \
        f"Giro extra: {COSTO_RULETA_EXTRA} monedas"
    s = fuente_numero.render(sub, True, (0, 0, 0))
    ventana.blit(s, s.get_rect(center=(400, 122)))

    cx, cy = RULETA_CENTRO
    n = len(RULETA_PREMIOS)
    for i, (etiqueta, _, _) in enumerate(RULETA_PREMIOS):
        a0 = ruleta["ang"] + i * 45
        puntos = [RULETA_CENTRO]
        for k in range(0, 10):
            puntos.append(_punto_circ(RULETA_CENTRO, RULETA_RADIO, a0 + 45 * k / 9))
        pygame.draw.polygon(ventana, RULETA_COLORES[i % len(RULETA_COLORES)], puntos)
        pygame.draw.polygon(ventana, (60, 40, 30), puntos, 2)
        pos = _punto_circ(RULETA_CENTRO, RULETA_RADIO * 0.66, a0 + 22.5)
        txt = fuente.render(etiqueta, True, (40, 30, 30))
        ventana.blit(txt, txt.get_rect(center=(int(pos[0]), int(pos[1]))))
    pygame.draw.circle(ventana, (60, 40, 30), RULETA_CENTRO, RULETA_RADIO, 4)
    pygame.draw.circle(ventana, (255, 255, 255), RULETA_CENTRO, 14)
    pygame.draw.circle(ventana, (60, 40, 30), RULETA_CENTRO, 14, 3)
    # puntero
    pygame.draw.polygon(ventana, (220, 40, 60),
                        [(cx - 14, cy - RULETA_RADIO - 18), (cx + 14, cy - RULETA_RADIO - 18),
                         (cx, cy - RULETA_RADIO + 10)])
    pygame.draw.polygon(ventana, (0, 0, 0),
                        [(cx - 14, cy - RULETA_RADIO - 18), (cx + 14, cy - RULETA_RADIO - 18),
                         (cx, cy - RULETA_RADIO + 10)], 2)

    if ruleta["estado"] != "girando":
        dibujar_boton(ventana, boton_girar, "¡Girar!")
    dibujar_boton(ventana, boton_volver, "Volver")


def click_ruleta(posicion):
    global subpantalla
    if boton_volver.collidepoint(posicion):
        subpantalla = "normal"
    elif boton_girar.collidepoint(posicion):
        girar_ruleta()


# --- Jardín ---
def _progreso_parcela(parcela):
    tiempo = CULTIVOS[parcela["cultivo"]]["tiempo"]
    return max(0.0, min(1.0, (time.time() - parcela["inicio"]) / tiempo))


def usar_parcela(i, posicion):
    global monedas
    parcela = huerta[i]
    if parcela is None:
        datos = CULTIVOS[cultivo_elegido]
        if monedas < datos["semilla"]:
            avisar("No te alcanzan las monedas")
            sonar("error")
            return
        monedas -= datos["semilla"]
        huerta[i] = {"cultivo": cultivo_elegido, "inicio": time.time(), "regada": False}
        avisar(f"Plantaste {cultivo_elegido}")
        crear_particulas("estrella", posicion, 4)
        guardar()
        return

    datos = CULTIVOS[parcela["cultivo"]]
    prog = _progreso_parcela(parcela)
    if prog >= 1:
        cosecha = datos["cosecha"]
        inventario[parcela["cultivo"]] += cosecha
        huerta[i] = None
        progreso_mision("cosechar")
        stats["cosechas"] += 1
        ganar_xp(8)
        avisar(f"Cosechaste {cosecha} {parcela['cultivo']}")
        sonar("moneda")
        crear_particulas("estrella", posicion, 8)
        guardar()
    elif not parcela["regada"]:
        parcela["regada"] = True
        parcela["inicio"] -= datos["tiempo"] * 0.4
        avisar("¡Regaste la planta! Crece más rápido")
        crear_particulas("burbuja", posicion, 8)
        guardar()
    else:
        faltan = int(datos["tiempo"] * (1 - prog)) + 1
        avisar(f"Faltan {faltan} segundos")


def dibujar_planta(ventana, rect, prog, cultivo, ahora):
    cx, base = rect.centerx, rect.bottom - 18
    verde, verde_claro = (60, 150, 60), (80, 195, 80)
    if prog < 0.34:
        pygame.draw.circle(ventana, (70, 170, 70), (cx, base - 6), 6)
    elif prog < 0.67:
        pygame.draw.line(ventana, verde, (cx, base), (cx, base - 35), 4)
        pygame.draw.ellipse(ventana, verde_claro, (cx - 18, base - 38, 18, 10))
        pygame.draw.ellipse(ventana, verde_claro, (cx, base - 30, 18, 10))
    elif prog < 1:
        pygame.draw.line(ventana, verde, (cx, base), (cx, base - 55), 5)
        pygame.draw.ellipse(ventana, verde_claro, (cx - 26, base - 58, 26, 14))
        pygame.draw.ellipse(ventana, verde_claro, (cx, base - 46, 26, 14))
        pygame.draw.ellipse(ventana, verde_claro, (cx - 22, base - 34, 22, 12))
    else:
        salto = int(math.sin(ahora / 200) * 4)
        dibujar_comida(ventana, cultivo, (cx, rect.centery - 8 + salto), imagenes_comidas, 28)
        lista = fuente_numero.render("¡Lista!", True, (255, 255, 255))
        ventana.blit(lista, lista.get_rect(center=(cx, rect.y + 12)))


def dibujar_jardin(ventana, ahora):
    for i, rect in enumerate(parcelas):
        pygame.draw.rect(ventana, (110, 75, 45), rect, border_radius=10)
        pygame.draw.rect(ventana, (60, 40, 25), rect, 3, border_radius=10)
        parcela = huerta[i]
        if parcela is None:
            t = fuente.render("Plantar", True, (255, 255, 255))
            ventana.blit(t, t.get_rect(center=(rect.centerx, rect.centery - 8)))
            semilla = CULTIVOS[cultivo_elegido]["semilla"]
            c = fuente_numero.render(f"({semilla} moneda{'s' if semilla != 1 else ''})",
                                     True, (230, 210, 180))
            ventana.blit(c, c.get_rect(center=(rect.centerx, rect.centery + 14)))
        else:
            prog = _progreso_parcela(parcela)
            dibujar_planta(ventana, rect, prog, parcela["cultivo"], ahora)
            barra = pygame.Rect(rect.x, rect.bottom + 4, rect.width, 6)
            pygame.draw.rect(ventana, (220, 220, 220), barra)
            pygame.draw.rect(ventana, (100, 200, 100),
                             (barra.x, barra.y, int(barra.width * prog), barra.height))
            pygame.draw.rect(ventana, (0, 0, 0), barra, 1)
            if parcela["regada"]:
                pygame.draw.circle(ventana, (90, 160, 255), (rect.right - 14, rect.y + 14), 6)

    dibujar_boton(ventana, boton_semilla, f"Semilla: {cultivo_elegido}")
    ayuda = fuente_numero.render("Toca una parcela: planta, riega o cosecha", True, (0, 0, 0))
    ventana.blit(ayuda, ayuda.get_rect(center=(520, 145)))


# --- Regalos sorpresa ---
DURACION_REGALO = 8000
regalo = None
proximo_regalo = pygame.time.get_ticks() + random.randint(45000, 90000)


def rect_regalo():
    return pygame.Rect(regalo["x"] - 24, regalo["y"] - 24, 48, 48)


def actualizar_regalo(ahora):
    global regalo, proximo_regalo
    if regalo is None:
        if ahora >= proximo_regalo:
            regalo = {"x": random.randint(100, 700), "y": random.randint(210, 420), "nace": ahora}
    elif ahora - regalo["nace"] > DURACION_REGALO:
        regalo = None
        proximo_regalo = ahora + random.randint(45000, 90000)


def abrir_regalo():
    global regalo, proximo_regalo, monedas
    pos = (regalo["x"], regalo["y"])
    if random.random() < 0.6:
        premio = random.randint(10, 30)
        monedas += premio
        avisar(f"¡Regalo! +{premio} monedas")
    else:
        nombre = random.choice(COMIDAS)[0]
        inventario[nombre] += 1
        avisar(f"¡Regalo! Te dieron {nombre}")
    crear_particulas("estrella", pos, 10)
    crear_particulas("moneda", pos, 4)
    sonar("moneda")
    stats["regalos"] += 1
    ganar_xp(3)
    guardar()
    regalo = None
    proximo_regalo = pygame.time.get_ticks() + random.randint(45000, 90000)


def dibujar_regalo(ventana, ahora):
    if regalo is None:
        return
    restante = DURACION_REGALO - (ahora - regalo["nace"])
    if restante < 2500 and (ahora // 150) % 2 == 0:
        return
    r = rect_regalo().move(0, int(math.sin(ahora / 180) * 5))
    pygame.draw.rect(ventana, (230, 70, 90), r, border_radius=6)
    pygame.draw.rect(ventana, (255, 220, 80), (r.centerx - 5, r.y, 10, r.height))
    pygame.draw.rect(ventana, (255, 220, 80), (r.x, r.centery - 5, r.width, 10))
    pygame.draw.circle(ventana, (255, 220, 80), (r.centerx - 8, r.y - 3), 7)
    pygame.draw.circle(ventana, (255, 220, 80), (r.centerx + 8, r.y - 3), 7)
    pygame.draw.rect(ventana, (0, 0, 0), r, 2, border_radius=6)


# ---------------------------------------------------------------------------
# DESMAYO / REVIVIR
# ---------------------------------------------------------------------------
def _desmayar():
    global muerta, subpantalla, modo_noche, minijuego, arrastrando
    muerta = True
    subpantalla = "normal"
    modo_noche = False
    minijuego = None
    arrastrando = None


def revivir():
    global baño, comer, dormir, jugar, monedas, muerta
    costo = monedas // 4
    monedas -= costo
    baño = comer = dormir = jugar = 50
    muerta = False
    guardar()
    avisar(f"Pau revivió (-{costo} monedas)")
    crear_particulas("corazon", (400, 300), 10)


def dibujar_muerte(ventana):
    ventana.blit(VELO_MUERTE, (0, 0))

    panel = pygame.Rect(0, 0, 440, 230)
    panel.center = (400, 300)
    pygame.draw.rect(ventana, (255, 255, 255), panel, border_radius=12)
    pygame.draw.rect(ventana, (0, 0, 0), panel, 3, border_radius=12)

    lineas = [
        (fuente_grande, "¡Pau se desmayó!", 225),
        (fuente, "Descuidaste sus necesidades.", 265),
        (fuente_numero, f"Revivir cuesta {monedas // 4} monedas", 300),
    ]
    for f, texto, y in lineas:
        s = f.render(texto, True, (0, 0, 0))
        ventana.blit(s, s.get_rect(center=(400, y)))
    dibujar_boton(ventana, boton_revivir, "Revivir (Enter)")


def reiniciar_progreso():
    """Borra TODO el progreso y empieza de cero."""
    global monedas, baño, comer, dormir, jugar, racha, xp, nivel, misiones_dia
    global ultimo_dia, ruleta_dia, muerta, modo_noche, subpantalla, minijuego
    global cultivo_elegido
    monedas = 100
    for k in inventario:
        inventario[k] = 0
    ropa_puesta.clear()
    ropa_comprada.clear()
    for k in records:
        records[k] = 0
    for k in stats:
        stats[k] = 0
    logros_hechos.clear()
    huerta[:] = [None] * len(huerta)
    baño = comer = dormir = jugar = 100
    racha, xp, nivel = 1, 0, 1
    misiones_dia = {"dia": hoy(), "progreso": {}, "reclamadas": []}
    ultimo_dia = hoy()
    ruleta_dia = ""
    muerta = modo_noche = False
    subpantalla = "normal"
    minijuego = None
    cultivo_elegido = "Manzana"
    cola_avisos.clear()
    guardar()


# ---------------------------------------------------------------------------
# MINIJUEGOS (integrados, sin bloquear el bucle principal)
# ---------------------------------------------------------------------------
MINIJUEGOS = [
    ("Flappy Pau", "flappy"),
    ("Atrapa comida", "atrapa"),
    ("Memoria", "memoria"),
    ("Reflejos", "reflejos"),
    ("Simón dice", "simon"),
]
NOMBRES_MJ = {"atrapa": "Atrapa comida", "memoria": "Memoria",
              "reflejos": "Reflejos", "simon": "Simón dice"}
AYUDA_MJ = {
    "atrapa": "Mouse o flechas para atrapar. ¡Evita la basura y busca lo dorado!",
    "memoria": "Encuentra los 6 pares con la menor cantidad de intentos.",
    "reflejos": "Haz click en los círculos... ¡si fallas pierdes un punto!",
    "simon": "",
}
SIMBOLOS = [(c[0], None) for c in COMIDAS[:4]] + [
    ("Corazón", (230, 60, 90)), ("Estrella", (250, 200, 40)),
]
COLORES_COMIDA = {
    "Manzana": (220, 50, 50), "Pizza": (240, 170, 60),
    "Sushi": (120, 170, 230), "Hamburguesa": (170, 110, 60),
    "Zanahoria": (240, 130, 40), "Helado": (250, 170, 200),
    "Dona": (220, 150, 190), "Sopa": (230, 120, 60),
    "Tacos": (240, 200, 80), "Sandía": (90, 190, 90),
    "Pastel": (250, 200, 220), "Pollo": (200, 140, 70),
}
COLORES_SIMON = [(220, 60, 60), (60, 180, 80), (70, 110, 230), (240, 200, 50)]


def lanzar_flappy():
    global monedas, jugar, subpantalla
    try:
        import Flappy_Pau
    except ImportError:
        avisar("No se encontró Flappy_Pau.py")
        return
    resultado = Flappy_Pau.ejecutar_flappy()
    subpantalla = "minijuegos"
    surf = pygame.display.get_surface()
    if surf is None or surf.get_size() != (ancho, alto):
        crear_ventana()           # por si el minijuego cambió la ventana
    if isinstance(resultado, int) and resultado > 0:
        monedas += resultado
        jugar = min(100, jugar + 20)
        progreso_mision("minijuegos")
        stats["minijuegos"] += 1
        ganar_xp(5 + resultado // 2)
        guardar()
        avisar(f"¡Ganaste {resultado} monedas!")
        sonar("moneda")


def iniciar_minijuego(clave):
    global minijuego, subpantalla
    mj = {"tipo": clave, "fin": False, "puntos": 0, "tiempo": 0.0,
          "recompensa": 0, "nuevo_record": False}
    if clave == "atrapa":
        mj.update(duracion=30.0, x=ancho / 2, items=[], spawn=0.5, combo=0)
    elif clave == "reflejos":
        mj.update(duracion=20.0, objetivo=None)
        _nuevo_objetivo(mj)
    elif clave == "memoria":
        simbolos = list(range(len(SIMBOLOS))) * 2
        random.shuffle(simbolos)
        mj.update(
            cartas=[{"sim": s, "vista": False, "hecha": False} for s in simbolos],
            elegidas=[], espera=0.0, intentos=0,
        )
    elif clave == "simon":
        mj.update(seq=[random.randint(0, 3)], fase="mostrar", paso=0,
                  reloj=0.8, brillo=-1, entrada=0)
    minijuego = mj
    subpantalla = "minijuego"


def terminar_minijuego(mj):
    global monedas, jugar
    mj["fin"] = True
    mj["recompensa"] = max(1, mj["puntos"] // 2) if mj["puntos"] > 0 else 0
    monedas += mj["recompensa"]
    jugar = min(100, jugar + 25)
    if mj["puntos"] > records.get(mj["tipo"], 0):
        records[mj["tipo"]] = mj["puntos"]
        mj["nuevo_record"] = mj["puntos"] > 0
    progreso_mision("minijuegos")
    stats["minijuegos"] += 1
    ganar_xp(5 + mj["puntos"] // 2)
    guardar()
    sonar("moneda")
    crear_particulas("moneda", (400, 300), 10)


# --- Atrapa comida (con combos y comida dorada) ---
def _multiplicador(mj):
    return min(3, 1 + mj["combo"] // 5)


def _actualizar_atrapa(mj, dt):
    teclas = pygame.key.get_pressed()
    mov = (teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) - (teclas[pygame.K_LEFT] or teclas[pygame.K_a])
    if mov:
        mj["x"] = max(45, min(ancho - 45, mj["x"] + mov * 520 * dt))

    mj["spawn"] -= dt
    if mj["spawn"] <= 0:
        mj["spawn"] = max(0.35, 0.9 - mj["tiempo"] * 0.02)
        r = random.random()
        if r < 0.22:
            tipo = "basura"
        elif r < 0.28:
            tipo = "dorada"
        else:
            tipo = random.choice(COMIDAS)[0]
        mj["items"].append({
            "x": random.randint(30, ancho - 30), "y": -30.0,
            "vy": random.uniform(160, 230) + mj["tiempo"] * 3,
            "tipo": tipo,
        })

    cesta = pygame.Rect(int(mj["x"]) - 40, 490, 80, 70)
    restantes = []
    for it in mj["items"]:
        it["y"] += it["vy"] * dt
        r = pygame.Rect(int(it["x"]) - 22, int(it["y"]) - 22, 44, 44)
        if r.colliderect(cesta):
            if it["tipo"] == "basura":
                mj["puntos"] = max(0, mj["puntos"] - 2)
                mj["combo"] = 0
                sonar("error")
                crear_particulas("burbuja", (it["x"], it["y"]), 3)
            elif it["tipo"] == "dorada":
                mj["combo"] += 1
                mj["puntos"] += 5 * _multiplicador(mj)
                sonar("moneda")
                crear_particulas("moneda", (it["x"], it["y"]), 6)
            else:
                mj["combo"] += 1
                mj["puntos"] += _multiplicador(mj)
                crear_particulas("estrella", (it["x"], it["y"]), 3)
        elif it["y"] < alto + 30:
            restantes.append(it)
        elif it["tipo"] not in ("basura",):
            mj["combo"] = 0          # se te cayó comida: se rompe el combo
    mj["items"] = restantes


def dibujar_comida(ventana, nombre, centro, imagenes, radio):
    img = imagenes.get(nombre)
    if img is not None:
        ventana.blit(img, img.get_rect(center=centro))
    else:
        pygame.draw.circle(ventana, COLORES_COMIDA.get(nombre, (150, 150, 150)), centro, radio)
        letra = fuente.render(nombre[0], True, (255, 255, 255))
        ventana.blit(letra, letra.get_rect(center=centro))


def _dibujar_atrapa(ventana, mj):
    pygame.draw.rect(ventana, (120, 190, 110), (0, 570, ancho, 30))
    for it in mj["items"]:
        centro = (int(it["x"]), int(it["y"]))
        if it["tipo"] == "basura":
            pygame.draw.circle(ventana, (110, 75, 40), centro, 22)
            pygame.draw.circle(ventana, (0, 0, 0), (centro[0] - 7, centro[1] - 4), 3)
            pygame.draw.circle(ventana, (0, 0, 0), (centro[0] + 7, centro[1] - 4), 3)
        elif it["tipo"] == "dorada":
            pygame.draw.circle(ventana, (255, 230, 120), centro, 26)
            dibujar_estrella(ventana, centro, 24, (255, 190, 0))
            pygame.draw.circle(ventana, (200, 140, 0), centro, 26, 2)
        else:
            dibujar_comida(ventana, it["tipo"], centro, imgs_caida, 22)
    ventana.blit(img_cesta, img_cesta.get_rect(midbottom=(int(mj["x"]), 570)))


# --- Reflejos ---
def _nuevo_objetivo(mj):
    mj["objetivo"] = {
        "x": random.randint(70, ancho - 70),
        "y": random.randint(150, alto - 70),
        "edad": 0.0,
    }


def _vida_objetivo(mj):
    return max(0.55, 1.5 - 0.04 * mj["puntos"])


def _radio_objetivo(mj):
    return 12 + 36 * (1 - mj["objetivo"]["edad"] / _vida_objetivo(mj))


def _actualizar_reflejos(mj, dt):
    mj["objetivo"]["edad"] += dt
    if mj["objetivo"]["edad"] >= _vida_objetivo(mj):
        _nuevo_objetivo(mj)


def _dibujar_reflejos(ventana, mj):
    o = mj["objetivo"]
    centro = (o["x"], o["y"])
    r = int(max(4, _radio_objetivo(mj)))
    pygame.draw.circle(ventana, (230, 70, 70), centro, r)
    pygame.draw.circle(ventana, (255, 255, 255), centro, max(2, r // 2))
    pygame.draw.circle(ventana, (230, 70, 70), centro, max(1, r // 5))
    pygame.draw.circle(ventana, (0, 0, 0), centro, r, 2)


# --- Memoria ---
def rect_carta(i):
    return pygame.Rect(150 + (i % 4) * 130, 130 + (i // 4) * 135, 110, 120)


def dibujar_simbolo(ventana, idx, centro):
    nombre, color = SIMBOLOS[idx]
    if nombre == "Corazón":
        dibujar_corazon(ventana, centro, 30, color)
    elif nombre == "Estrella":
        dibujar_estrella(ventana, centro, 34, color)
    else:
        dibujar_comida(ventana, nombre, centro, imagenes_comidas, 32)


def _dibujar_memoria(ventana, mj):
    for i, c in enumerate(mj["cartas"]):
        rect = rect_carta(i)
        if c["vista"] or c["hecha"]:
            pygame.draw.rect(ventana, (255, 255, 255), rect, border_radius=10)
            dibujar_simbolo(ventana, c["sim"], rect.center)
            borde = (0, 160, 0) if c["hecha"] else (0, 0, 0)
            pygame.draw.rect(ventana, borde, rect, 4 if c["hecha"] else 2, border_radius=10)
        else:
            pygame.draw.rect(ventana, (120, 150, 220), rect, border_radius=10)
            pygame.draw.rect(ventana, (0, 0, 0), rect, 2, border_radius=10)
            q = fuente_grande.render("?", True, (255, 255, 255))
            ventana.blit(q, q.get_rect(center=rect.center))


def _click_memoria(mj, pos):
    if mj["espera"] > 0:
        return
    for i, c in enumerate(mj["cartas"]):
        if rect_carta(i).collidepoint(pos) and not c["vista"] and not c["hecha"]:
            c["vista"] = True
            mj["elegidas"].append(i)
            if len(mj["elegidas"]) == 2:
                mj["intentos"] += 1
                a, b = mj["elegidas"]
                if mj["cartas"][a]["sim"] == mj["cartas"][b]["sim"]:
                    mj["cartas"][a]["hecha"] = mj["cartas"][b]["hecha"] = True
                    mj["elegidas"] = []
                    crear_particulas("estrella", rect_carta(a).center, 4)
                    crear_particulas("estrella", rect_carta(b).center, 4)
                    if all(k["hecha"] for k in mj["cartas"]):
                        mj["puntos"] = max(2, 20 - 2 * (mj["intentos"] - len(SIMBOLOS)))
                        terminar_minijuego(mj)
                else:
                    mj["espera"] = 0.8
            return


# --- Simón dice ---
def rect_pad(i):
    return pygame.Rect(250 + (i % 2) * 150, 150 + (i // 2) * 150, 140, 140)


def _actualizar_simon(mj, dt):
    mj["reloj"] -= dt
    if mj["fase"] == "mostrar":
        if mj["reloj"] <= 0:
            if mj["brillo"] != -1:
                mj["brillo"] = -1
                mj["reloj"] = 0.2
            elif mj["paso"] < len(mj["seq"]):
                mj["brillo"] = mj["seq"][mj["paso"]]
                mj["paso"] += 1
                mj["reloj"] = 0.45
                sonar("click")
            else:
                mj["fase"] = "esperar"
                mj["entrada"] = 0
    elif mj["brillo"] != -1 and mj["reloj"] <= 0:
        mj["brillo"] = -1


def _click_simon(mj, pos):
    if mj["fase"] != "esperar":
        return
    for i in range(4):
        if rect_pad(i).collidepoint(pos):
            mj["brillo"] = i
            mj["reloj"] = 0.2
            sonar("click")
            if i == mj["seq"][mj["entrada"]]:
                mj["entrada"] += 1
                if mj["entrada"] == len(mj["seq"]):
                    mj["puntos"] = len(mj["seq"])
                    mj["seq"].append(random.randint(0, 3))
                    mj["fase"] = "mostrar"
                    mj["paso"] = 0
                    mj["brillo"] = -1
                    mj["reloj"] = 0.9
                    crear_particulas("estrella", rect_pad(i).center, 4)
            else:
                sonar("error")
                terminar_minijuego(mj)
            return


def _dibujar_simon(ventana, mj):
    for i in range(4):
        base = COLORES_SIMON[i]
        if i == mj["brillo"]:
            color = tuple(min(255, c + 70) for c in base)
        else:
            color = tuple(int(c * 0.55) for c in base)
        r = rect_pad(i)
        pygame.draw.rect(ventana, color, r, border_radius=18)
        pygame.draw.rect(ventana, (0, 0, 0), r, 3, border_radius=18)


# --- Control general de minijuegos ---
def actualizar_minijuego(dt):
    mj = minijuego
    if mj is None or mj["fin"]:
        return
    if mj["tipo"] == "memoria":
        if mj["espera"] > 0:
            mj["espera"] -= dt
            if mj["espera"] <= 0:
                for i in mj["elegidas"]:
                    mj["cartas"][i]["vista"] = False
                mj["elegidas"] = []
        return
    if mj["tipo"] == "simon":
        _actualizar_simon(mj, dt)
        return

    mj["tiempo"] += dt
    if mj["tiempo"] >= mj["duracion"]:
        terminar_minijuego(mj)
        return
    if mj["tipo"] == "atrapa":
        _actualizar_atrapa(mj, dt)
    elif mj["tipo"] == "reflejos":
        _actualizar_reflejos(mj, dt)


def click_minijuego(pos):
    global minijuego, subpantalla
    mj = minijuego
    if mj is None:
        subpantalla = "minijuegos"
        return
    if boton_volver.collidepoint(pos):
        minijuego = None
        subpantalla = "minijuegos"
        return
    if mj["fin"]:
        if boton_reintentar.collidepoint(pos):
            iniciar_minijuego(mj["tipo"])
        return

    if mj["tipo"] == "atrapa":
        movimiento_minijuego(pos)
    elif mj["tipo"] == "memoria":
        _click_memoria(mj, pos)
    elif mj["tipo"] == "simon":
        _click_simon(mj, pos)
    elif mj["tipo"] == "reflejos":
        o = mj["objetivo"]
        if math.hypot(pos[0] - o["x"], pos[1] - o["y"]) <= _radio_objetivo(mj) + 6:
            mj["puntos"] += 1
            sonar("click")
            crear_particulas("estrella", (o["x"], o["y"]), 4)
            _nuevo_objetivo(mj)
        else:
            mj["puntos"] = max(0, mj["puntos"] - 1)
            sonar("error")
            crear_particulas("burbuja", pos, 2)


def movimiento_minijuego(pos):
    mj = minijuego
    if mj is not None and mj["tipo"] == "atrapa" and not mj["fin"]:
        mj["x"] = max(45, min(ancho - 45, pos[0]))


def dibujar_minijuego(ventana):
    mj = minijuego
    tipo = mj["tipo"]
    ventana.fill((200, 225, 245))

    t = fuente_grande.render(NOMBRES_MJ[tipo].upper(), True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 20))
    dibujar_boton(ventana, boton_volver, "Volver" if mj["fin"] else "Salir")

    if tipo == "atrapa":
        _dibujar_atrapa(ventana, mj)
    elif tipo == "memoria":
        _dibujar_memoria(ventana, mj)
    elif tipo == "reflejos":
        _dibujar_reflejos(ventana, mj)
    elif tipo == "simon":
        _dibujar_simon(ventana, mj)

    if tipo == "memoria":
        pares = sum(1 for c in mj["cartas"] if c["hecha"]) // 2
        info = f"Intentos: {mj['intentos']}     Pares: {pares}/{len(SIMBOLOS)}"
    elif tipo == "simon":
        info = f"Ronda: {len(mj['seq'])}     Puntos: {mj['puntos']}"
    elif tipo == "atrapa":
        restante = max(0, int(mj["duracion"] - mj["tiempo"]) + (0 if mj["fin"] else 1))
        info = f"Tiempo: {restante}     Puntos: {mj['puntos']}     Combo x{_multiplicador(mj)}"
    else:
        restante = max(0, int(mj["duracion"] - mj["tiempo"]) + (0 if mj["fin"] else 1))
        info = f"Tiempo: {restante}     Puntos: {mj['puntos']}"
    s = fuente.render(info, True, (0, 0, 0))
    ventana.blit(s, s.get_rect(center=(ancho // 2, 68)))

    ayuda = AYUDA_MJ[tipo]
    if tipo == "simon" and not mj["fin"]:
        ayuda = "Memoriza la secuencia..." if mj["fase"] == "mostrar" else "¡Tu turno! Repítela."
    a = fuente_numero.render(ayuda, True, (60, 60, 60))
    ventana.blit(a, a.get_rect(center=(ancho // 2, 94)))

    if mj["fin"]:
        panel = pygame.Rect(200, 170, 400, 250)
        pygame.draw.rect(ventana, (255, 255, 255), panel, border_radius=12)
        pygame.draw.rect(ventana, (0, 0, 0), panel, 3, border_radius=12)
        if tipo == "memoria":
            titulo = "¡Completado!"
        elif tipo == "simon":
            titulo = "¡Fallaste!"
        else:
            titulo = "¡Se acabó el tiempo!"
        lineas = [
            (fuente_grande, titulo, 205),
            (fuente, f"Puntos: {mj['puntos']}", 250),
            (fuente, f"Monedas ganadas: +{mj['recompensa']}", 282),
            (fuente, "¡Nuevo récord!" if mj["nuevo_record"]
             else f"Récord: {records.get(tipo, 0)}", 314),
        ]
        for f, texto, y in lineas:
            r = f.render(texto, True, (0, 0, 0))
            ventana.blit(r, r.get_rect(center=(400, y)))
        dibujar_boton(ventana, boton_reintentar, "Jugar otra vez")

    dibujar_monedas(ventana)


# ---------------------------------------------------------------------------
# INTERACCIÓN
# ---------------------------------------------------------------------------
FRASES_CARICIA = ["¡Me encanta!", "¡Qué rico!", "¡Más, más!", "¡Te quiero!",
                  "Jijiji...", "¡Eres la mejor!", "¡Qué cosquillas!"]


def acariciar(posicion):
    global jugar, ultima_caricia
    ahora = pygame.time.get_ticks()
    if ahora - ultima_caricia < 350:
        return
    ultima_caricia = ahora
    jugar = min(100, jugar + 1)
    stats["caricias"] += 1
    progreso_mision("caricias")
    crear_particulas("corazon", posicion, 3)
    if stats["caricias"] % 6 == 0:
        pau_dice(random.choice(FRASES_CARICIA))


def cambiar_habitacion(paso):
    global habitacion_actual, arrastrando
    arrastrando = None
    habitacion_actual = (habitacion_actual + paso) % len(nombres_habitaciones)


def manejar_click(posicion):
    global baño, comer, dormir, jugar
    global modo_noche, inicio_noche
    global subpantalla
    global monedas
    global arrastrando, pos_arrastre
    global pagina_armario, pestaña_tienda, cultivo_elegido

    if muerta:
        if boton_revivir.collidepoint(posicion):
            revivir()
        return

    if subpantalla == "minijuego":
        click_minijuego(posicion)
        return

    if subpantalla == "minijuegos":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        for i, b in enumerate(botones_minijuegos):
            if b.collidepoint(posicion):
                clave = MINIJUEGOS[i][1]
                if clave == "flappy":
                    lanzar_flappy()
                    return
                elif clave is not None:
                    iniciar_minijuego(clave)
                    return
                else:
                    avisar(f"Minijuego {i + 1} en desarrollo")
        return

    if subpantalla == "tienda":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        if boton_tab_comidas.collidepoint(posicion):
            pestaña_tienda = "comidas"
            pagina_armario = 0
            return
        if boton_tab_ropa.collidepoint(posicion):
            pestaña_tienda = "ropa"
            pagina_armario = 0
            return

        if pestaña_tienda == "comidas":
            if manejar_paginacion(posicion, len(COMIDAS)):
                return
            for i, (nombre, _, precio, _) in enumerate(prendas_de_pagina(COMIDAS)):
                if rect_tarjeta_comida(i, Y_TIENDA).collidepoint(posicion):
                    if monedas >= precio:
                        monedas -= precio
                        inventario[nombre] += 1
                        guardar()
                        avisar(f"Compraste {nombre}")
                        sonar("moneda")
                        crear_particulas("moneda", posicion, 5)
                    else:
                        avisar("No te alcanzan las monedas")
                        sonar("error")
        else:
            if manejar_paginacion(posicion, len(PRENDAS)):
                return
            for i, prenda in enumerate(prendas_de_pagina(PRENDAS)):
                if rect_tarjeta_ropa(i, Y_TIENDA).collidepoint(posicion):
                    if comprar_prenda(prenda):
                        crear_particulas("moneda", posicion, 6)
        return

    if subpantalla == "comidas":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        if manejar_paginacion(posicion, len(COMIDAS)):
            return
        for i, (nombre, _, _, valor) in enumerate(prendas_de_pagina(COMIDAS)):
            if rect_tarjeta_comida(i, Y_ARMARIO).collidepoint(posicion):
                if comer >= 100:
                    avisar("Pau no tiene hambre")
                elif inventario[nombre] > 0:
                    inventario[nombre] -= 1
                    comer = min(100, comer + valor)
                    aplicar_efectos(nombre)
                    progreso_mision("comer")
                    stats["comidas"] += 1
                    ganar_xp(4)
                    guardar()
                    sonar("comer")
                    pau_dice("¡Ñam ñam!")
                    crear_particulas("estrella", posicion, 6)
                else:
                    avisar(f"No tienes {nombre}")
                    sonar("error")
        return

    if subpantalla == "armario":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        if boton_quitar_ropa.collidepoint(posicion):
            ropa_puesta.clear()
            guardar()
            avisar("Pau no lleva ropa")
            return

        lista = prendas_poseidas()
        if manejar_paginacion(posicion, len(lista)):
            return
        for i, prenda in enumerate(prendas_de_pagina(lista)):
            if rect_tarjeta_ropa(i, Y_ARMARIO).collidepoint(posicion):
                alternar_prenda(prenda)
                crear_particulas("estrella", posicion, 5)
        return

    if subpantalla == "misiones":
        click_misiones(posicion)
        return

    if subpantalla == "logros":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
        return

    if subpantalla == "ruleta":
        click_ruleta(posicion)
        return

    # Regalo sorpresa
    if regalo is not None and rect_regalo().collidepoint(posicion):
        abrir_regalo()
        return

    # Mientras Pau duerme no se puede cambiar de habitación
    if not modo_noche:
        if flecha_izquierda.collidepoint(posicion):
            cambiar_habitacion(-1)
            return
        elif flecha_derecha.collidepoint(posicion):
            cambiar_habitacion(1)
            return

    if habitacion_actual == 0:
        for i, (rect, _, _) in enumerate(objetos_bano):
            if i == fase_bano and rect.collidepoint(posicion):
                arrastrando = i
                pos_arrastre = posicion

    elif habitacion_actual == 1:
        if boton_minijuegos.collidepoint(posicion):
            subpantalla = "minijuegos"
        elif boton_tienda.collidepoint(posicion):
            pestaña_tienda = "comidas"
            pagina_armario = 0
            subpantalla = "tienda"
        elif boton_ruleta.collidepoint(posicion):
            subpantalla = "ruleta"
        elif boton_misiones.collidepoint(posicion):
            subpantalla = "misiones"
        elif boton_logros.collidepoint(posicion):
            subpantalla = "logros"

    elif habitacion_actual == 2:
        if objeto_almohada.collidepoint(posicion) and not modo_noche:
            modo_noche = True
            inicio_noche = pygame.time.get_ticks()
            progreso_mision("dormir")
            ganar_xp(5)
        elif boton_armario.collidepoint(posicion) and not modo_noche:
            pagina_armario = 0
            subpantalla = "armario"

    elif habitacion_actual == 3:
        if boton_comidas.collidepoint(posicion):
            pagina_armario = 0
            subpantalla = "comidas"

    elif habitacion_actual == 4:
        if boton_semilla.collidepoint(posicion):
            claves = list(CULTIVOS)
            cultivo_elegido = claves[(claves.index(cultivo_elegido) + 1) % len(claves)]
        else:
            for i, rect in enumerate(parcelas):
                if rect.collidepoint(posicion):
                    usar_parcela(i, posicion)

    # Caricias: click sobre Pau (fuera del baño y sin que duerma)
    if (subpantalla == "normal" and habitacion_actual != 0 and not modo_noche
            and zona_pou.collidepoint(posicion)):
        acariciar(posicion)


def manejar_movimiento(pos):
    global pos_arrastre, arrastrando, fase_bano, baño

    if subpantalla == "minijuego":
        movimiento_minijuego(pos)
        return

    if arrastrando is None:
        return

    dist = min(40, math.hypot(pos[0] - pos_arrastre[0], pos[1] - pos_arrastre[1]))
    i = arrastrando

    if zona_pou.collidepoint(pos):
        progreso_bano[i] = min(100, progreso_bano[i] + dist * FACTORES_BANO[i])

        if progreso_bano[i] >= 100:
            arrastrando = None
            if i < 2:
                fase_bano += 1
            else:
                baño = 100
                fase_bano = 0
                progreso_bano[:] = [0.0, 0.0, 0.0]
                avisar("¡Pau está limpia!")
                pau_dice("¡Qué fresquita!")
                progreso_mision("banar")
                stats["banos"] += 1
                ganar_xp(10)
                crear_particulas("burbuja", zona_pou.center, 14)
                crear_particulas("estrella", zona_pou.center, 6)
            pos_arrastre = pos
            return

    pos_arrastre = pos


def manejar_soltar():
    global arrastrando
    arrastrando = None


def manejar_escape():
    """ESC dentro del juego. Devuelve True si cerró algo (submenú / minijuego)."""
    global subpantalla, minijuego
    if muerta:
        return False
    if subpantalla == "minijuego":
        minijuego = None
        subpantalla = "minijuegos"
        return True
    if subpantalla != "normal":
        subpantalla = "normal"
        return True
    return False


def manejar_tecla(tecla):
    if muerta:
        if tecla in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            revivir()
        return
    if subpantalla == "normal" and not modo_noche:
        if tecla in (pygame.K_LEFT, pygame.K_a):
            cambiar_habitacion(-1)
        elif tecla in (pygame.K_RIGHT, pygame.K_d):
            cambiar_habitacion(1)


def necesidades_pausadas():
    """True en cualquier minijuego: las barras se congelan por completo."""
    return subpantalla in SUBPANTALLAS_PAUSA


def actualizar_necesidades(dt):
    global baño, comer, dormir, jugar
    global acum_descenso, ultimo_incremento_dormir, modo_noche
    global ultimo_guardado, ultimo_chequeo_dia

    tiempo_actual = pygame.time.get_ticks()
    pausadas = necesidades_pausadas()

    # El descenso usa un acumulador (no marcas de tiempo): al pausar solo se
    # deja de sumar, así al volver no hay saltos ni bajadas de golpe.
    if not pausadas:
        acum_descenso += dt * 1000
        if acum_descenso >= TIEMPO_DISMINUCION:
            acum_descenso -= TIEMPO_DISMINUCION
            comer = max(0, comer - 1)
            jugar = max(0, jugar - 1)

            if not modo_noche:
                baño = max(0, baño - 1)
                dormir = max(0, dormir - 1)

    if modo_noche:
        if tiempo_actual - ultimo_incremento_dormir >= 100:
            dormir = min(100, dormir + 2)
            ultimo_incremento_dormir = tiempo_actual

        if tiempo_actual - inicio_noche >= DURACION_NOCHE:
            modo_noche = False

    if not pausadas and not muerta and min(baño, comer, dormir, jugar) <= 0:
        _desmayar()

    # ¿Cambió el día mientras jugabas? (pasada la medianoche)
    if tiempo_actual - ultimo_chequeo_dia >= 5000:
        ultimo_chequeo_dia = tiempo_actual
        if hoy() != ultimo_dia:
            _procesar_nuevo_dia(ultimo_dia)

    if tiempo_actual - ultimo_guardado >= INTERVALO_AUTOGUARDADO:
        guardar()
        ultimo_guardado = tiempo_actual


def principal():
    global ultimo_frame, ultimo_zzz, bonus_diario_pendiente, subpantalla
    ventana = pygame.display.get_surface()

    ahora = pygame.time.get_ticks()
    dt = min(0.05, (ahora - ultimo_frame) / 1000)
    ultimo_frame = ahora

    if bonus_diario_pendiente:
        avisar(f"¡Bonus diario! +{bonus_diario_pendiente} monedas (racha: {racha})")
        bonus_diario_pendiente = 0
        sonar("moneda")
        crear_particulas("moneda", (400, 300), 8)

    if subpantalla == "minijuego" and minijuego is None:
        subpantalla = "minijuegos"

    actualizar_necesidades(dt)
    actualizar_particulas(dt)
    actualizar_ruleta(ahora)
    revisar_logros()
    _procesar_avisos(ahora)
    if subpantalla == "minijuego":
        actualizar_minijuego(dt)
    if subpantalla == "normal" and not muerta and not modo_noche:
        actualizar_regalo(ahora)
    if modo_noche and ahora - ultimo_zzz > 700:
        ultimo_zzz = ahora
        crear_particulas("zzz", (450, 250), 1)

    if subpantalla == "minijuegos":
        ventana.fill((200, 220, 240))
        titulo = fuente_grande.render("SELECCIONA UN MINIJUEGO", True, (0, 0, 0))
        ventana.blit(titulo, (ancho // 2 - titulo.get_width() // 2, 80))

        for i, b in enumerate(botones_minijuegos):
            nombre, clave = MINIJUEGOS[i]
            dibujar_boton(ventana, b, nombre)
            if clave in records:
                rec = fuente_numero.render(f"Récord: {records[clave]}", True, (0, 0, 0))
                ventana.blit(rec, (b.right + 15, b.centery - rec.get_height() // 2))

        dibujar_boton(ventana, boton_volver, "Volver")
        dibujar_monedas(ventana)

    elif subpantalla == "minijuego" and minijuego is not None:
        dibujar_minijuego(ventana)

    elif subpantalla == "tienda":
        dibujar_tienda(ventana)
        dibujar_monedas(ventana)

    elif subpantalla == "comidas":
        dibujar_catalogo(ventana, "COMIDAS", "comidas")
        dibujar_monedas(ventana)

    elif subpantalla == "misiones":
        dibujar_misiones(ventana)
        dibujar_monedas(ventana)

    elif subpantalla == "logros":
        dibujar_logros(ventana)
        dibujar_monedas(ventana)

    elif subpantalla == "ruleta":
        dibujar_ruleta(ventana)
        dibujar_monedas(ventana)

    elif subpantalla == "armario":
        dibujar_armario(ventana)
        dibujar_monedas(ventana)

    else:
        fondos = [fondo_bano, fondo_sala, fondo_habitacion, fondo_cocina, fondo_jardin]
        ventana.blit(fondos[habitacion_actual], (0, 0))

        # Almohada sobre la mesa de luz (antes de la capa nocturna)
        if habitacion_actual == 2:
            dibujar_almohada_mesita(ventana)

        if modo_noche and habitacion_actual == 2:
            ventana.blit(VELO_NOCHE, (0, 0))

        if not modo_noche:
            dibujar_boton(ventana, flecha_izquierda, "<")
            dibujar_boton(ventana, flecha_derecha, ">")

        txt_hab = fuente_grande.render(nombres_habitaciones[habitacion_actual], True, (0, 0, 0))
        ventana.blit(txt_hab, (ancho // 2 - txt_hab.get_width() // 2, 10))

        if habitacion_actual == 0 or muerta:
            vaiven = 0
        elif modo_noche:
            vaiven = int(math.sin(ahora / 700) * 2)
        else:
            vaiven = int(math.sin(ahora / 350) * 4)
        centro_pou = (400, 320 + vaiven)

        personaje = obtener_personaje()
        ventana.blit(personaje, personaje.get_rect(center=centro_pou))
        if modo_noche:
            dibujar_suciedad(ventana, centro_pou)
        dibujar_ropa(ventana, centro_pou)

        if habitacion_actual == 0:
            dibujar_bano(ventana)

        elif habitacion_actual == 1:
            dibujar_boton(ventana, boton_minijuegos, "Minijuegos")
            dibujar_boton(ventana, boton_tienda, "Tienda")
            dibujar_boton(ventana, boton_ruleta, "Ruleta!" if ruleta_gratis() else "Ruleta")
            dibujar_boton(ventana, boton_misiones,
                          "Misiones!" if hay_mision_lista() else "Misiones")
            dibujar_boton(ventana, boton_logros, "Logros")

        elif habitacion_actual == 2:
            dibujar_objeto(ventana, objeto_almohada, img_almohada, "Dormir")
            if not modo_noche:
                dibujar_boton(ventana, boton_armario, "Armario")

        elif habitacion_actual == 3:
            dibujar_boton(ventana, boton_comidas, "Comidas")

        elif habitacion_actual == 4:
            dibujar_jardin(ventana, ahora)

        # Pau habla (reacciones) o avisa cuando necesita algo
        if habitacion_actual != 0 and not modo_noche and not muerta:
            if habla[0] and ahora < habla[1]:
                dibujar_burbuja_habla(ventana, habla[0], 400, 180)
            else:
                frase = frase_pau()
                if frase:
                    dibujar_burbuja_habla(ventana, frase, 400, 180)

        dibujar_regalo(ventana, ahora)
        dibujar_nivel(ventana)
        dibujar_barra(ventana, barra_baño, "BAÑO", baño)
        dibujar_barra(ventana, barra_comer, "COMER", comer)
        dibujar_barra(ventana, barra_dormir, "DORMIR", dormir)
        dibujar_barra(ventana, barra_jugar, "JUGAR", jugar)
        dibujar_monedas(ventana)

    dibujar_particulas(ventana)

    if muerta:
        dibujar_muerte(ventana)

    if mensaje_temporal and (ahora - tiempo_mensaje < DURACION_AVISO):
        txt_msg = fuente_grande.render(mensaje_temporal, True, (170, 0, 0))
        rect_msg = txt_msg.get_rect(center=(ancho // 2, alto // 2))
        pygame.draw.rect(ventana, (255, 255, 255), rect_msg.inflate(20, 10), border_radius=8)
        pygame.draw.rect(ventana, (0, 0, 0), rect_msg.inflate(20, 10), 2, border_radius=8)
        ventana.blit(txt_msg, rect_msg)