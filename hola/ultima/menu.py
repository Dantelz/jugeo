import pygame
import principal

pygame.init()

ancho = 800
alto = 600

ventana = pygame.display.set_mode((ancho, alto))
pygame.display.set_caption("PAU")

ejecutando = True
reloj = pygame.time.Clock()
x = 300

texto1 = "JUGAR"
texto2 = "INSTRUCCIONES"
texto3 = "SALIR"

fuente = pygame.font.Font(None, 32)
pantalla_actual = "menu"

cuadro1 = pygame.Rect(x, 225, 200, 50)
cuadro2 = pygame.Rect(x, 300, 200, 50)
cuadro3 = pygame.Rect(x, 375, 200, 50)

cruz = pygame.Rect(740, 10, 40, 40)

try:
    fondo = pygame.image.load("PAU.png")
    fondo = pygame.transform.smoothscale(fondo, (ancho, alto))
except:
    fondo = pygame.Surface((ancho, alto))
    fondo.fill((100, 150, 200))


while ejecutando:

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            ejecutando = False

        if evento.type == pygame.MOUSEBUTTONDOWN:

            if evento.button == 1:

                if pantalla_actual == "menu":

                    if cuadro1.collidepoint(evento.pos):
                        pantalla_actual = "juego"

                    elif cuadro2.collidepoint(evento.pos):
                        pantalla_actual = "instrucciones"

                    elif cuadro3.collidepoint(evento.pos):
                        ejecutando = False

                elif pantalla_actual == "instrucciones":

                    if cruz.collidepoint(evento.pos):
                        pantalla_actual = "menu"

                elif pantalla_actual == "juego":

                    if cruz.collidepoint(evento.pos):
                        pantalla_actual = "menu"

                    else:
                        principal.manejar_click(evento.pos)


    if pantalla_actual == "menu":

        ventana.blit(fondo, (0, 0))

        pygame.draw.rect(ventana, (255, 255, 255), cuadro1)
        pygame.draw.rect(ventana, (255, 255, 255), cuadro2)
        pygame.draw.rect(ventana, (255, 255, 255), cuadro3)

        superficietexto1 = fuente.render(
            texto1, True, (194, 228, 255)
        )

        superficietexto2 = fuente.render(
            texto2, True, (194, 228, 255)
        )

        superficietexto3 = fuente.render(
            texto3, True, (194, 228, 255)
        )

        ventana.blit(
            superficietexto1,
            (x + 60, 225 + 14)
        )

        ventana.blit(
            superficietexto2,
            (x + 10, 300 + 14)
        )

        ventana.blit(
            superficietexto3,
            (x + 60, 375 + 14)
        )


    elif pantalla_actual == "instrucciones":

        ventana.fill((223, 186, 201))

        texto_instrucc = fuente.render(
            "Instrucciones:",
            True,
            (255, 255, 255)
        )

        texto_instrucc2 = fuente.render(
            "Usa las flechas para moverte de habitación.",
            True,
            (255, 255, 255)
        )

        ventana.blit(
            texto_instrucc,
            (250, 200)
        )

        ventana.blit(
            texto_instrucc2,
            (200, 250)
        )

        pygame.draw.line(
            ventana,
            (255, 255, 255),
            (740, 10),
            (770, 40),
            5
        )

        pygame.draw.line(
            ventana,
            (255, 255, 255),
            (770, 10),
            (740, 40),
            5
        )


    elif pantalla_actual == "juego":

        principal.principal()

        pygame.draw.line(
            ventana,
            (0, 0, 0),
            (740, 10),
            (770, 40),
            5
        )

        pygame.draw.line(
            ventana,
            (0, 0, 0),
            (770, 10),
            (740, 40),
            5
        )


    pygame.display.flip()
    reloj.tick(60)


pygame.quit()