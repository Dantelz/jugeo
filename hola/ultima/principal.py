import pygame

import os
import sys

# 1. Obtiene la ruta de la carpeta actual (carpeta_a)
ruta_actual = os.path.dirname(os.path.abspath(__file__))

# 2. Sube un nivel a la raíz del proyecto y apunta a carpeta_b
ruta_minijuegos = os.path.join(ruta_actual, "..", "minijuegos")

# 3. Agrega la ruta de carpeta_b a sys.path
sys.path.append(os.path.normpath(ruta_minijuegos))

# 4. Ahora puedes importar el archivo script_b como un módulo normal
import Flappy_Pau

pygame.init()

ancho = 800
alto = 600

TIEMPO_DISMINUCION = 1000
DURACION_NOCHE = 3000

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
nombres_habitaciones = [
    "BAÑO",
    "SALA DE ESTAR",
    "HABITACIÓN",
    "COCINA"
]

subpantalla = "normal"


try:

    fondo_bano = pygame.transform.smoothscale(
        pygame.image.load("bano.png"),
        (ancho, alto)
    )

    fondo_sala = pygame.transform.smoothscale(
        pygame.image.load("principal.png"),
        (ancho, alto)
    )

    fondo_habitacion = pygame.transform.smoothscale(
        pygame.image.load("habitacion.png"),
        (ancho, alto)
    )

    fondo_cocina = pygame.transform.smoothscale(
        pygame.image.load("cocina.png"),
        (ancho, alto)
    )

except:

    fondo_bano = pygame.Surface((ancho, alto))
    fondo_bano.fill((173, 216, 230))

    fondo_sala = pygame.Surface((ancho, alto))
    fondo_sala.fill((240, 230, 140))

    fondo_habitacion = pygame.Surface((ancho, alto))
    fondo_habitacion.fill((230, 230, 250))

    fondo_cocina = pygame.Surface((ancho, alto))
    fondo_cocina.fill((255, 218, 185))


noche = pygame.Surface((ancho, alto))
noche.fill((20, 20, 50))


def escalar_personaje(imagen, tamaño_maximo):

    ancho_orig, alto_orig = imagen.get_size()

    escala = min(
        tamaño_maximo / ancho_orig,
        tamaño_maximo / alto_orig
    )

    return pygame.transform.smoothscale(
        imagen,
        (
            int(ancho_orig * escala),
            int(alto_orig * escala)
        )
    )


tamaño_pou = 220


try:

    pou = escalar_personaje(
        pygame.image.load("pou.png"),
        tamaño_pou
    )

    paufeliz = escalar_personaje(
        pygame.image.load("paufeliz.png"),
        tamaño_pou
    )

    paumaso = escalar_personaje(
        pygame.image.load("paumaso.png"),
        tamaño_pou
    )

    paumuerto = escalar_personaje(
        pygame.image.load("paumuerto.png"),
        tamaño_pou
    )

    paudormido = escalar_personaje(
        pygame.image.load("poudormido.png"),
        tamaño_pou
    )

except:

    pou = pygame.Surface((150, 150))
    pou.fill((139, 69, 19))

    paufeliz = pou
    paumaso = pou
    paumuerto = pou
    paudormido = pou


fuente = pygame.font.Font(None, 28)
fuente_grande = pygame.font.Font(None, 36)
fuente_numero = pygame.font.Font(None, 22)


flecha_izquierda = pygame.Rect(
    10, 270, 50, 60
)

flecha_derecha = pygame.Rect(
    740, 270, 50, 60
)


# Botones de las habitaciones

boton_banar = pygame.Rect(
    325, 480, 150, 50
)

boton_minijuegos = pygame.Rect(
    230, 480, 160, 50
)

boton_tienda = pygame.Rect(
    410, 480, 160, 50
)

boton_dormir = pygame.Rect(
    325, 480, 150, 50
)

boton_comidas = pygame.Rect(
    325, 480, 150, 50
)


# Botones del menú de minijuegos

botones_minijuegos = [
    pygame.Rect(
        300,
        150 + i * 65,
        200,
        45
    )
    for i in range(5)
]


boton_volver_minijuegos = pygame.Rect(
    20, 20, 100, 40
)


pos_y_barras = 65

barra_baño = pygame.Rect(
    30, pos_y_barras, 170, 20
)

barra_comer = pygame.Rect(
    220, pos_y_barras, 170, 20
)

barra_dormir = pygame.Rect(
    410, pos_y_barras, 170, 20
)

