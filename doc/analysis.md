# Analysis

## Is kkappkit an offline builder or a runtime library?
- If we aim for a runtime, then the app would still have to import  codegen part, which would still be part of the package unless "from...import" is used; this does not make much sense for the app
- If we aim for offline builder, then UI code will be baked into the app, which would give us maintenance headache
- Can we use a set of global widgets that's constantly updated for all apps? This would be a good idea if we want to build a widget library, but it's not a good idea for a RAD tool, because we want to keep the app as self-contained as possible
- So it makes more sense to make kkappkit a code-gen, and the dev can detach the app from kkappkit afterward; if an widget update is needed, then simply re-run the code-gen and let user update from the app store instead of pulling from kkappkit PyPI as a runtime dependency 

## Do we have to know what app this is?
- Yes, we want to generate the app completely from config files. This way the appkit may eventually become techstack-agnostic

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
- each `my.kkwgt.json` specifies a widget's implementation, without knowing how it is laid out
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
- RPC allows us to use any backend language, but the framework itself and the frontend is Python-based
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
- CLI argparse arguments must use primitive types that can be passed along through RPC, e.g., supported by protobuf with gRPC
- For app-config to remain KISS, the backend service specs must remain simple; this would require all details are defined elsewhere
- To support services/commands more than Python, we have to define a common interface for all languages, e.g., a JSON to specify the commandline and all arg types, which is actually a better idea than python argparse, because it is language-agnostic; by generating the JSON with an argparse-like form, the workflow can be as smooth as using argparse, and the Python CLI can be generated using this config as well

## Do we allow for custom data bindings?
- We must provide default bindings so that UI is mostly generated with one-click for primitive data types, e.g., int, float, list, etc.
- Advanced widgets can be defined to bind with domain-specific data types, e.g., a parameter with a threshold can be a float-slider that auto-switches its background color when the slider value passes the threshold; the CLI parser can apply such a type system to the parameter, and the UI can be generated accordingly; this is most likely a V2 feature
- Avoid making a sophisticated type system, which is often beautifully implemented in game engines and app-engines with a DSL, e.g., dart
- Instead, allow CLI to stay with primitive types, but tag arguments in widget-configs to define data roles; then in binding-config use role tags to bind with advanced widgets

## What kind of dev workflow do we promote?
### 1. GUI-UX first
- Consider UX in terms of layout first: what the app LOOKS like
  - In layout-config, define how widgets are arranged on a page or pages
  - Each widget corresponds to an app role, e.g., samplerate.kkwgt.json; this way we think in terms of domain concepts, e.g., samplerate, instead of implementation details, e.g., a slider
- then consider widgets in terms of data: how widget ops affect data and how to retrieve data from widgets:
  - In widget-config, define how widget ops affect data, e.g., sampling-rate is discrete and should be seen as an option widget like ComboBox; also because SR is unique, it must be a single-selection option 
  - Does the widget send out events on changing its value (RTPC),  or we bind data statically with the widget by keeping widget values in memory, consolidating all values from all the widgets as a parameter set, and finally shooting out a single event containing the parameter set on submit (form-filling)?
  - For an RTPC parameter, the widget must define an event
  - For a form entry, the widget must use a data binding
  - For a widget that is both, then both the above are needed
  - For a compound widget whose sub-widgets can do any or both the above, then sub-widgets must be defined in a list with predefined layout, each using a binding or an event or both
  - The handlers of these events will be generated later into a mediator module where RPCs can be hooked up
  - For form-filling, where data are first consolidated then sent out as a whole, codegen will generate submit button event handler, in which all widgets' values are retrieved through their bindings, and sent out in an RPC call
  - For RTPC, where data are sent out on every change, codegen will generate event handlers for each widget, in which the widget's value is retrieved through its binding, and sent out in an RPC call
  - All the above are defined in role.kkwgt.json
- Afterward, implement features using CLI for easier TDD
- Finally, polish on aesthetics and UI infographics using theming

### 2. CLI first
- Generate a CLI using the backend sub-config alone and implement the CLI version
- Then add frontend sub-config and generate the GUI and test the UX
- Later on, polish on aesthetics and UI infographics using theming
- Finally, config distribution method and generate the package


## Given all the constraints, do we have to support RPC?
- The build pipeline implies that the backend services are written in Python, because ast parsing is used
- That means we have full access to backend code, so we can just import the backend code and call the functions directly
- Services written in other languages cannot be registered to server anyway, so the multi-language benefit does not apply once frontend is written in a fixed language 
- As long as we have the glue layer, where event handlers are defined, we still enjoy frontend/backend separation
- so there is no need to support RPC in this architecture
- but we can support any subprocess backend as executable with arguments, this can be defined in a command-config .kakcmdex.json
- We are interested in creating a sequence of services and commands and combine the separate ui of these services/commands into one single-page app
- By importing the core modules of those services and commands, dev can then implement the event handlers directly; codegen can generate partial imp of calling services and commands, without trying to map output to input, which is impossible in general
- RPC is actually an imp detail and can be left for dev to implement, e.g., using gRPC, websocket, etc., so we can delegate the setup to a comm-config from app-config

## Do we have to consider distribution of the resulting app?
- Probably yes because it's a pain to install Python and all the dependencies
- The ideal workflow should be one-click to generate a user-friendly package that can be installed on any machine

## Do we really need to introduce microservices?
- We are only interested in fast-prototyping and simple delivery
- So our focus should be making things work and deliver in one piece for demoing
- Maintainability and scalability are not our concerns
- Microservices, however, is best for scalability and maintainability, which is better left for when the app is ready for production; and Tkinter will not be the ideal platform for production
- In other words, our target app is a monolith RAD tool for short-term usage; once the app proves useful, we'll build it in a more scalable and maintainable way 
- However, there is one scenario that is close to microservice case: the intended task may reuse two existing CLI tools as possible steps, then we could generate a GUI that use them both and possible some new services
- In this case, we can still hide those services as imp detail and only provide a facade service in the app-config to generate UI for the whole task

