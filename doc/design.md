# Design

## app-config v2
- When generate a new project, all the configs should be generated at the fixed location with fixed filenames
- If we want to apply template configs, just manually overwrite the generated ones
- Although in app-config, frontend/comm/backend/dist are all fixed, we still keep them to given dev an overview about what should be configured

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
    "binding": "default_template.kkbind.json",
    "behaviour": "default_template.kkbehav.json",
    "theme": "default_template.kktheme.json"
  },
  "communication": "subproc.kkcomm.json",
  "backend": {
    "root": {
      "macOS": "</path/to/backend_root>",
      "Windows": "<c:/path/to/backend_root>"
    }
  },
  "distribution": "default_template.kkdist.json"
}
```

## app-config v1
```json
{
  "format": "1",
  "name": "my_app",
  "author": ["my_name <my_email>"],
  "description": "My app",
  "tutorial": [
    "example 1: do this",
    "my_app -i input_file -o output_file"
  ],
  "frontend": {
    "binding": "/path/to/my_app.kkbind.json",
    "behaviour": "/path/to/my_app.kkbehav.json",
    "theme": "/path/to/my_app.kktheme.json"
  },
  "communication": "/path/to/subproc.kkcomm.json",
  "backend": {
    "root": "</path/to/backend_root>"
  },
  "distribution": "/path/to/my_app.kkdist.json"
}
```