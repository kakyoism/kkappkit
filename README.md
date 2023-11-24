# kkAppKit

Framework for building small desktop applications with Python and [Tkinter](https://wiki.python.org/moin/TkInter)

## Design Goals
This project targets making it easier to build:
- Small desktop productivity tools
- Prototypes, demos, and tutorials

End-User UX
- Simple layout, e.g., vertical scroll, endless page as the parameter list grows
- Supports form-based apps and realtime-control apps
- Supports CLI and GUI
- Supports some common app features such as presets and context help

Dev UX
- Supports frontend-backend decoupling using Model-View-Controller architecture
- Ready-to-use widgets for solving common UI patterns
- JSON-based declarative configuration that drives code generation
- CI/CD friendly: ready-to-use build scripts for testing, building, and packaging
- Minimum dependencies: The generated app will only depend on Python 3 and Tkinter (wrapped into open-source packages written by this author)

## How to install kkappkit?
- Clone this repo
- POSIX: `cd kkappkit && sudo ln -s $(pwd)/kkappgen /usr/local/bin/`, ensure `/usr/local/bin` is under your system `$PATH`
- Windows: `cd kkappkit && mklink a\folder\under\your\system\%PATH%\kkappgen.bat .\kkappgen\kkappgen.bat`

## How to work with kkappkit?
- Initialize a new app project: `kkappgen -r /path/to/my_app_root -t <template_name>`
  - This generates a Poetry project with a template app
- Edit `pyproject.toml` and install dependencies: `cd /path/to/my_app_root && poetry install`
- Design the app parameter interface by editing the initialized configuration file, e.g., `src/app.json`
- Generates the interface (CLI/GUI) code: `kkappgen -r /path/to/my_app_root`
- Implement the core and hooks as a CLI or GUI or both
- Run the CLI or GUI using: `run` or `gui`
- Optionally, dev builds a standalone app bundle for distribution based on the configuration
- See `demo` folder for examples 

## Why not use a full-fledged framework like PySide, PyGTK, or Electron?
- Most of them are too heavy for small tools, complicating CI and distribution; Tkinter is the only first-party GUI lib, which simplifies distribution
- Those frameworks aim for flexibility and power and come with a steep learning curve; I want to bake in just enough policies for the RAD dev style without making the framework too opinionated
