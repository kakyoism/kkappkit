# Design

## Q&A
### Do we have to know what app this is?
- No, better parsing from backend because app is just a frontend and all the features are in the backend
- So, the config should contain no app name, version, description and so on; the frontend version should be bound to the backend, e.g., its .toml

### Should we include all configuration in one file?
- No, we want to support as many types of legacy scripts as possible
- So, to parse those interfaces and generate RPC service stubs, we only specify the following at the app-config level:
  - where the backend repo is on the local machine, assuming service source code is saved under that repo as flat sub-folders
  - for each service, where to find their api for a static analysis, i.e., ast parsing
  - also assume there are argparse specs for ast parsing in their interfaces
- We don't fully specify RPC protocols so that various RPC frameworks can be hooked up, e.g., gRPC, websocket, POSIX sockets; we only specify ip, port, and protocol type, and possibly where the api stubs are saved, so that the offline codegen knows where to export the generated code
- Because UI can be infinitely complicated, we simply point from app-config to the layout-config, which is a separate file
- As a next step, layout-config can further point to widget-configs



