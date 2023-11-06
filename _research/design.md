# Design

## generated output
`dataclass` vs. `class` vs. `types.SimpleNamespace` vs. `dict`
- we prefer having type annotation for future type-matching opportunities between inputs and outputs
- type annotation is not supported while initializing `dict` or `types.SimpleNamespace`
- `class` and `dataclass` both support type annotation, but `dataclass` is more compact
- since output doesn't need behaviours, `dataclass` is good enough

## build variables
- syntax: `${<var_name>}`
- `CLI`: app's command line interface source file path
- `PLATFORM`: platform name, e.g., `macOS`, `Windows`, etc.
- `APP_NAME`: app's name

## behaviour-config
- Define the behaviour of the app, e.g., oneshot, rt-control, etc.
- Top-level keys represent UI elements and their behaviours; implementation details are not exposed to the user, e.g., lock-free queues 
- The app behaviour reflects on the bottom action panel along with other non-parameter panels, e.g., statusbar, etc.
- Progress can be finite or infinite; finite progressbar should display the color bar along with the fraction of progress; no descriptive text is shown, which is the job of statusbar

## binding-config
- Parameters are laid out from top to bottom as top-level key-value groups; their order is preserved both in the sidebar groups and in the group pages
- Every parameter is bound to a tk variable 
- Does not differentiate between oneshot and rt-control
- Snake-case top-level keys are auto-used for widget title, unless sub-key *title* is specified
- *title* will be a separate row on top of the widget
- *validate* key is optional, and default to false if not specified; once specified, custom validation is enabled and statusbar will show validation tips; value text will be highlighted if validation fails
- *group* format: <sidebar-entry>.<page-group>
- *slaves* define widgets to be influenced by the current widget; the current widget is the master widget; one master can slave on several groups of slaves with group-specific effects, e.g., enable one but disable another; custom actions must be defined in code; on change, these effects are applied in sequence

## app-config
- When generate a new project, all the configs should be generated at the fixed location with fixed filenames
- If we want to apply template configs, just manually overwrite the generated ones
- Although in app-config, frontend/comm/backend/dist are all fixed, we still keep them to given dev an overview about what should be configured
- Renamed cfgfile prefix from `kk` to `kak`
- `kk` refers `kakyo` and `kak` refers to `kkappkit`; name `kkbind` seems too generic and may risk shadowing all later namings 
```json
{
  "format": "1",
  "name": "my_app",
  "author": ["my_name <my_email>"],
  "description": "My app",
  "tutorial": [
    "example 1: do this",
    "<app_name> -i input_file -o output_file"
  ],
  "frontend": {
    "binding": "oneshot.kakbind.json",
    "behaviour": "default.kakbehav.json",
    "theme": "default.kaktheme.json"
  },
  "communication": "subproc.kakcomm.json",
  "backend": {
    "root": {
      "macOS": "</path/to/backend_root>",
      "Windows": "<c:/path/to/backend_root>"
    },
    "tech": "python"
  },
  "distribution": "pyinstaller.kakdist.json"
}
```