barra_jugar = pygame.Rect(
    600, pos_y_barras, 170, 20
)


def dibujar_barra(
    ventana,
    rectangulo,
    nombre,
    valor
):

    pygame.draw.rect(
        ventana,
        (220, 220, 220),
        rectangulo
    )

    ancho_barra = int(
        rectangulo.width * valor / 100
    )

    parte_llena = pygame.Rect(
        rectangulo.x,
        rectangulo.y,
        ancho_barra,
        rectangulo.height
    )

    pygame.draw.rect(
        ventana,
        (100, 200, 100),
        parte_llena
    )

    pygame.draw.rect(
        ventana,
        (0, 0, 0),
        rectangulo,
        2
    )

    texto_nombre = fuente.render(
        nombre,
        True,
        (0, 0, 0)
    )

    ventana.blit(
        texto_nombre,
        (
            rectangulo.centerx -
            texto_nombre.get_width() // 2,
            rectangulo.y - 22
        )
    )

    texto_numero = fuente_numero.render(
        str(valor),
        True,
        (0, 0, 0)
    )

    ventana.blit(
        texto_numero,
        (
            rectangulo.centerx -
            texto_numero.get_width() // 2,
            rectangulo.bottom + 2
        )
    )


def dibujar_boton(
    ventana,
    rectangulo,
    texto
):

    pygame.draw.rect(
        ventana,
        (255, 255, 255),
        rectangulo
    )

    pygame.draw.rect(
        ventana,
        (0, 0, 0),
        rectangulo,
        2
    )

    texto_render = fuente.render(
        texto,
        True,
        (0, 0, 0)
    )

    ventana.blit(
        texto_render,
        texto_render.get_rect(
            center=rectangulo.center
        )
    )


def obtener_personaje():

    if (
        baño <= 5
        or comer <= 5
        or dormir <= 5
        or jugar <= 5
    ):
        return paumuerto

    if (
        baño <= 40
        or comer <= 40
        or dormir <= 40
        or jugar <= 40
    ):
        return pou

    if (
        baño < 95
        or comer < 95
        or dormir < 95
        or jugar < 95
    ):
        return paumaso

    return paufeliz


def manejar_click(posicion):

    global baño
    global comer
    global dormir
    global jugar
    global modo_noche
    global inicio_noche
    global habitacion_actual
    global subpantalla
    global mensaje_temporal
    global tiempo_mensaje


    # MENÚ DE MINIJUEGOS

    if subpantalla == "minijuegos":

        if boton_volver_minijuegos.collidepoint(posicion):

            subpantalla = "normal"
            return


        for i, b in enumerate(botones_minijuegos):

            if b.collidepoint(posicion):

                # MINIJUEGO 1
                if i == 0:

                    Flappy_Pau.ejecutar_flappy()

                    # Cuando termina Flappy Pau
                    # volvemos al menú de minijuegos
                    subpantalla = "minijuegos"

                    return


                else:

                    mensaje_temporal = (
                        f"Minijuego {i + 1} en desarrollo"
                    )

                    tiempo_mensaje = (
                        pygame.time.get_ticks()
                    )

        return


    # CAMBIO DE HABITACIÓN

    if flecha_izquierda.collidepoint(posicion):

        habitacion_actual = (
            habitacion_actual - 1
        ) % 4

        return


    elif flecha_derecha.collidepoint(posicion):

        habitacion_actual = (
            habitacion_actual + 1
        ) % 4

        return


    # BAÑO

    if habitacion_actual == 0:

        if boton_banar.collidepoint(posicion):

            baño = min(
                100,
                baño + 20
            )


    # SALA

    elif habitacion_actual == 1:

        if boton_minijuegos.collidepoint(posicion):

            subpantalla = "minijuegos"

        elif boton_tienda.collidepoint(posicion):

            mensaje_temporal = (
                "Todavía no disponible"
            )

            tiempo_mensaje = (
                pygame.time.get_ticks()
            )


    # HABITACIÓN

    elif habitacion_actual == 2:

        if (
            boton_dormir.collidepoint(posicion)
            and not modo_noche
        ):

            modo_noche = True

            inicio_noche = (
                pygame.time.get_ticks()
            )


    # COCINA

    elif habitacion_actual == 3:

        if boton_comidas.collidepoint(posicion):

            mensaje_temporal = (
                "Todavía no disponible"
            )

            tiempo_mensaje = (
                pygame.time.get_ticks()
            )


