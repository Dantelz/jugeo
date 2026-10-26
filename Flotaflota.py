import pygame
import os
import random

def encontrar_archivo(nombre):
    carpeta_raiz = os.path.dirname(__file__)
    archivo = os.path.join(carpeta_raiz, "assets", "minijuegos", "flotaflota", nombre)
    return archivo

pygame.init()

jugando = True
game_over = False

ANCHO = 800
ALTO = 500

ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Flota Pau")

reloj = pygame.time.Clock()

fondo = pygame.image.load(encontrar_archivo("agua.jpg"))
fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))

pau = pygame.image.load(encontrar_archivo("pauflotaflota.png"))
pau = pygame.transform.scale(pau, (80, 80))

flota_flota_imagen = pygame.image.load(encontrar_archivo("uniflota.png"))
flota_flota_imagen = pygame.transform.scale(flota_flota_imagen, (150, 150))

ANCHO_PAU = 80
ALTO_PAU = 80
ANCHO_FLOTA = 150
ALTO_FLOTA = 45
ALTURA_FLOTA = 370

MARGEN_SUPERIOR_FLOTA = 65
MARGEN_LATERAL_FLOTA = 10
MARGEN_PIES_PAU = 12
MARGEN_LATERAL_PAU = 12
OFFSET_X_APOYO = 20

DEBUG = False

def superficie_flota(flota):
    return flota.top + MARGEN_SUPERIOR_FLOTA

def y_pau_apoyado(flota):
    return superficie_flota(flota) - ALTO_PAU + MARGEN_PIES_PAU

def crear_flota(anterior):
    distancia = random.randint(25, 50)

    if random.randint(1, 5) == 1:
        distancia = random.randint(125, 300)

    cambio_altura = random.randint(-8, 8)
    nueva_y = anterior.y + cambio_altura
    nueva_y = max(350, min(390, nueva_y))

    nueva_flota = pygame.Rect(
        anterior.right + distancia,
        nueva_y,
        ANCHO_FLOTA,
        ALTO_FLOTA
    )

    return nueva_flota

gravedad = 0.6
f_salto_normal = -9
f_doble_salto = -15

x_pau = 135 + OFFSET_X_APOYO
velocidad_y = 0
saltando = False

flota_flota_list = []

flota_inicial = pygame.Rect(
    100,
    ALTURA_FLOTA,
    ANCHO_FLOTA,
    ALTO_FLOTA
)

flota_flota_list.append(flota_inicial)

y_pau = y_pau_apoyado(flota_inicial)

for i in range(1, 8):
    anterior = flota_flota_list[-1]
    nueva_flota = crear_flota(anterior)
    flota_flota_list.append(nueva_flota)

indice_actual = 0
indice_destino = 0

destino_x = x_pau
camara_x = 0
puntos = 0

fuente = pygame.font.Font(None, 40)
fuente_game_over = pygame.font.Font(None, 60)
fuente_reinicio = pygame.font.Font(None, 35)

