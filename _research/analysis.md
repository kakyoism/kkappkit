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

## How to let one widget affect another?
- Sometimes we add a checkbox for enabling/disabling a set of the widgets below it, to express a conditional config
- this requires dev to define a master-slave binding from the checkbox master to its slaves, for instance
- hence, we can mark the master and its slaves
- because UI ops are one at a time, so it's safe to allow multiple masters on one slave in addition to one master on multiple slaves
- as an alternative, we could let slaves to define its masters, but that'd be more work than define from the master end where we can edit everything in one place

## What do we specify in behaviour-config?
- The goals for having a status report
  - giving feedback on all kinds of form-filling actions, e.g., validation errors without msgbox: red text on the widget, with tooltip on statusbar, the full info in the log
- statusbar is a good place for briefing the current status, e.g., "ready", "working", "done", "error", "age must be a number", etc. 
- log is a good place for detailed info, e.g., "failed to connect to server at ..., diagnostics: ...", etc.; statusbar can provide a button to open the log in web-browser 
- with oneshot apps, form entries can automatically send error messages to statusbar, and log to log file
- with controller apps, there would be no need to validate or show control parameters on statusbar or log for performance reasons; but in the debug-build, logging might be useful
- as long as some parameters should bind with statusbar and the others should not, we need to define a list of parameters that should bind with statusbar

## How to define a control protocol?
- Controller app is GUI only with V1; it's possible to later support app-specific REPL commands for CLI, but that's not the focus of V1
- The elements of control: sender, receiver, message, and protocol
- OSC protocol defines an IP-like command ID, and a parameter list
- gRPC defines a package-service-request-reply structure
- Frontend is usually the sender/client (Tkinter widgets), and the server 
- Server IP/port should be in binding-config; the protocol should only care about the message format, e.g., OSC commands, gRPC requests, etc.
- The control-config should be independent of the binding-config, and only generates a mediator/bridge module as the mechanism for sending commands

## Do we need custom environment variable? syntax?
- Yes we do. It should be clear which part of a JSON string must be substituted and which part is literal
- Then the syntax had better be:
  - familiar to devs; reuse established syntax
  - easy to parse
  - easy to read
- Candidates: `%(<var_name>)s`, `$<var_name>`, `$<var_name>$`, `${<var_name>}`, `{{<var_name>}}`
- `%(<var_name>)s` is the syntax for Python string formatting, which is easy to parse and read, but not familiar to devs
- `$<var_name>$` is the JetBrains snippet syntax, not familiar to most devs, and not easy to parse when there are consecutive vars
- `$<var_name>` is the basic BASH variable syntax, familiar to devs, but not easy to parse when it's followed by literal text
- `${<var_name>}` is the BASH variable syntax with braces, familiar to devs, and easy to parse, and somewhat easy to read
- `{{<var_name>}}` is the Jinja2 syntax, not familiar to devs, easy to parse, and somewhat verbose to write up

## What should the code-gen's analytical chain be like?
- dev: kak => kakctrl => kakcomm => kakbind/kaktheme =>
- distribute: app => kakdist
- Before analysis, config files are copied from kkappkit's template folder to the app's designated folder

## Looks like we need a syntax system to make the formats a bit more rigorous to make the system more robust. What should it be like?
- take cross-config reference as an example
- we need to reference
  - config file: JSON
  - JSON fields inside the file
- constraints
  - no field has mixture of literal and variable, i.e., the text components are all variables, e.g., JSON keys or build-vars
- approaches for referencing fields
  - compact oneliner: `${cfgfile}.<parent_field>.<sub_field>....`
  - compound fields: `{"file": "${cfgfile}", "field": "<parent_field>.<sub_field>...."`
- the compact approach is easy to write, but harder to parse
- the compound approach is easy to parse, but harder to write
- the design constraints:
  - we want this system to be easy to learn
  - and we want people to write it by hand in the design process
- so we must minimize custom syntax, but writing cross-referencing by hand implies a learning curve
- the shortest referencing path is a UUID, but it's not human-readable
- to flatten the learning curve, the workflow can allow human to write the initial template with a minimal meta-language, then the codegen generates the UUIDs, finally human can complete the cross-referencing using the generated UUIDs; user can always use text search to associate IDs with their sources (usually widgets)
- we can define the format constraints: only widgets use IDs, and in kakcomm, first-level keys are always widget IDs
- ID-driven cross-referencing will hurt readability, so we can offer an optional `note` field for each config field, so that human can comment with readable reminders; we can also generate a private field, e.g., `_sender` or `_path`, to store the source of the field, e.g., the dot-formatted config-field path
- in other words, instead of human writing the paths, we can generate the paths instead, and human can focus on the protocal itself, i.e., topic, payload, response, etc.

## How should kkappkit interact with the app?
- Candidate approaches
  - make kkappkit a dependency
  - make kkappkit a git submodule
  - ship kkappkit as part of the app, e.g., as its ci pipeline
- Relevant questions:
  1. is the app actually an app project, i.e., open-source?
  2. should we debug the app onsite after it's shipped to end-users?
  3. should we support auto-update?
- The idea of making a standalone app is to relieve user from the burden of learning the implementation detail
- The app dev should be able to fix the app on site without dependencies, meaning the build pipeline should be self-contained, even when without the internet
- The only way to ensure this is to ship the build pipeline with the app
- Then how to migrate when pipeline upgrades?
- Wait for the dev to ship the new version, which is the expected workflow for a standalone app