def actualizar_necesidades():

    global baño
    global comer
    global dormir
    global jugar
    global ultimo_descenso
    global ultimo_incremento_dormir
    global modo_noche


    tiempo_actual = pygame.time.get_ticks()


    if (
        tiempo_actual - ultimo_descenso
        >= TIEMPO_DISMINUCION
    ):

        baño = max(0, baño - 1)
        comer = max(0, comer - 1)
        jugar = max(0, jugar - 1)


        if not modo_noche:

            dormir = max(
                0,
                dormir - 1
            )


        ultimo_descenso = tiempo_actual


    if modo_noche:

        if (
            tiempo_actual -
            ultimo_incremento_dormir
            >= 100
        ):

            dormir = min(
                100,
                dormir + 2
            )

            ultimo_incremento_dormir = (
                tiempo_actual
            )


        if (
            tiempo_actual -
            inicio_noche
            >= DURACION_NOCHE
        ):

            modo_noche = False


def principal():

    ventana = pygame.display.get_surface()

    actualizar_necesidades()


    # PANTALLA DE MINIJUEGOS

    if subpantalla == "minijuegos":

        ventana.fill(
            (200, 220, 240)
        )

        titulo = fuente_grande.render(
            "SELECCIONA UN MINIJUEGO",
            True,
            (0, 0, 0)
        )

        ventana.blit(
            titulo,
            (
                ancho // 2 -
                titulo.get_width() // 2,
                80
            )
        )


        for i, b in enumerate(
            botones_minijuegos
        ):

            dibujar_boton(
                ventana,
                b,
                f"Minijuego {i + 1}"
            )


        dibujar_boton(
            ventana,
            boton_volver_minijuegos,
            "Volver"
        )


    # PANTALLA NORMAL

    else:

        fondos = [
            fondo_bano,
            fondo_sala,
            fondo_habitacion,
            fondo_cocina
        ]

        ventana.blit(
            fondos[habitacion_actual],
            (0, 0)
        )


        if (
            modo_noche
            and habitacion_actual == 2
        ):

            s = pygame.Surface(
                (ancho, alto)
            )

            s.set_alpha(180)

            s.fill(
                (0, 0, 50)
            )

            ventana.blit(
                s,
                (0, 0)
            )


        dibujar_boton(
            ventana,
            flecha_izquierda,
            "<"
        )

        dibujar_boton(
            ventana,
            flecha_derecha,
            ">"
        )


        txt_hab = fuente_grande.render(
            nombres_habitaciones[
                habitacion_actual
            ],
            True,
            (0, 0, 0)
        )

        ventana.blit(
            txt_hab,
            (
                ancho // 2 -
                txt_hab.get_width() // 2,
                10
            )
        )


        personaje = obtener_personaje()

        ventana.blit(
            personaje,
            personaje.get_rect(
                center=(400, 320)
            )
        )


        if habitacion_actual == 0:

            dibujar_boton(
                ventana,
                boton_banar,
                "Bañar"
            )


        elif habitacion_actual == 1:

            dibujar_boton(
                ventana,
                boton_minijuegos,
                "Minijuegos"
            )

            dibujar_boton(
                ventana,
                boton_tienda,
                "Tienda"
            )


        elif habitacion_actual == 2:

            dibujar_boton(
                ventana,
                boton_dormir,
                "Dormir"
            )


        elif habitacion_actual == 3:

            dibujar_boton(
                ventana,
                boton_comidas,
                "Comidas"
            )


        dibujar_barra(
            ventana,
            barra_baño,
            "BAÑO",
            baño
        )

        dibujar_barra(
            ventana,
            barra_comer,
            "COMER",
            comer
        )

        dibujar_barra(
            ventana,
            barra_dormir,
            "DORMIR",
            dormir
        )

        dibujar_barra(
            ventana,
            barra_jugar,
            "JUGAR",
            jugar
        )


    # MENSAJE TEMPORAL

    if (
        mensaje_temporal
        and (
            pygame.time.get_ticks()
            - tiempo_mensaje
            < 2000
        )
    ):

        txt_msg = fuente_grande.render(
            mensaje_temporal,
            True,
            (200, 0, 0)
        )

        rect_msg = txt_msg.get_rect(
            center=(
                ancho // 2,
                alto // 2
            )
        )

        pygame.draw.rect(
            ventana,
            (255, 255, 255),
            rect_msg.inflate(20, 10)
        )

        pygame.draw.rect(
            ventana,
            (0, 0, 0),
            rect_msg.inflate(20, 10),
            2
        )

        ventana.blit(
            txt_msg,
            rect_msg
        )