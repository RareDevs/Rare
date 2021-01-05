# Rare
## A frontend for legendary, the open source Epic Games Launcher alternative

Rare is currently considered beta software and in no way feature-complete. You **will** run into issues, so make backups first!

### Requirements
 - requests, 
 - pillow
 - pyqt5
 - legendary-gl
 - PyQtWebengine
 
 ### Usage
 When you run Rare, it'll check if you're currently logged in and walk you through logging in if you aren't.
 Once you're logged in, it will pull game covers from the "metadata" folder in Legedary's config folder, join logo and background together and then display a list of games you have in your account. Installed games will appear in full color while not installed ones will appear in black and white.

 ### Implemented
- Launch, install and uninstall games
- Authentication(Import from existing installation and via Browser)**(Please test it!)**
- In-app Browser to buy games
- Settings
### Todos
- Sync saves
- ...


### Images

![alt text](https://github.com/Dummerle/Rare/blob/master/Screenshots/GameList.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/master/Screenshots/Uninstalled.png?raw=true)
![alt text](https://github.com/Dummerle/Rare/blob/master/Screenshots/Settings.png?raw=true)



If you have features you want to have in this app, create an issue on github or build it yourself. Please report bugs(Especially Windows)

