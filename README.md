# Aurora Server

This server allows you to control an RGB LED strip connected to a Raspberry Pi ([like this setup](http://dordnung.de/raspberrypi-ledstrip/)) through a RESTful API.
###About
The server has two main functions:

1. Static Light
	* This displays solid colors, fading colors, and sequences containing both solid and fading colors.
2. Light Show (based on [LightshowPi](lightshowpi.org))
	* This uses spectrum analysis to generate colors from music.
	* The music plays through a program called [Mopidy](https://www.mopidy.com/) which can be configured to stream from services like Spotify, SoundCloud, and Google Play.


## Getting Started

### Prerequisities
Although it may be possible to run this project on Windows, this server is designed to run on a Raspberry Pi, so it will work best on a POSIX system.

####Python
Before running the project you need to install python 3. On Raspbian, you can use the Advanced Package Tool:

```
$ sudo apt-get update
$ sudo apt-get install python3
``` 

####Mopidy
This project uses the mopidy sound server to stream music from the internet. You can see instructions on how to install Mopidy [here](https://docs.mopidy.com/en/latest/installation/). Ensure that the mopidy command has been added to your system PATH variable. 

### Installation

To use and contribute to this project clone it directly from this repository:

```
#HTTP
$ git clone https://github.com/barrymcandrews/aurora-server.git
#SSH
$ git clone git@github.com:barrymcandrews/aurora-server.git
```

####Dependencies
After cloneing, run the install script to get the rest of the dependencies:

```
$ cd aurora-server
$ ./install.sh
```

 
