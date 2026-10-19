import pygame
import os
import sys
import json

# Carpeta donde está este archivo
ruta_actual = os.path.dirname(os.path.abspath(__file__))

# Agrega la carpeta de minijuegos al path
ruta_minijuegos = os.path.join(ruta_actual, "..", "minijuegos")
sys.path.append(os.path.normpath(ruta_minijuegos))

import Flappy_Pau

pygame.init()

ancho = 800
alto = 600

TIEMPO_DISMINUCION = 1000
DURACION_NOCHE = 3000

# ---------------------------------------------------------------
# BÚSQUEDA DE IMÁGENES
# Busca cada archivo en varias carpetas posibles (FONDOS, objetos...)
# ---------------------------------------------------------------
CARPETAS = [
    "", "FONDOS", "objetos", "personajes", "imagenes",
    "..", os.path.join("..", "FONDOS"), os.path.join("..", "objetos"),
]


def buscar_ruta(nombre):
    for carpeta in CARPETAS:
        ruta = os.path.normpath(os.path.join(ruta_actual, carpeta, nombre))
        if os.path.isfile(ruta):
            return ruta
    return None


def cargar_imagen(nombre, tamaño=None, maximo=None):
    """Carga una imagen. Devuelve None (y avisa en consola) si no la encuentra.
    tamaño=(w, h) estira; maximo=n la ajusta a n x n conservando proporción."""
    ruta = buscar_ruta(nombre)
    if ruta is None:
        print(f"[AVISO] No se encontró la imagen: {nombre}")
        return None
    try:
        img = pygame.image.load(ruta)
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
    img = cargar_imagen(nombre, tamaño=(ancho, alto))
    if img is None:
        img = pygame.Surface((ancho, alto))
        img.fill(color)
    return img


# ---------------------------------------------------------------
# DATOS GUARDADOS (monedas e inventario)
# ---------------------------------------------------------------
ARCHIVO_GUARDADO = os.path.join(ruta_actual, "guardado.json")

# Cada comida: (nombre, imagen, precio 3-10, puntos de comida que da)
COMIDAS = [
    ("Manzana", "manzana.png", 3, 10),
    ("Pizza", "pizza.png", 6, 20),
    ("Sushi", "sushi.png", 8, 25),
    ("Hamburguesa", "hamburguesa.png", 10, 30),
]

monedas = 100
inventario = {c[0]: 0 for c in COMIDAS}


def cargar_datos():
    global monedas, inventario
    if os.path.isfile(ARCHIVO_GUARDADO):
        try:
            with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as f:
                datos = json.load(f)
            monedas = int(datos.get("monedas", 100))
            for k, v in datos.get("inventario", {}).items():
                if k in inventario:
                    inventario[k] = int(v)
            return
        except (OSError, ValueError):
            pass
    # Primera vez que se abre el juego: 100 monedas
    monedas = 100
    guardar()


def guardar():
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as f:
            json.dump({"monedas": monedas, "inventario": inventario}, f)
    except OSError as e:
        print(f"[AVISO] No se pudo guardar: {e}")


cargar_datos()

# ---------------------------------------------------------------
# ESTADO DEL JUEGO
# ---------------------------------------------------------------
baño = 100
comer = 100
dormir = 100
jugar = 100

ultimo_descenso = pygame.time.get_ticks()
ultimo_incremento_dormir = pygame.time.get_ticks()
inicio_noche = 0
modo_noche = False

mensaje_temporal = ""
tiempo_mensaje = 0

habitacion_actual = 0
nombres_habitaciones = ["BAÑO", "SALA DE ESTAR", "HABITACIÓN", "COCINA"]

subpantalla = "normal"  # normal, minijuegos, tienda, comidas


def avisar(texto):
    global mensaje_temporal, tiempo_mensaje
    mensaje_temporal = texto
    tiempo_mensaje = pygame.time.get_ticks()


# ---------------------------------------------------------------
# IMÁGENES
# ---------------------------------------------------------------
fondo_bano = fondo_o_color("bano.png", (173, 216, 230))
fondo_sala = fondo_o_color("principal.png", (240, 230, 140))
fondo_habitacion = fondo_o_color("habitacion.png", (230, 230, 250))
fondo_cocina = fondo_o_color("cocina.png", (255, 218, 185))

TAMAÑO_POU = 220


def cargar_pou(nombre):
    img = cargar_imagen(nombre, maximo=TAMAÑO_POU)
    return img if img is not None else pou_base


pou_base = cargar_imagen("pou.png", maximo=TAMAÑO_POU)
if pou_base is None:
    pou_base = pygame.Surface((150, 150))
    pou_base.fill((139, 69, 19))

