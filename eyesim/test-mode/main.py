import pygame


def setup(screen, etc):
    pass


def draw(screen, etc):
    xmid = etc.xres // 2
    ymid = etc.yres // 2
    pygame.draw.circle(
        surface=screen,
        color=etc.color_picker(etc.knob1), 
        center=(xmid, ymid),
        radius=10*etc.knob2 * max(etc.audio_in) / 2**8,
        width=int(10*etc.knob3),
    )
    etc.color_picker_bg(etc.knob5)
