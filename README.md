# LifeGen - A ClanGen Mod

## On AI & LLMs

> [!WARNING]
> Issues and Pull Requests created with AI based tools are going to be closed without further comment.
> Repeat offenders will be blocked from this project until further notice.

### [Discord Server](https://discord.gg/lifegen) || [Official website](https://mods.clangen.io/LifeGen/download) || [ClanGen Itch.io Page](https://sablesteel.itch.io/clan-gen-fan-edit) 

## Description
A ClanGen mod where you control your own cat! Choose your path and live out your life as a warrior.

## Credits
Original creator: just-some-cat.tumblr.com

Fan-edit creator: SableSteel, and many others

[LifeGen credits](https://docs.google.com/document/d/1XCm5Eo-y5VA6W9quDMbF3VNyKL7S8_9Tl4c2buuiA8g/edit?usp=sharing)

## Downloads
### Stable
Stable versions can be downloaded directly from the [official LifeGen mod website](https://mods.clangen.io/LifeGen/download)

### Development
**Note**: Development versions are automatic snapshots of current development efforts. They are _not_ stable, can crash and even corrupt your save files.
Additionally, we do not provide tech support for development versions.

Download at your own risk here: [LifeGen development download](https://mods.clangen.io/LifeGen/download-development)

## Running from source
> [!WARNING]
> Running the game via poetry is no longer supported. Please use uv instead.

ClanGen uses uv to manage virtual environments. Therefore it is required to install the dependencies and run the game from source without manual tweaking.

### Installing python
> [!NOTE] 
> You no longer need to install Python on your system. uv will automatically install the correct version for you.

### Installing uv
Follow the instructions for installing uv from the official website: https://docs.astral.sh/uv/getting-started/installation/

#### Linux, macOS, WSL
Open a terminal and paste this:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then restart your terminal and check if uv is installed by running `uv --version`

#### Windows (Powershell)
Open a PowerShell window (Windows key and then enter `PowerShell`) and paste this:
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Then restart your terminal and check if uv is installed by running `uv --version`

### Running the game via the helper scripts
#### Linux, macOS
Double click the `run.sh` script or open it in the terminal via `./run.sh` with the current working directory set to the game's root directory.

#### Windows
Double click the `run.bat` script.

### Running the game via Visual Studio Code
> [!NOTE] 
> uv automatically creates the .venv folder in the root directory of the game, unlike poetry.

First, you need to let uv install the dependencies. To do so, run the following command in the terminal:
```
uv sync
```

After that, ensure that you have the Python extension installed in Visual Studio Code. You can install it from the Extensions tab on the left sidebar. [(or click here)
](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

Then, open the Command Palette (Ctrl+Shift+P) and search for `Python: Select Interpreter`. Select the virtual environment created by uv (it should mention a `.venv` somewhere).

Finally, open the `main.py` file and click the play button in the top right corner to run the game.


## Bug Reporting
Please report any bugs on the LifeGen discord server: https://discord.gg/WqzdEcavcH