pou_feliz = cargar_pou("paufeliz.png")
pou_maso = cargar_pou("paumaso.png")
pou_popo = cargar_pou("poupopo.png")
pou_triste = cargar_pou("poutriste.png")
pou_muerto = cargar_pou("paumuerto.png")
pou_dormido = cargar_pou("poudormido.png")

TAMAÑO_OBJETO = 100
img_jabon = cargar_imagen("jabon.png", maximo=TAMAÑO_OBJETO)
img_ducha = cargar_imagen("ducha.png", maximo=TAMAÑO_OBJETO)
img_toalla = cargar_imagen("toalla.png", maximo=TAMAÑO_OBJETO)
img_almohada = cargar_imagen("almohada.png", maximo=TAMAÑO_OBJETO)

imagenes_comidas = {
    c[0]: cargar_imagen(c[1], maximo=90) for c in COMIDAS
}

fuente = pygame.font.Font(None, 28)
fuente_grande = pygame.font.Font(None, 36)
fuente_numero = pygame.font.Font(None, 22)

# ---------------------------------------------------------------
# RECTÁNGULOS
# ---------------------------------------------------------------
flecha_izquierda = pygame.Rect(10, 270, 50, 60)
flecha_derecha = pygame.Rect(740, 270, 50, 60)

# Objetos del baño (cada uno sube la higiene)
objeto_jabon = pygame.Rect(190, 450, 110, 110)
objeto_ducha = pygame.Rect(345, 450, 110, 110)
objeto_toalla = pygame.Rect(500, 450, 110, 110)
objetos_bano = [
    (objeto_jabon, img_jabon, "Jabón", 10),
    (objeto_ducha, img_ducha, "Ducha", 10),
    (objeto_toalla, img_toalla, "Toalla", 10),
]

# Almohada (reemplaza el botón de dormir)
objeto_almohada = pygame.Rect(345, 450, 110, 110)

boton_minijuegos = pygame.Rect(230, 480, 160, 50)
boton_tienda = pygame.Rect(410, 480, 160, 50)
boton_comidas = pygame.Rect(325, 480, 150, 50)

botones_minijuegos = [
    pygame.Rect(300, 150 + i * 65, 200, 45) for i in range(5)
]

boton_volver = pygame.Rect(20, 20, 100, 40)

# Tarjetas de comidas (tienda y cocina)
tarjetas_comidas = [
    pygame.Rect(70 + i * 170, 200, 150, 190) for i in range(len(COMIDAS))
]

pos_y_barras = 65
barra_baño = pygame.Rect(30, pos_y_barras, 170, 20)
barra_comer = pygame.Rect(220, pos_y_barras, 170, 20)
barra_dormir = pygame.Rect(410, pos_y_barras, 170, 20)
barra_jugar = pygame.Rect(600, pos_y_barras, 170, 20)


