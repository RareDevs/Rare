# Rare
## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is currently considered beta software and in no way feature-complete. You **will** run into issues, so make backups first!

### Requirements
 - requests, pillow and pyqt5 installed via PyPI
 - Legendary installed via PyPI
 
 ### Usage
 When you run Rare, it'll check if you're currently logged in and walk you through logging in if you aren't.
 Once you're logged in, it will pull game covers from the "metadata" folder in Legedary's config folder, join logo and background together and then display a list of games you have in your account. Installed games will appear in full color while not installed ones will appear in black and white.

 ### Implemented
- Launch, install and uninstall games
- Authentication(Import from existing installation and via Browser)**(Please test it!)**
- In-app Browser to buy games
### Todos
- Sync saves
- ...

If you have features you want to have in this app, create an issue on github or build it yourself. Please report bugs(Especially Windows)