## The current analytical model is still confusing. Can we improve it?
- Confusion: There is no obvious implementation path by looking at the config files
- the model-view-controller (MVC) pattern is a good start, but we don't have it right now; frontend is View, backend is Model, and the mediator is Controller
- we have a model in .kakbind.json, but it contains both data model (argparse-inspired argument definition) and some ui design (events, group). So a scientist or a backend-dev would have no idea how to fill up the events and groups because those are unrelated with the core algorithm; both designer and dev must edit this config; this would slow down the design process
- the model should also define inter-data influences, which is actually a model thing; the design of using a checkbox to enable/disable is just a frontend manifestation; so this info is currently in .kakbind.json and rightfully so
- .kakctrl.json seems out of place; it seems merely a gimmick UI that bears no info about model/view/controller; it defines the bottom action hub, and thus a view entity
- for backend to work with both CLI and GUI, it needs a model that both CLI and GUI operate on; for CLI, its usually the parsed arguments, and a wrapper object (model) for GUI, both can be abstracted away with a worker class
- views like offline form submission bar (control panels) have no direct access to model, but rely on a controller that knows both model and view; even with a subprocess IPC imp, views should only consider its looks without defining the CLI commands
- kkcomm should act as a controller: it should define for each data entry:
  - events 
  - protocols
  - requests and responses for events
- there should be a separate view config for data model and control panel that collaboratively define the layout of the whole app, e.g., sidebar, statusbar, etc.
- endless page is good enough, later when introducing voice commands, sidebar would be totally unnecessary especially for a small app
- So an updated workflow
  - edit .kkmdl.json to define the data model, i.e., CLI args
  - generate ids for each data entry
  - edit bind.kkview.json to define the layout, grouping, theme of data-binding widgets, and control panels, for each data-entry ID
  - edit ctrl.kkview.json to define the layout, theme of control panels, for each ID
  - edit layout.kkview.json to layout the widget groups if we have 2+ .kkview.json files
  - generate ids for each control on the panel
  - edit .kkcomm.json to define the control protocol, including events (triggers), sender, requests, responses, and protocol tech
  - edit .kkdist.json to define how to package and ship the app
- If we pair up MVC, because model keys are both readable and unique (first-level keys), they are natural app-scope uuids; there is no need to generate uuid in the human-editable configuration; we could still generate IDs in the imp if needed

## Do we have better options for the config file naming?
- Current naming: <app_specific>.kak<config_type>.json
  - Pros: `kak-` prefix is short and unique, minimizing name clashing
  - Cons: `kak-` prefix is not intuitive, so it hurts the SNR of the middlename 
- Alternative: <app_specific>.<config_type>.json
  - Pros: more intuitive, and the middlename is more readable
  - Cons: name clashing is possible, but they can be protected by a folder, e.g., `kkappkit/<app_specific>.<config_type>.json`
- Conclusion: the alternative is a better approach

## What's with the frontend-backend-communication to MVC switch?
- frontend-backend-communication is a good idea, but it's an analytical model instead of a design model; it's therefore not fit for a role of codegen configuration
- MVC is a design pattern, and therefore a better fit for codegen configuration
- The current design is a mix of both, which is confusing; so we removed backend 
- As for the backend field, currently all it specifies is Python as its tech-stack. But that's not useful and it's impossible to use anything otherwise to interface with Tkinter; other tech-stacks usually have mature frontend-backend duo, e.g., flutter, JS frameworks, etc.; so we can throw it away after converting to MVC

## Is the current scope too big?
- probably yse. Once we introduce MVP, it's no longer a code-gen but a designer tool, or a middleware.
- then the config files expand to include:
  - data model
  - view model
  - control model
  - layout model
  - theme model
  - distribution model
- the details involved in configuring the entire set is simply another UI language, except that we design it in JSON instead of a DSL
- we are gonna ask the question again: who's the most frequent user?
- probably just me, and I'm not a designer, so I don't need a designer tool; let's just KISS; do not make it another flutter
- this means it should offer fewer features and forget about flexibility; it's too big if it's bigger than pysimplegui
- for v1, we should cut the following features
  - themes
  - configurable control panels
- this means, we only configure the data model and events, and the rest is generated

## Do we need a .sh/.bat-.py delegation?
- No, because this would introduce two layers of subprocesses, which would add to the complexity despite some maintenance benefit in making .sh/.bat shorter

## Is *required* necessary for an argument spec?
- No, because it's redundant with the default value
- An argument is required when its default is None (null for JSON) 

## Is the bridge pattern necessary for structuring generated main app entry point versus custom implementation?
- In V1, we aim to expose the full interface of controller in gui.py so that dev can implement the controller in control.py accordingly
- Because gui.py is fully generated main entry, we don't want dev to mess with it; so we need a way to separate the generated code from the custom code
- We chose the bridge pattern, which is a simple way for the separation
- However, we soon dicovered that the implementation still needs to be aware of the generated code, e.g., before submitting, we need to update the view and retrieve all fields, which is implemented in the base controller
- Therefore, we had to expose the base controller to the implementation, leading to a tight coupling between the interface and the interface; we essentially just extended the interface
- so inheritance would be a better fit here, because the implementation can open-close the base controller as needed