# ---------------------------------------------------------------
# DIBUJO
# ---------------------------------------------------------------
def dibujar_barra(ventana, rectangulo, nombre, valor):
    pygame.draw.rect(ventana, (220, 220, 220), rectangulo)
    ancho_barra = int(rectangulo.width * valor / 100)
    parte_llena = pygame.Rect(
        rectangulo.x, rectangulo.y, ancho_barra, rectangulo.height
    )
    pygame.draw.rect(ventana, (100, 200, 100), parte_llena)
    pygame.draw.rect(ventana, (0, 0, 0), rectangulo, 2)

    texto_nombre = fuente.render(nombre, True, (0, 0, 0))
    ventana.blit(
        texto_nombre,
        (rectangulo.centerx - texto_nombre.get_width() // 2, rectangulo.y - 22),
    )
    texto_numero = fuente_numero.render(str(valor), True, (0, 0, 0))
    ventana.blit(
        texto_numero,
        (rectangulo.centerx - texto_numero.get_width() // 2, rectangulo.bottom + 2),
    )


def dibujar_boton(ventana, rectangulo, texto):
    pygame.draw.rect(ventana, (255, 255, 255), rectangulo)
    pygame.draw.rect(ventana, (0, 0, 0), rectangulo, 2)
    texto_render = fuente.render(texto, True, (0, 0, 0))
    ventana.blit(texto_render, texto_render.get_rect(center=rectangulo.center))


def dibujar_objeto(ventana, rectangulo, imagen, texto):
    """Dibuja la imagen del objeto; si no existe, un botón con texto."""
    if imagen is None:
        dibujar_boton(ventana, rectangulo, texto)
    else:
        ventana.blit(imagen, imagen.get_rect(center=rectangulo.center))


def dibujar_monedas(ventana):
    txt = fuente_grande.render(f"Monedas: {monedas}", True, (0, 0, 0))
    ventana.blit(txt, (725 - txt.get_width(), 10))


def dibujar_catalogo(ventana, titulo, modo):
    ventana.fill((200, 220, 240))
    t = fuente_grande.render(titulo, True, (0, 0, 0))
    ventana.blit(t, (ancho // 2 - t.get_width() // 2, 100))

    for rect, comida in zip(tarjetas_comidas, COMIDAS):
        nombre, _, precio, _ = comida
        pygame.draw.rect(ventana, (255, 255, 255), rect)
        pygame.draw.rect(ventana, (0, 0, 0), rect, 2)

        img = imagenes_comidas[nombre]
        if img is not None:
            ventana.blit(img, img.get_rect(center=(rect.centerx, rect.y + 60)))

        n = fuente.render(nombre, True, (0, 0, 0))
        ventana.blit(n, (rect.centerx - n.get_width() // 2, rect.y + 115))

        if modo == "tienda":
            sub = f"{precio} monedas"
        else:
            sub = f"Tienes: {inventario[nombre]}"
        s = fuente_numero.render(sub, True, (0, 0, 0))
        ventana.blit(s, (rect.centerx - s.get_width() // 2, rect.y + 150))

    dibujar_boton(ventana, boton_volver, "Volver")


# ---------------------------------------------------------------
# ESTADO DE POU
# Regla: se usa la barra MÁS BAJA para decidir el aspecto.
#   0        -> muerto
#   1 - 30   -> triste
#   31 - 59  -> popo
#   60 - 79  -> maso
#   80 - 100 -> feliz
# Mientras duerme se muestra dormido; al terminar se recalcula solo.
# ---------------------------------------------------------------
def obtener_personaje():
    if modo_noche:
        return pou_dormido

    nivel = min(baño, comer, dormir, jugar)

    if nivel <= 0:
        return pou_muerto
    if nivel <= 30:
        return pou_triste
    if nivel < 60:
        return pou_popo
    if nivel < 80:
        return pou_maso
    return pou_feliz


# ---------------------------------------------------------------
# CLICKS
# ---------------------------------------------------------------
def manejar_click(posicion):
    global baño, comer, dormir, jugar
    global modo_noche, inicio_noche
    global habitacion_actual, subpantalla
    global monedas

    # MENÚ DE MINIJUEGOS
    if subpantalla == "minijuegos":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        for i, b in enumerate(botones_minijuegos):
            if b.collidepoint(posicion):
                if i == 0:
                    resultado = Flappy_Pau.ejecutar_flappy()
                    subpantalla = "minijuegos"

                    # Si el minijuego devuelve un número, son las monedas ganadas
                    if isinstance(resultado, int) and resultado > 0:
                        monedas += resultado
                        guardar()
                        avisar(f"¡Ganaste {resultado} monedas!")
                    return
                else:
                    avisar(f"Minijuego {i + 1} en desarrollo")
        return

    # TIENDA (comprar comidas)
    if subpantalla == "tienda":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        for rect, (nombre, _, precio, _) in zip(tarjetas_comidas, COMIDAS):
            if rect.collidepoint(posicion):
                if monedas >= precio:
                    monedas -= precio
                    inventario[nombre] += 1
                    guardar()
                    avisar(f"Compraste {nombre}")
                else:
                    avisar("No te alcanzan las monedas")
        return

    # COCINA (comer lo comprado)
    if subpantalla == "comidas":
        if boton_volver.collidepoint(posicion):
            subpantalla = "normal"
            return

        for rect, (nombre, _, _, valor) in zip(tarjetas_comidas, COMIDAS):
            if rect.collidepoint(posicion):
                if inventario[nombre] > 0:
                    inventario[nombre] -= 1
                    comer = min(100, comer + valor)
                    guardar()
                else:
                    avisar(f"No tienes {nombre}")
        return

    # CAMBIO DE HABITACIÓN
    if flecha_izquierda.collidepoint(posicion):
        habitacion_actual = (habitacion_actual - 1) % 4
        return
    elif flecha_derecha.collidepoint(posicion):
        habitacion_actual = (habitacion_actual + 1) % 4
        return

    # BAÑO
    if habitacion_actual == 0:
        for rect, _, _, subida in objetos_bano:
            if rect.collidepoint(posicion):
                baño = min(100, baño + subida)

    # SALA
    elif habitacion_actual == 1:
        if boton_minijuegos.collidepoint(posicion):
            subpantalla = "minijuegos"
        elif boton_tienda.collidepoint(posicion):
            subpantalla = "tienda"

    # HABITACIÓN
    elif habitacion_actual == 2:
        if objeto_almohada.collidepoint(posicion) and not modo_noche:
            modo_noche = True
            inicio_noche = pygame.time.get_ticks()

    # COCINA
    elif habitacion_actual == 3:
        if boton_comidas.collidepoint(posicion):
            subpantalla = "comidas"


# ---------------------------------------------------------------
# ACTUALIZACIÓN
# ---------------------------------------------------------------
def actualizar_necesidades():
    global baño, comer, dormir, jugar
    global ultimo_descenso, ultimo_incremento_dormir, modo_noche

    tiempo_actual = pygame.time.get_ticks()

    if tiempo_actual - ultimo_descenso >= TIEMPO_DISMINUCION:
        baño = max(0, baño - 1)
        comer = max(0, comer - 1)
        jugar = max(0, jugar - 1)

        if not modo_noche:
            dormir = max(0, dormir - 1)

        ultimo_descenso = tiempo_actual

    if modo_noche:
        if tiempo_actual - ultimo_incremento_dormir >= 100:
            dormir = min(100, dormir + 2)
            ultimo_incremento_dormir = tiempo_actual

        if tiempo_actual - inicio_noche >= DURACION_NOCHE:
            modo_noche = False


# ---------------------------------------------------------------
# PANTALLA PRINCIPAL
# ---------------------------------------------------------------
def principal():
    ventana = pygame.display.get_surface()

    actualizar_necesidades()

    if subpantalla == "minijuegos":
        ventana.fill((200, 220, 240))
        titulo = fuente_grande.render("SELECCIONA UN MINIJUEGO", True, (0, 0, 0))
        ventana.blit(titulo, (ancho // 2 - titulo.get_width() // 2, 80))

        for i, b in enumerate(botones_minijuegos):
            dibujar_boton(ventana, b, f"Minijuego {i + 1}")

        dibujar_boton(ventana, boton_volver, "Volver")
        dibujar_monedas(ventana)

    elif subpantalla == "tienda":
        dibujar_catalogo(ventana, "TIENDA DE COMIDAS", "tienda")
        dibujar_monedas(ventana)

    elif subpantalla == "comidas":
        dibujar_catalogo(ventana, "COMIDAS", "comidas")
        dibujar_monedas(ventana)

    else:
        fondos = [fondo_bano, fondo_sala, fondo_habitacion, fondo_cocina]
        ventana.blit(fondos[habitacion_actual], (0, 0))

        if modo_noche and habitacion_actual == 2:
            s = pygame.Surface((ancho, alto))
            s.set_alpha(180)
            s.fill((0, 0, 50))
            ventana.blit(s, (0, 0))

        dibujar_boton(ventana, flecha_izquierda, "<")
        dibujar_boton(ventana, flecha_derecha, ">")

        txt_hab = fuente_grande.render(
            nombres_habitaciones[habitacion_actual], True, (0, 0, 0)
        )
        ventana.blit(txt_hab, (ancho // 2 - txt_hab.get_width() // 2, 10))

        personaje = obtener_personaje()
        ventana.blit(personaje, personaje.get_rect(center=(400, 320)))

        if habitacion_actual == 0:
            for rect, img, texto, _ in objetos_bano:
                dibujar_objeto(ventana, rect, img, texto)

        elif habitacion_actual == 1:
            dibujar_boton(ventana, boton_minijuegos, "Minijuegos")
            dibujar_boton(ventana, boton_tienda, "Tienda")

        elif habitacion_actual == 2:
            dibujar_objeto(ventana, objeto_almohada, img_almohada, "Dormir")

        elif habitacion_actual == 3:
            dibujar_boton(ventana, boton_comidas, "Comidas")

        dibujar_barra(ventana, barra_baño, "BAÑO", baño)
        dibujar_barra(ventana, barra_comer, "COMER", comer)
        dibujar_barra(ventana, barra_dormir, "DORMIR", dormir)
        dibujar_barra(ventana, barra_jugar, "JUGAR", jugar)

        dibujar_monedas(ventana)

    # MENSAJE TEMPORAL
    if mensaje_temporal and (pygame.time.get_ticks() - tiempo_mensaje < 2000):
        txt_msg = fuente_grande.render(mensaje_temporal, True, (200, 0, 0))
        rect_msg = txt_msg.get_rect(center=(ancho // 2, alto // 2))
        pygame.draw.rect(ventana, (255, 255, 255), rect_msg.inflate(20, 10))
        pygame.draw.rect(ventana, (0, 0, 0), rect_msg.inflate(20, 10), 2)
        ventana.blit(txt_msg, rect_msg)