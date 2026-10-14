import pygame
jugador=True
game_over=False

pygame.init()
ANCHO=800
ALTO=500
ventana=pygame.display.set_mode((ANCHO,ALTO))
reloj=pygame.time.Clock()

fondo=pygame.image.load("salto.png")

pau_N=pygame.image.load("paumaso.png")
alto_pau=100
ancho_pau=100
x_pau=
y_pau=