while jugando:

    reloj.tick(60)

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            jugando = False

        if evento.type == pygame.KEYDOWN:

            if not game_over and not saltando:

                if evento.key == pygame.K_LEFT:

                    nuevo_indice = indice_actual + 1

                    if nuevo_indice < len(flota_flota_list):

                        indice_destino = nuevo_indice

                        destino_x = (
                            flota_flota_list[indice_destino].centerx
                            - ANCHO_PAU // 2
                            + OFFSET_X_APOYO
                        )

                        velocidad_y = f_salto_normal
                        saltando = True
                        puntos += 1

                elif evento.key == pygame.K_RIGHT:

                    nuevo_indice = indice_actual + 2

                    if nuevo_indice < len(flota_flota_list):

                        indice_destino = nuevo_indice

                        destino_x = (
                            flota_flota_list[indice_destino].centerx
                            - ANCHO_PAU // 2
                            + OFFSET_X_APOYO
                        )

                        velocidad_y = f_doble_salto
                        saltando = True
                        puntos += 2

            if evento.key == pygame.K_r and game_over:

                x_pau = 135 + OFFSET_X_APOYO
                velocidad_y = 0
                saltando = False

                puntos = 0
                indice_actual = 0
                indice_destino = 0
                camara_x = 0
                destino_x = x_pau

                flota_flota_list = []

                flota_inicial = pygame.Rect(
                    100,
                    ALTURA_FLOTA,
                    ANCHO_FLOTA,
                    ALTO_FLOTA
                )

                flota_flota_list.append(flota_inicial)

                y_pau = y_pau_apoyado(flota_inicial)

                for i in range(1, 8):
                    anterior = flota_flota_list[-1]
                    nueva_flota = crear_flota(anterior)
                    flota_flota_list.append(nueva_flota)

                game_over = False

    if not game_over:

        if saltando:

            y_anterior = y_pau

            velocidad_y += gravedad
            y_pau += velocidad_y

            diferencia_x = destino_x - x_pau
            x_pau += diferencia_x * 0.12

            flotaflota = flota_flota_list[indice_destino]
            superficie = superficie_flota(flotaflota)

            pies_anterior = (
                y_anterior + ALTO_PAU - MARGEN_PIES_PAU
            )

            pies_actual = (
                y_pau + ALTO_PAU - MARGEN_PIES_PAU
            )

            izquierda = flotaflota.left + MARGEN_LATERAL_FLOTA
            derecha = flotaflota.right - MARGEN_LATERAL_FLOTA

            pau_izquierda = x_pau + MARGEN_LATERAL_PAU
            pau_derecha = x_pau + ANCHO_PAU - MARGEN_LATERAL_PAU

            if (
                velocidad_y > 0
                and pies_anterior <= superficie
                and pies_actual >= superficie
                and pau_derecha > izquierda
                and pau_izquierda < derecha
            ):

                y_pau = y_pau_apoyado(flotaflota)

                x_pau = (
                    flotaflota.centerx
                    - ANCHO_PAU // 2
                    + OFFSET_X_APOYO
                )

                velocidad_y = 0
                saltando = False
                indice_actual = indice_destino

        if x_pau > camara_x + 400:
            camara_x = x_pau - 400

        while flota_flota_list[-1].x < camara_x + ANCHO + 300:
            anterior = flota_flota_list[-1]
            nueva_flota = crear_flota(anterior)
            flota_flota_list.append(nueva_flota)

        if y_pau > ALTO + 100:
            game_over = True

    ventana.blit(fondo, (0, 0))

    for flotaflota in flota_flota_list:

        x_pantalla = flotaflota.x - camara_x

        if -ANCHO_FLOTA <= x_pantalla <= ANCHO:
            ventana.blit(
                flota_flota_imagen,
                (int(x_pantalla), flotaflota.y)
            )

    ventana.blit(
        pau,
        (int(x_pau - camara_x), int(y_pau))
    )

    if DEBUG:

        for flotaflota in flota_flota_list:

            x_pantalla = flotaflota.x - camara_x

            pygame.draw.line(
                ventana,
                (255, 0, 0),
                (
                    x_pantalla + MARGEN_LATERAL_FLOTA,
                    superficie_flota(flotaflota)
                ),
                (
                    x_pantalla + ANCHO_FLOTA - MARGEN_LATERAL_FLOTA,
                    superficie_flota(flotaflota)
                ),
                2
            )

        pygame.draw.line(
            ventana,
            (0, 255, 0),
            (
                x_pau - camara_x + MARGEN_LATERAL_PAU,
                y_pau + ALTO_PAU - MARGEN_PIES_PAU
            ),
            (
                x_pau - camara_x + ANCHO_PAU - MARGEN_LATERAL_PAU,
                y_pau + ALTO_PAU - MARGEN_PIES_PAU
            ),
            2
        )

    texto_puntos = fuente.render(
        "Puntos: " + str(puntos),
        True,
        (255, 255, 255)
    )

    ventana.blit(texto_puntos, (20, 20))

    if game_over:

        texto = fuente_game_over.render(
            "GAME OVER",
            True,
            (255, 255, 255)
        )

        ventana.blit(texto, (270, 190))

        texto2 = fuente_reinicio.render(
            "Presiona R para volver a jugar",
            True,
            (255, 255, 255)
        )

        ventana.blit(texto2, (230, 260))

    pygame.display.update()

pygame.quit()
