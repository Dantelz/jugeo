import pygame
import random, os

jugando = True
game_over = False

def encontrar_archivo(nombre):
    carpeta_raiz = os.path.dirname(__file__)
    archivo = os.path.join(carpeta_raiz, "assets", "minijuegos", "salto_nubes", nombre)
    return archivo

pygame.init()

ANCHO = 800
ALTO = 500

ventana = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Salta nube")
reloj = pygame.time.Clock()

fondo = pygame.image.load(encontrar_archivo("salto.png"))
pau = pygame.image.load(encontrar_archivo("paulanube.png"))

fondo = pygame.transform.scale(fondo, (ANCHO, ALTO))
pau = pygame.transform.scale(pau, (80, 80))

ancho_pau = 60
alto_pau = 60

x_pau = ANCHO // 2
y_pau = ALTO - 150

velocidad_x = 6
velocidad_y = 0
gravedad = 0.4
f_salto = -11

ancho_plataforma = 90
alto_plataforma = 15
velocidad_plataformas = 0

plataformas = []

plataformas.append(pygame.Rect(ANCHO // 2 - 45, ALTO - 70, ancho_plataforma, alto_plataforma))

for i in range(7):
    x_plataforma = random.randint(0, ANCHO - ancho_plataforma)
    y_plataforma = ALTO - 140 - i * 65
    plataformas.append(pygame.Rect(x_plataforma, y_plataforma, ancho_plataforma, alto_plataforma))

puntos = 0
fuente = pygame.font.Font(None, 35)

while jugando:

    reloj.tick(60)

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            jugando = False

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_SPACE and game_over:

                x_pau = ANCHO // 2
                y_pau = ALTO - 150
                velocidad_y = 0
                puntos = 0
                game_over = False
                plataformas.clear()

                plataformas.append(pygame.Rect(ANCHO // 2 - 45, ALTO - 70, ancho_plataforma, alto_plataforma))

                for i in range(7):
                    x_plataforma = random.randint(0, ANCHO - ancho_plataforma)
                    y_plataforma = ALTO - 140 - i * 65
                    plataformas.append(pygame.Rect(x_plataforma, y_plataforma, ancho_plataforma, alto_plataforma))

    if not game_over:

        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            x_pau -= velocidad_x

        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            x_pau += velocidad_x

        if x_pau < -ancho_pau:
            x_pau = ANCHO

        if x_pau > ANCHO:
            x_pau = -ancho_pau

        velocidad_y += gravedad
        y_pau += velocidad_y

        pau_rect = pygame.Rect(
            x_pau + 10,
            y_pau + 10,
            ancho_pau - 20,
            alto_pau - 20
        )

        if velocidad_y > 0:

            for plataforma in plataformas:

                if pau_rect.colliderect(plataforma) and y_pau + alto_pau - 10 <= plataforma.y + velocidad_y + 5:
                    velocidad_y = f_salto
                    break

        if y_pau < ALTO // 2 and velocidad_y < 0:

            desplazamiento = ALTO // 2 - y_pau
            y_pau = ALTO // 2

            for plataforma in plataformas:
                plataforma.y += desplazamiento

            puntos += desplazamiento

        plataformas = [
            plataforma for plataforma in plataformas
            if plataforma.y < ALTO
        ]

        while len(plataformas) < 8:

            y_nueva = min([plataforma.y for plataforma in plataformas], default=0) - random.randint(55, 85)
            x_nueva = random.randint(0, ANCHO - ancho_plataforma)

            plataformas.append(
                pygame.Rect(x_nueva, y_nueva, ancho_plataforma, alto_plataforma)
            )

        if y_pau > ALTO:
            game_over = True

    ventana.blit(fondo, (0, 0))

    for plataforma in plataformas:
        pygame.draw.rect(ventana, (80, 200, 80), plataforma)

    ventana.blit(pau, (x_pau, y_pau))

    texto_puntos = fuente.render("Puntos: " + str(puntos // 10), True, (255, 255, 255))
    ventana.blit(texto_puntos, (20, 20))

    if game_over:

        texto_game_over = fuente.render("GAME OVER", True, (255, 255, 255))
        texto_reiniciar = pygame.font.Font(None, 28).render("Presiona ESPACIO para volver a jugar", True, (255, 255, 255))

        ventana.blit(texto_game_over, (ANCHO // 2 - 100, ALTO // 2 - 30))
        ventana.blit(texto_reiniciar, (ANCHO // 2 - 180, ALTO // 2 + 20))

    pygame.display.update()

pygame.quit()
