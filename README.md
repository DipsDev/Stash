# Stash
A custom git service and github like site.\
Stash, Stashhub(Much like git and github)\
\
This project is a school project, and later was submmited as a 5 units bagrot.\


## Stash
The service is 100% custom built, with no libraries whatsoever.

### Install
Currently, the service does not have an installer,\
and it is not planned to have one, as the project was already submitted.

### Usage
There are a few actions available in Stash:
- Push: push to stash-supported services(ex: StashHub).
- Pull: pull from stash-supported services, others and your repositories. 
- Commit: commit any changes to the local repository. 
- Add: add any files for stash to track.
- Clone: clone any stash-supported cloud repository.
- Branch: branch any local stash repository branch, or delete an existing one.
- Checkout: checkout to any existing branch, or branch-n-checkout a branch.
- Merge: merge between local stash-repositories, online merging is not supported.

## StashHub
The service was built using flask and sqlite.\
The service itself is made of two servers, which support concurrency and are built in python. 

### Web Server
The web server exposes a url to view and register with a user.\
the browser view allows:
- Users: create a user, or register with an existing one.
- Repository Maker: create a stash-repository, with description and name as you want.
- Repository Watcher: view public repositories' files, in browser.

### File Server
The file server allows users to push, pull and clone repositories from the cloud.\


