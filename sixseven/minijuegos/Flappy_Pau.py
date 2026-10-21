import pygame
import random
import os


def ejecutar_flappy():

    pygame.init()

    ANCHO = 800
    ALTO = 600

    # Usamos la ventana que ya creó el juego principal
    ventana = pygame.display.get_surface()

    if ventana is None:
        ventana = pygame.display.set_mode((ANCHO, ALTO))

    pygame.display.set_caption("Flappy Pau")

    reloj = pygame.time.Clock()

    # =========================================================
    # RUTAS DE LAS IMÁGENES
    # =========================================================

    carpeta = os.path.dirname(os.path.abspath(__file__))

    ruta_fondo = os.path.join(
        carpeta,
        "assets",
        "minijuegos",
        "flappy",
        "flappy.png"
    )

    ruta_pau = os.path.join(
        carpeta,
        "assets",
        "minijuegos",
        "flappy",
        "flappypau.png"
    )

    # =========================================================
    # CARGAR IMÁGENES
    # =========================================================

    fondo = pygame.image.load(ruta_fondo).convert()
    pau = pygame.image.load(ruta_pau).convert_alpha()

    # Fondo ocupando toda la pantalla
    fondo = pygame.transform.scale(
        fondo,
        (ANCHO, ALTO)
    )

    # Pau
    pau = pygame.transform.scale(
        pau,
        (100, 100)
    )

    # =========================================================
    # VARIABLES DEL JUEGO
    # =========================================================

    pau_x = 150
    pau_y = 300

    velocidad_y = 0

    gravedad = 0.5
    salto = -9

    # =========================================================
    # TUBOS
    # =========================================================

    ancho_tubo = 80
    espacio = 170
    velocidad_tubos = 4

    obstaculos = []

    def crear_tubo():

        altura = random.randint(100, 300)

        obstaculos.append({
            "x": ANCHO,
            "altura": altura,
            "paso": False
        })

    crear_tubo()

    # =========================================================
    # PUNTOS
    # =========================================================

    puntos = 0

    fuente = pygame.font.Font(None, 50)
    fuente_game_over = pygame.font.Font(None, 70)
    fuente_reinicio = pygame.font.Font(None, 35)

    # =========================================================
    # ESTADO
    # =========================================================

    jugando = True
    game_over = False

    while jugando:

        # =====================================================
        # EVENTOS
        # =====================================================

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                jugando = False

            if evento.type == pygame.KEYDOWN:

                # ESC = volver al menú de minijuegos
                if evento.key == pygame.K_ESCAPE:
                    jugando = False

                # ESPACIO = saltar
                if evento.key == pygame.K_SPACE:

                    if game_over:

                        # Reiniciar
                        pau_y = 300
                        velocidad_y = 0

                        obstaculos.clear()

                        crear_tubo()

                        puntos = 0

                        game_over = False

                    else:

                        velocidad_y = salto

        # =====================================================
        # JUEGO
        # =====================================================

        if not game_over:

            # Gravedad
            velocidad_y += gravedad
            pau_y += velocidad_y

            # -------------------------------------------------
            # MOVER TUBOS
            # -------------------------------------------------

            for tubo in obstaculos:

                tubo["x"] -= velocidad_tubos

            # -------------------------------------------------
            # CREAR NUEVO TUBO
            # -------------------------------------------------

            if len(obstaculos) == 0 or obstaculos[-1]["x"] < 450:
                crear_tubo()

            # -------------------------------------------------
            # BORRAR TUBOS QUE SALIERON
            # -------------------------------------------------

            obstaculos = [
                tubo for tubo in obstaculos
                if tubo["x"] + ancho_tubo > 0
            ]

            # -------------------------------------------------
            # RECTÁNGULO DE PAU
            # -------------------------------------------------

            rect_pau = pygame.Rect(
                pau_x,
                int(pau_y),
                100,
                100
            )

            # -------------------------------------------------
            # COLISIONES CON LOS TUBOS
            # -------------------------------------------------

            for tubo in obstaculos:

                x = tubo["x"]
                altura = tubo["altura"]

                tubo_arriba = pygame.Rect(
                    x,
                    0,
                    ancho_tubo,
                    altura
                )

                tubo_abajo = pygame.Rect(
                    x,
                    altura + espacio,
                    ancho_tubo,
                    ALTO - (altura + espacio)
                )

                if rect_pau.colliderect(tubo_arriba):
                    game_over = True

                if rect_pau.colliderect(tubo_abajo):
                    game_over = True

                # -------------------------------------------------
                # PUNTOS
                # -------------------------------------------------

                if not tubo["paso"] and x + ancho_tubo < pau_x:

                    tubo["paso"] = True
                    puntos += 1

            # -------------------------------------------------
            # BORDES DE LA PANTALLA
            # -------------------------------------------------

            if pau_y < 0:
                game_over = True

            if pau_y + 100 > ALTO:
                game_over = True

        # =====================================================
        # DIBUJAR FONDO
        # =====================================================

        ventana.blit(fondo, (0, 0))

        # =====================================================
        # DIBUJAR TUBOS
        # =====================================================

        for tubo in obstaculos:

            x = tubo["x"]
            altura = tubo["altura"]

            # Tubo de arriba
            pygame.draw.rect(
                ventana,
                (0, 180, 0),
                (
                    x,
                    0,
                    ancho_tubo,
                    altura
                )
            )

            # Borde del tubo de arriba
            pygame.draw.rect(
                ventana,
                (0, 120, 0),
                (
                    x,
                    0,
                    ancho_tubo,
                    altura
                ),
                4
            )

            # Tubo de abajo
            pygame.draw.rect(
                ventana,
                (0, 180, 0),
                (
                    x,
                    altura + espacio,
                    ancho_tubo,
                    ALTO - (altura + espacio)
                )
            )

            # Borde del tubo de abajo
            pygame.draw.rect(
                ventana,
                (0, 120, 0),
                (
                    x,
                    altura + espacio,
                    ancho_tubo,
                    ALTO - (altura + espacio)
                ),
                4
            )

        # =====================================================
        # DIBUJAR PAU
        # =====================================================

        ventana.blit(
            pau,
            (
                pau_x,
                int(pau_y)
            )
        )

        # =====================================================
        # PUNTOS
        # =====================================================

        texto_puntos = fuente.render(
            str(puntos),
            True,
            (255, 255, 255)
        )

        ventana.blit(
            texto_puntos,
            (
                ANCHO // 2 - texto_puntos.get_width() // 2,
                30
            )
        )

        # =====================================================
        # GAME OVER
        # =====================================================

        if game_over:

            texto_game_over = fuente_game_over.render(
                "GAME OVER",
                True,
                (255, 255, 255)
            )

            ventana.blit(
                texto_game_over,
                (
                    ANCHO // 2 - texto_game_over.get_width() // 2,
                    220
                )
            )

            texto_reinicio = fuente_reinicio.render(
                "ESPACIO PARA REINICIAR",
                True,
                (255, 255, 255)
            )

            ventana.blit(
                texto_reinicio,
                (
                    ANCHO // 2 - texto_reinicio.get_width() // 2,
                    300
                )
            )

            texto_salir = fuente_reinicio.render(
    "ESC PARA VOLVER",
    True,
    (255, 255, 255)
)

            ventana.blit(
                texto_salir,
                (
                    ANCHO // 2 - texto_salir.get_width() // 2,
                    340
                )
            )

        # =====================================================
        # ACTUALIZAR PANTALLA
        # =====================================================

        pygame.display.flip()

        reloj.tick(60)

    # Volvemos al nombre de la ventana principal
    pygame.display.set_caption("PAU")


if __name__ == "__main__":
    ejecutar_flappy()