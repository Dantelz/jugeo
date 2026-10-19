
import pygame
import os
import random

def encontrar_archivo(nombre):
    carpeta_raiz = os.path.dirname(__file__)
    archivo = os.path.join(carpeta_raiz, "assets", "minijuegos", "salto_nubes", nombre)
    return archivo

def crear_plataforma(anterior):
    y = anterior.y - random.randint(130, 160)

    desplazamiento = random.randint(200, 250)

    if anterior.x < ANCHO // 2:
        x = anterior.x + desplazamiento
    else:
        x = anterior.x - desplazamiento

    if x < 20:
        x = 20

    if x > ANCHO - ANCHO_PLATAFORMA - 20:
        x = ANCHO - ANCHO_PLATAFORMA - 20

    return pygame.Rect(
        x,
        y,
        ANCHO_PLATAFORMA,
        ALTO_PLATAFORMA
    )

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
pau = pygame.transform.scale(pau, (55, 55))

plataforma_imagen = pygame.image.load(encontrar_archivo("plataforma.png"))
plataforma_imagen = pygame.transform.scale(plataforma_imagen, (100, 100))

ANCHO_PAU = 55
ALTO_PAU = 55
ANCHO_PLATAFORMA = 100
ALTO_PLATAFORMA = 100


MARGEN_SUPERIOR_PLAT = 35   
MARGEN_LATERAL_PLAT = 15    
MARGEN_PIES_PAU = 8         


DEBUG = False

x_pau = ANCHO // 2
y_pau = ALTO - 150

velocidad_x = 0
velocidad_y = 0
gravedad = 0.4
salto = -15

plataformas = []

plataforma_inicial = pygame.Rect(
    ANCHO // 2 - 50,
    ALTO - 70,
    ANCHO_PLATAFORMA,
    ALTO_PLATAFORMA
)

plataformas.append(plataforma_inicial)

for i in range(8):
    nueva_plataforma = crear_plataforma(plataformas[-1])
    plataformas.append(nueva_plataforma)

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

                puntos = 0

                plataformas = []

                plataforma_inicial = pygame.Rect(
                    ANCHO // 2 - 50,
                    ALTO - 70,
                    ANCHO_PLATAFORMA,
                    ALTO_PLATAFORMA
                )

                plataformas.append(plataforma_inicial)

                for i in range(8):
                    nueva_plataforma = crear_plataforma(plataformas[-1])
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

        rect_pau = pygame.Rect(
            x_pau + 10,
            y_pau + 10,
            ANCHO_PAU - 20,
            ALTO_PAU - 20
        )

        if velocidad_y > 0:

            pies_anterior = y_anterior + ALTO_PAU - MARGEN_PIES_PAU
            pies_actual = y_pau + ALTO_PAU - MARGEN_PIES_PAU

            for plataforma in plataformas:

                superficie = plataforma.top + MARGEN_SUPERIOR_PLAT
                izquierda = plataforma.left + MARGEN_LATERAL_PLAT
                derecha = plataforma.right - MARGEN_LATERAL_PLAT

                if (
                    pies_anterior <= superficie
                    and pies_actual >= superficie
                    and rect_pau.right > izquierda
                    and rect_pau.left < derecha
                ):

                    y_pau = superficie - ALTO_PAU + MARGEN_PIES_PAU
                    velocidad_y = salto
                    puntos += 1
                    break

        if y_pau < ALTO // 2:

            diferencia = ALTO // 2 - y_pau
            y_pau = ALTO // 2

            for plataforma in plataformas:
                plataforma.y += diferencia

        plataformas = [
            plataforma
            for plataforma in plataformas
            if plataforma.y < ALTO + 50
        ]

        while plataformas and plataformas[-1].y > -100:
            nueva_plataforma = crear_plataforma(plataformas[-1])
            plataformas.append(nueva_plataforma)

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

    ventana.blit(pau, (x_pau, y_pau))

    if DEBUG:
        for plataforma in plataformas:
            pygame.draw.line(
                ventana,
                (255, 0, 0),
                (plataforma.left + MARGEN_LATERAL_PLAT, plataforma.top + MARGEN_SUPERIOR_PLAT),
                (plataforma.right - MARGEN_LATERAL_PLAT, plataforma.top + MARGEN_SUPERIOR_PLAT),
                2
            )
        pygame.draw.line(
            ventana,
            (0, 255, 0),
            (x_pau + 10, y_pau + ALTO_PAU - MARGEN_PIES_PAU),
            (x_pau + ANCHO_PAU - 10, y_pau + ALTO_PAU - MARGEN_PIES_PAU),
            2
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