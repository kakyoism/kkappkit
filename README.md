# kkAppKit

Framework for building small desktop tools with Python and [Tkinter](https://wiki.python.org/moin/TkInter)

## Intentions
This project aims to simplify building:
- Small desktop tools
- Prototypes, demos, and tutorials

## Target Users
- Scientists and engineers
- Technical artists

## Benefits for End-Users 
- Easy to add GUI frontend to command-line programs, and release them as standalone apps 
- Simple and consistent layout: All tools made by this kit use multi-page and endless-vertical-scroll paradigms
- Supports both CLI and GUI
- Supports important common app features out of the box, such as reset-to-default, presets and context help

## Benefits for Developers
- Almost no frontend code to write, thanks to its declarative JSON configuration that drives code generation
- Decouples frontend-backend developement using the Model-View-Controller architecture
- CI/CD friendly: ready-to-use build scripts for testing, building, and packaging in the generated app
- Lightweight: The GUI code only depends on small wrapper packages around Python 3 and Tkinter

## How to install kkappkit?
- Clone this repo
- POSIX: `cd kkappkit && sudo ln -s $(pwd)/kkappgen /usr/local/bin/`; ensure `/usr/local/bin` is under your system `$PATH`
- Windows: `cd kkappkit && mklink a\folder\under\your\system\%PATH%\kkappgen.bat .\kkappgen\kkappgen.bat`

## How to work with kkappkit?
- Initialize a new app project: `kkappgen -r /path/to/my_app_root -t <template_name>`
  - This generates a Poetry project with a template app
  - Look for template name under `res/template/*.app.json`; the firstname of the template file is the template name
- Edit `pyproject.toml` and install dependencies: `cd /path/to/my_app_root && poetry install`
- Design the app parameter interface by editing the initialized configuration file, e.g., `src/app.json`
- Generates the interface (CLI/GUI) code: `kkappgen -r /path/to/my_app_root`
- Implement the core and hooks as a CLI or GUI or both
- Run the CLI or GUI using: `run` or `gui`
- Optionally, dev builds a standalone app bundle for distribution based on the configuration
- See `demo` folder for examples 

## Why not use a full-fledged framework like PySide, PyGTK, or Electron?
- Most of them are too heavy for small tools, complicating CI and distribution; as the first-party GUI lib, the usage of Tkinter simplifies distribution
- Those frameworks aim for breadth and come with a steep learning curve; I want to bake in just enough policies for RAD without making the kit too opinionated

## How to run the demos?
The following procedures assume:
- You are a POSIX developer; Windows developers should be able to adapt the steps accordingly
- You have cloned and installed `kkappkit`
- You have [`poetry`](https://python-poetry.org) on your system

The demos must be built before running:
- The demo assets are located under `demo` folder.
- `character` is a form-filling demo
- `oscillator` is a controller demo
Next, we'll introduce each demo.

### Charater
```sh
# create a new skeleton
cd /path/to/kkappkit
kkappgen -r /path/to/character -t template

# navigate to the generated app  
cd /path/to/character
#
# edit pyproject.toml to add dependencies
# 
# then install dependencies
rm poetry.lock &> /dev/null
poetry install

# manually edit the configuration file (src/app.json) to fill in app metadata and input/output
# and generate the interface code
# overwrite the default assets with demo implementation
kkappgen -r `pwd` -i /path/to/kkappkit/demo/character

# run the app and play around with it
./ui

# quit the app after done
# build the standalone app for local testing 
ci/evaluate

# release as a platform-dependent installer
ci/release
```

### Oscillator
Similart to the above steps, but the demo assets are located under `demo/oscillator`.
