
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

fondo = pygame.image.load(encontrar_archivo("flotaflota.png"))
fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))

pau = pygame.image.load(encontrar_archivo("pauflotaflota.png"))
pau = pygame.transform.scale(pau, (80, 80))

flota_flota_imagen = pygame.image.load(encontrar_archivo("uniflota.png"))
flota_flota_imagen = pygame.transform.scale(flota_flota_imagen, (150, 150))

ANCHO_PAU = 80
ALTO_PAU = 80
ANCHO_FLOTA = 150
ALTO_FLOTA = 45
ALTURA_FLOTA = 410

gravedad = 0.6
f_salto = -6

x_pau = 135
y_pau = ALTURA_FLOTA - ALTO_PAU

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

for i in range(1, 8):

    anterior = flota_flota_list[-1]
    distancia = random.randint(100, 190)

    nueva_flota = pygame.Rect(
        anterior.right + distancia,
        ALTURA_FLOTA,
        ANCHO_FLOTA,
        ALTO_FLOTA
    )

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
                        destino_x = flota_flota_list[indice_destino].centerx - ANCHO_PAU // 2
                        velocidad_y = f_salto
                        saltando = True
                        puntos += 1

                elif evento.key == pygame.K_RIGHT:

                    nuevo_indice = indice_actual + 2

                    if nuevo_indice < len(flota_flota_list):

                        indice_destino = nuevo_indice
                        destino_x = flota_flota_list[indice_destino].centerx - ANCHO_PAU // 2
                        velocidad_y = f_salto - 1
                        saltando = True
                        puntos += 2

            if evento.key == pygame.K_r and game_over:

                x_pau = 135
                y_pau = ALTURA_FLOTA - ALTO_PAU

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

                for i in range(1, 8):

                    anterior = flota_flota_list[-1]
                    distancia = random.randint(100, 190)

                    nueva_flota = pygame.Rect(
                        anterior.right + distancia,
                        ALTURA_FLOTA,
                        ANCHO_FLOTA,
                        ALTO_FLOTA
                    )

                    flota_flota_list.append(nueva_flota)

                game_over = False

    if not game_over:

        if saltando:

            y_anterior = y_pau

            velocidad_y += gravedad
            y_pau += velocidad_y

            diferencia_x = destino_x - x_pau
            x_pau += diferencia_x * 0.08

            if velocidad_y > 0:

                rect_pau = pygame.Rect(
                    x_pau,
                    y_pau,
                    ANCHO_PAU,
                    ALTO_PAU
                )

                flotaflota = flota_flota_list[indice_destino]

                if (
                    y_anterior + ALTO_PAU <= flotaflota.top
                    and rect_pau.bottom >= flotaflota.top
                    and rect_pau.right > flotaflota.left
                    and rect_pau.left < flotaflota.right
                ):

                    y_pau = flotaflota.top - ALTO_PAU
                    x_pau = flotaflota.centerx - ANCHO_PAU // 2

                    velocidad_y = 0
                    saltando = False
                    indice_actual = indice_destino

        if x_pau > camara_x + 400:
            camara_x = x_pau - 400

        while flota_flota_list[-1].x < camara_x + ANCHO + 300:

            anterior = flota_flota_list[-1]
            distancia = random.randint(100, 190)

            nueva_flota = pygame.Rect(
                anterior.right + distancia,
                ALTURA_FLOTA,
                ANCHO_FLOTA,
                ALTO_FLOTA
            )

            flota_flota_list.append(nueva_flota)

        if y_pau > ALTO + 100:
            game_over = True

    ventana.blit(fondo, (0, 0))

    for flotaflota in flota_flota_list:

        x_pantalla = flotaflota.x - camara_x

        if -ANCHO_FLOTA <= x_pantalla <= ANCHO:
            ventana.blit(
                flota_flota_imagen,
                (x_pantalla, flotaflota.y)
            )

    ventana.blit(
        pau,
        (x_pau - camara_x, y_pau)
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
