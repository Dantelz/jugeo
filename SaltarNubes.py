
import pygame
import os
import random

def encontrar_archivo(nombre):
    carpeta_raiz = os.path.dirname(__file__)
    archivo = os.path.join(carpeta_raiz, "assets", "minijuegos", "salto_nubes", nombre)
    return archivo

pygame.init()

jugando = True
game_over = False

ANCHO = 800
ALTO = 500

ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("SaltoPAUUU")

reloj = pygame.time.Clock()

fondo = pygame.image.load(encontrar_archivo("salto.png"))
fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))

pau = pygame.image.load(encontrar_archivo("paulanube.png"))
pau = pygame.transform.scale(pau, (80, 80))

plataforma_imagen = pygame.image.load(encontrar_archivo("plataforma.png"))
plataforma_imagen = pygame.transform.scale(plataforma_imagen, (100, 100))

ANCHO_PAU = 55
ALTO_PAU = 55
ANCHO_PLATAFORMA = 100
ALTO_PLATAFORMA = 25

x_pau = ANCHO // 2
y_pau = ALTO - 150

velocidad_x = 0
velocidad_y = 0
gravedad = 0.4
salto = -11

plataformas = []

plataforma_inicial = pygame.Rect(
    ANCHO // 2 - 50,
    ALTO - 70,
    ANCHO_PLATAFORMA,
    ALTO_PLATAFORMA
)

plataformas.append(plataforma_inicial)

for i in range(1, 9):

    anterior = plataformas[-1]

    x = random.randint(0, ANCHO - ANCHO_PLATAFORMA)
    y = anterior.y - random.randint(35, 55)

    nueva_plataforma = pygame.Rect(
        x,
        y,
        ANCHO_PLATAFORMA,
        ALTO_PLATAFORMA
    )

    plataformas.append(nueva_plataforma)

camara_y = 0
puntos = 0
record = 0

fuente = pygame.font.Font(None, 35)
fuente_grande = pygame.font.Font(None, 60)

while jugando:

    reloj.tick(60)

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            jugando = False

        if evento.type == pygame.KEYDOWN:

            if not game_over:

                if evento.key == pygame.K_LEFT:
                    velocidad_x = -5

                if evento.key == pygame.K_RIGHT:
                    velocidad_x = 5

            if evento.key == pygame.K_r and game_over:

                x_pau = ANCHO // 2
                y_pau = ALTO - 150

                velocidad_x = 0
                velocidad_y = 0

                camara_y = 0
                puntos = 0

                plataformas = []

                plataforma_inicial = pygame.Rect(
                    ANCHO // 2 - 50,
                    ALTO - 70,
                    ANCHO_PLATAFORMA,
                    ALTO_PLATAFORMA
                )

                plataformas.append(plataforma_inicial)

                for i in range(1, 9):

                    anterior = plataformas[-1]

                    x = random.randint(0, ANCHO - ANCHO_PLATAFORMA)
                    y = anterior.y - random.randint(35, 55)

                    nueva_plataforma = pygame.Rect(
                        x,
                        y,
                        ANCHO_PLATAFORMA,
                        ALTO_PLATAFORMA
                    )

                    plataformas.append(nueva_plataforma)

                game_over = False

        if evento.type == pygame.KEYUP:

            if evento.key == pygame.K_LEFT and velocidad_x < 0:
                velocidad_x = 0

            if evento.key == pygame.K_RIGHT and velocidad_x > 0:
                velocidad_x = 0

    if not game_over:

        y_anterior = y_pau

        x_pau += velocidad_x
        velocidad_y += gravedad
        y_pau += velocidad_y

        if x_pau < -ANCHO_PAU:
            x_pau = ANCHO

        if x_pau > ANCHO:
            x_pau = -ANCHO_PAU

        if velocidad_y > 0:

            rect_pau = pygame.Rect(
                x_pau,
                y_pau,
                ANCHO_PAU,
                ALTO_PAU
            )

            for plataforma in plataformas:

                if (
                    y_anterior + ALTO_PAU <= plataforma.top
                    and rect_pau.bottom >= plataforma.top
                    and rect_pau.right > plataforma.left
                    and rect_pau.left < plataforma.right
                ):

                    y_pau = plataforma.top - ALTO_PAU
                    velocidad_y = salto
                    puntos += 1
                    break

        if y_pau < ALTO // 2:

            diferencia = ALTO // 2 - y_pau
            y_pau = ALTO // 2

            for plataforma in plataformas:
                plataforma.y += diferencia

        while plataformas[-1].y > -100:

            anterior = plataformas[-1]

            x = random.randint(0, ANCHO - ANCHO_PLATAFORMA)
            y = anterior.y - random.randint(35, 55)

            nueva_plataforma = pygame.Rect(
                x,
                y,
                ANCHO_PLATAFORMA,
                ALTO_PLATAFORMA
            )

            plataformas.append(nueva_plataforma)

        plataformas = [
            plataforma
            for plataforma in plataformas
            if plataforma.y < ALTO + 50
        ]

        if y_pau > ALTO:
            game_over = True

        if puntos > record:
            record = puntos

    ventana.blit(fondo, (0, 0))

    for plataforma in plataformas:

        ventana.blit(
            plataforma_imagen,
            (plataforma.x, plataforma.y)
        )

    ventana.blit(
        pau,
        (x_pau, y_pau)
    )

    texto_puntos = fuente.render(
        "Puntos: " + str(puntos),
        True,
        (255, 255, 255)
    )

    ventana.blit(texto_puntos, (20, 20))

    texto_record = fuente.render(
        "Record: " + str(record),
        True,
        (255, 255, 255)
    )

    ventana.blit(texto_record, (20, 55))

    if game_over:

        texto = fuente_grande.render(
            "GAME OVER",
            True,
            (255, 255, 255)
        )

        ventana.blit(texto, (270, 190))

        texto2 = fuente.render(
            "Presiona R para volver a jugar",
            True,
            (255, 255, 255)
        )

        ventana.blit(texto2, (230, 260))

    pygame.display.update()

pygame.quit()
