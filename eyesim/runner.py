import argparse
import importlib.util
import pathlib
import sys
import typing

import pygame
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from scipy.io.wavfile import read as read_wav

import eyesim.etc


_KNOB_TOGGLER = pygame.K_SPACE


def run(
    mode_folder: pathlib.Path,
    width: int,
    height: int,
    audio_file: typing.Optional[pathlib.Path] = None,
):
    """Run the eyesy simulator

    Args:
        mode_folder: path to the folder containing the mode to run. This
            folder should contain a "main.py" file with setup and update
            methods conforming to the eyesy API.
        width, height: the dimensions of the pygame window to display
        audio_file: path to audio file to play. If None, then
            no audio is played.
    """

    if str(mode_folder) == "test":
        mode_folder = pathlib.Path(__file__).parent / "test-mode"
        if audio_file is None:
            audio_file = mode_folder / "test.wav"

    # Load main module from given mode
    spec = importlib.util.spec_from_file_location(
        "mode", mode_folder / "main.py"
    )
    mode = importlib.util.module_from_spec(spec)
    sys.modules["mode"] = mode
    spec.loader.exec_module(mode)

    # Initialize pygame stuff
    pygame.init()
    screen = pygame.display.set_mode([width, height])
    pygame.display.set_caption(mode_folder.stem)
    clock = pygame.time.Clock()  # for locking fps

    # Set up widgets...

    sliders = []
    for i in range(5):
        slider = Slider(
            win=screen,
            x=i*100+100, y=100,
            width=40, height=100,
            min=0, max=100, step=1,
            vertical=True,
            initial=50
        )
        sliders.append(slider)

    persist_button = Button(
        win=screen,
        x=600, y=120,
        width=60, height=60,
        text="persist"
    )

    widgets = [*sliders, persist_button]
    for widget in widgets:
        widget.hide()
    widgets_hidden = True

    # Set up etc...

    etc = eyesim.etc.System()
    etc.mode_root = str(mode_folder.absolute())
    etc.xres = width
    etc.yres = height
    for i in range(5):
        setattr(etc, f"knob{i+1}", 0.5)
    mode.setup(screen, etc)
    persist_button.onClick = lambda: setattr(
        etc, 'auto_clear', not etc.auto_clear
    )

    # Set up audio if applicable...

    has_audio = audio_file is not None

    if has_audio:
        rate, data = read_wav(audio_file)
        if data.dtype != 'int16':
            # TODO: scipy's wave reader handles other types and their
            # docs enumerate the min/max for each. So this might be handled
            # easily by scaling approriately. However, pygame's music
            # player might work for other types.
            print(f"Audio file {audio_file} had data type: {data.dtype}")
            print("Current only wav files of type int16 are understood")
            sys.exit(1)
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play(loops=1000)

    def get_audio_segment():
        # Get how long the audio has playing in milliseconds
        pos = pygame.mixer.music.get_pos()
        index = int(rate*pos/1000)
        index = index % len(data)
        segment = data[index:index+100]
        if len(segment) != 100:
            return [0]*100
        return segment.max(axis=1).tolist()

    print("*"*80)
    print("Press the spacebar to toggle widget visibility!")
    print("*"*80)

    try:
        while True:
            # Handle events...
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    shutdown()
                elif (
                    event.type == pygame.KEYDOWN and
                    event.key == _KNOB_TOGGLER
                ):
                    if widgets_hidden:
                        for widget in widgets:
                            widget.show()
                    else:
                        for widget in widgets:
                            widget.hide()
                    widgets_hidden = not widgets_hidden

            if has_audio:
                etc.audio_in = get_audio_segment()

            if not widgets_hidden:
                for i, slider in enumerate(sliders, start=1):
                    value = slider.getValue() / 100.0
                    setattr(etc, f"knob{i}", value)

            # Updates, draw, etc.
            mode.draw(screen, etc)
            pygame_widgets.update(events)
            pygame.display.update()
            if etc.auto_clear:
                screen.fill(etc.bg_color)

            clock.tick(30)
    except KeyboardInterrupt:
        shutdown()


def shutdown(exit_code: int = 0):
    """Cleanup and exit pygame
    """
    pygame.quit()
    sys.exit(exit_code)


def run_cli():
    """Start eyesim runner as CLI
    """
    parser = argparse.ArgumentParser(description="Start eyesy simulation")
    parser.add_argument(
        "-m", "--mode-folder",
        type=pathlib.Path,
        required=True,
        help="path to folder containing mode's main.py script",
    )
    parser.add_argument(
        "-a", "--audio-file",
        type=pathlib.Path,
        help="path to audio file to play (optional)",
    )
    parser.add_argument(
        "-w", "--width",
        default=1200,
        type=int,
        help="window width in pixels",
    )
    parser.add_argument(
        "-t", "--height",
        default=900,
        type=int,
        help="window height in pixels",
    )
    args = parser.parse_args()
    run(
        mode_folder=args.mode_folder,
        width=args.width,
        height=args.height,
        audio_file=args.audio_file,
    )


if __name__ == "__main__":
    run_cli()
