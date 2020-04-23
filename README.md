# Kivy-2048
A 2048 game using Python and Kivy. As the final project of the course 10.009-The Digital World

Author: Kevin Ma Yuchen

## How to run:
- install the libraries in `reqirements.txt` with command `pip3 install -r requirements.txt`
    - Do it in a virtual environment if you prefer. Check [this](https://github.com/Kevinskwk/Misc/blob/master/Python/Packages_and_Environments.md) for python virtual environment setup guidance.

- run 2048.py with command `python3 2048.py`

## How to play:

- Press the Start button to start a new game.

### Operation:
- With mouse: press and drag up/down/left/right
- With keyboard: use up/down/left/right keys

### Options
- Use the "Save" button to save the current game, the saved game will be stored in a file call save.p
    - **DO NOT** change the file name or move the file if you don't want to lose your saved game.
- Use the "Load" button to load previously saved game.

## Known issues
- If you move too fast (before the animation finishes), the colour update will have issue