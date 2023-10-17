# Design

## Do we have to know what app this is?
- No, better parsing from backend because app is just a frontend and all the features are in the backend
- So, the config should contain no app name, version, description and so on; the frontend version should be bound to the backend, e.g., its .toml

## Should we include all configuration in one file?
- No, we want to support as many types of legacy scripts as possible
- So, to parse those interfaces and generate RPC service stubs, we only specify the following at the app-config level:
  - where the backend repo is on the local machine, assuming service source code is saved under that repo as flat sub-folders
  - for each service, where to find their api for a static analysis, i.e., ast parsing
  - also assume there are argparse specs for ast parsing in their interfaces
- We don't fully specify RPC protocols so that various RPC frameworks can be hooked up, e.g., gRPC, websocket, POSIX sockets; we only specify ip, port, and protocol type, and possibly where the api stubs are saved, so that the offline codegen knows where to export the generated code
- Because UI can be infinitely complicated, we simply point from app-config to the layout-config, which is a separate file
- As a next step, layout-config can further point to widget-configs

## How do config files refer to each other?
### layout <=> app
- `.kakbehav.json` defines how ui binds to services through RPC
- `.kak.json` defines services that do the real work
- So `.kakbehav.json` only needs to know the service names, and parameters to call them
### layout <=> widget
- `.kaklayout.json` specifies how widgets are laid out on a single-page app panel, without knowing widget's implementation
- each `my.kakwgt.json` specifies a widget's implementation, without knowing how it is laid out
- So `.kaklayout.json` needs to specify widget names, and builder will find the corresponding widget config files
- All widgets are derived from the same base, so that layout only needs to know how to place the base widget, and the base widget knows how to render itself
- for optimal SNR, widget filtering is enabled at all times, e.g., widgets can be hidden-shown based on search-based visibility
- this means a default layout manager must be provided, e.g., a vertical grid layout that can hide rows based on keyword search
### widget <=> widget
- e.g., when a searchbar needs to know which widgets to hide, it needs to talk to a layout manager, which is likely a widget itself (panel)
- e.g., a checkbox may gray out a button, which is another widget
- so `.kkwgt.json` must refer to each other when necessary and define a list of ui reaction, e.g, disable/enable, hide/show, etc.
### theme <=> layout, widget
- `.kktheme.json` does not need to know app, but it needs to know widgets 
- `.kklayout.json` knows about themes, e.g., when laying ouw groups of widgets, how do we pick fonts for groups, how much margin/padding to use between groups, etc.

## Do we limit the feature scope of apps? e.g., do we aim for spreadsheet apps? media players? IDEs?
- To keep the framework as simple as possible, for V1 we support:
  - shoot-and-forget scripts, e.g., a script that takes a screenshot and saves it to a file
  - controllers, e.g., a synth that allows real-time parameter control
- We avoid supporting spreadsheet or media players because: 
  - they are too complicated to implement
  - they are too specific to be generalized
  - they are too easy to implement with existing tools, e.g., Excel, VLC, etc.
- For commercial-ready apps, commercial game-engines and app-engines are more suitable, e.g., Unreal and flutter are mature and free to use for commercial purposes, so we don't compete with them; but they are simply too heavy for small-scale development and requires building for platforms
- So the most suitable apps are those that are small enough to configure in a few minutes to generate a working prototype, but large enough to be useful, e.g., a task scheduler that needs a few pages of preferences to be set up before launching, which would be too time-consuming with CLI; a synth prototype that requires only a few sliders and switches
- If the declarative configs make the editing experience feel like programming, then the whole scheme is too complicated
- After building such client-side prototypes, and if they are useful, we can then decide whether to build a full-fledged app with a game engine, or to build a web app, etc.

## Do we support both endless-page and multi-page apps?
- Yes, we support both, because if parameter controls are too long then it is better to split them into multiple pages under well-defined topics and sub-topics
- This would require a page-switcher, e.g., a sidebar with a list of pages
- The searchbar will also need to search across all pages
- It'd be easier to just default to such a searchbar-sidebar-control-submit layout, and for simple apps, we can make the single-page endless but still keep the sidebar for compatibility
- To sum up, the layout starts as multi-page, and each page is implemented as an endless page to work with searchbar

## Do we have implementation constraints for the resulting app?
- The framework demands on a particular backend folder structure 
  - Services must be saved as flat sub-folders under a common root dir (backend)
  - Services must define a CLI using argparse
  - The feature implementation (core) can be located anywhere
- The server must load up services under a common API folder, e.g., gRPC implementation can generate the protobuf stubs under that folder
- Tkinter requires using the main thread to update UI, so the server must run either in a different process or a background thread
- It's likely that the server itself must be a headless app that  launches at system startup
- Theme must define emphasis styles using font, color, and shape
- We must limit the types of widgets that may affect other widgets, e.g., checkbox; it'd be much better to contain inter-widget influences inside a compound widget, so that configs don't have to define such influences
  - implement a widget for a dismissible widget group so that its checkbox can hide/show or enable/disable the whole group

## Do we allow for custom data bindings?
- We must provide default bindings so that UI is mostly generated with one-click for primitive data types, e.g., int, float, list, etc.
- Advanced widgets can be defined to bind with domain-specific data types, e.g., a parameter with a threshold can be a float-slider that auto-switches its background color when the slider value passes the threshold; the CLI parser can apply such a type system to the parameter, and the UI can be generated accordingly; this is most likely a V2 feature