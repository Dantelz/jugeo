

import pygame
import os
import random

def encontrar_archivo(nombre):
    carpeta_raiz = os.path.dirname(__file__)
    archivo = os.path.join(carpeta_raiz, "assets", "minijuegos", "salto_nubes", nombre)
    return archivo

def crear_plataforma(anterior):
    y = anterior.y - random.randint(105, 140)
    desplazamiento = random.randint(100, 190)

    if anterior.x < ANCHO // 2:
        x = anterior.x + desplazamiento
    else:
        x = anterior.x - desplazamiento

    x = max(0, min(x, ANCHO - ANCHO_PLATAFORMA))

    return pygame.Rect(
        x,
        y,
        ANCHO_PLATAFORMA,
        ALTO_PLATAFORMA
    )

def obtener_zona(puntos):
    if puntos < 50:
        return 0
    elif puntos < 150:
        return 1
    elif puntos < 300:
        return 2
    elif puntos < 500:
        return 3
    else:
        return 4

pygame.init()

jugando = True
game_over = False

ANCHO = 800
ALTO = 500

ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("SaltoPAUUU")

reloj = pygame.time.Clock()

fondos = [
    pygame.transform.scale(
        pygame.image.load(
            encontrar_archivo("resubdelsuelo.png")
        ).convert(),
        (ANCHO, ALTO)
    ),
    pygame.transform.scale(
        pygame.image.load(
            encontrar_archivo("salto.png")
        ).convert(),
        (ANCHO, ALTO)
    ),
    pygame.transform.scale(
        pygame.image.load(
            encontrar_archivo("salto.png")
        ).convert(),
        (ANCHO, ALTO)
    ),
    pygame.transform.scale(
        pygame.image.load(
            encontrar_archivo("spacebar.jpg")
        ).convert(),
        (ANCHO, ALTO)
    ),
    pygame.transform.scale(
        pygame.image.load(
            encontrar_archivo("paraisopau.jpg")
        ).convert(),
        (ANCHO, ALTO)
    )
]

pau = pygame.image.load(
    encontrar_archivo("paulanube.png")
).convert_alpha()

pau = pygame.transform.scale(pau, (55, 55))

plataformas_imagenes = [
    pygame.image.load(
        encontrar_archivo("piedraplat.png")
    ).convert_alpha(),

    pygame.image.load(
        encontrar_archivo("plataforma.png")
    ).convert_alpha(),

    pygame.image.load(
        encontrar_archivo("nubepau.png")
    ).convert_alpha()
]

plataformas_imagenes = [
    pygame.transform.scale(imagen, (100, 100))
    for imagen in plataformas_imagenes
]

nube_peligrosa = pygame.image.load(
    encontrar_archivo("nube_peligrosa.png")
).convert_alpha()

nube_peligrosa = pygame.transform.scale(
    nube_peligrosa,
    (85, 55)
)

ANCHO_PAU = 55
ALTO_PAU = 55

ANCHO_PLATAFORMA = 100
ALTO_PLATAFORMA = 100

MARGEN_SUPERIOR_PLAT = 35
MARGEN_LATERAL_PLAT = 15
MARGEN_PIES_PAU = 8

x_pau = ANCHO // 2
y_pau = ALTO - 150

velocidad_x = 0
velocidad_y = 0
gravedad = 0.4
salto = -15

plataformas = []
nubes_peligrosas = []

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
zona_anterior = 0

fuente = pygame.font.Font(None, 35)
fuente_grande = pygame.font.Font(None, 60)

while jugando:

    reloj.tick(60)

    zona = obtener_zona(puntos)

    if zona != zona_anterior:
        nubes_peligrosas = []
        zona_anterior = zona

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
                    nueva_plataforma = crear_plataforma(
                        plataformas[-1]
                    )
                    plataformas.append(nueva_plataforma)

                nubes_peligrosas = []
                zona_anterior = 0
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

            pies_anterior = (
                y_anterior + ALTO_PAU - MARGEN_PIES_PAU
            )

            pies_actual = (
                y_pau + ALTO_PAU - MARGEN_PIES_PAU
            )

            for plataforma in plataformas:

                superficie = (
                    plataforma.top + MARGEN_SUPERIOR_PLAT
                )

                izquierda = (
                    plataforma.left + MARGEN_LATERAL_PLAT
                )

                derecha = (
                    plataforma.right - MARGEN_LATERAL_PLAT
                )

                if (
                    pies_anterior <= superficie
                    and pies_actual >= superficie
                    and rect_pau.right > izquierda
                    and rect_pau.left < derecha
                ):

                    y_pau = (
                        superficie - ALTO_PAU
                        + MARGEN_PIES_PAU
                    )

                    velocidad_y = salto
                    puntos += 1
                    break

        if y_pau < ALTO // 2:

            diferencia = ALTO // 2 - y_pau
            y_pau = ALTO // 2

            for plataforma in plataformas:
                plataforma.y += diferencia

            for nube in nubes_peligrosas:
                nube.y += diferencia

        plataformas = [
            plataforma
            for plataforma in plataformas
            if plataforma.y < ALTO + 100
        ]

        nubes_peligrosas = [
            nube
            for nube in nubes_peligrosas
            if nube.y < ALTO + 100
        ]

        while plataformas and plataformas[-1].y > -100:

            nueva_plataforma = crear_plataforma(
                plataformas[-1]
            )

            plataformas.append(nueva_plataforma)

            if zona == 1 and random.random() < 0.65:

                x_nube = random.randint(
                    0,
                    ANCHO - 85
                )

                y_nube = nueva_plataforma.y + random.randint(
                    35,
                    100
                )

                nubes_peligrosas.append(
                    pygame.Rect(
                        x_nube,
                        y_nube,
                        85,
                        55
                    )
                )

        if zona == 1:

            for nube in nubes_peligrosas:

                if rect_pau.colliderect(nube):
                    game_over = True
                    break

        if y_pau > ALTO:
            game_over = True

        if puntos > record:
            record = puntos

    zona = obtener_zona(puntos)

    ventana.blit(fondos[zona], (0, 0))

    if zona == 0:
        imagen_plataforma = plataformas_imagenes[0]
    elif zona == 1:
        imagen_plataforma = plataformas_imagenes[1]
    else:
        imagen_plataforma = plataformas_imagenes[2]

    for plataforma in plataformas:

        ventana.blit(
            imagen_plataforma,
            (plataforma.x, plataforma.y)
        )

    if zona == 1:

        for nube in nubes_peligrosas:

            ventana.blit(
                nube_peligrosa,
                (nube.x, nube.y)
            )

    ventana.blit(pau, (x_pau, y_pau))

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

    nombres_zonas = [
        "Subsuelo",
        "Superficie / Cielo",
        "Atmósfera / Cielo Superior",
        "Espacio",
        "Paraíso / Cielo"
    ]

    texto_zona = fuente.render(
        nombres_zonas[zona],
        True,
        (255, 255, 255)
    )

    ventana.blit(
        texto_zona,
        (ANCHO - texto_zona.get_width() - 20, 20)
    )

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
