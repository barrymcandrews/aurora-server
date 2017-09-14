# Aurora Server

**TL;DR** This server allows you to control RGB LED strips through a REST API. (But it really does so much more than that, so you should keep reading.)

### About

After buying an [LED Light Strip](https://www.amazon.com/gp/product/B00DTOAWZ2/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1), I was very disappointed with what it could do. It comes with an IR remote that gives you a few choices of colors and patterns, but nothing too elaborate. There are a few existing ways to get the lights to synchronize with music, but most of them are too complicated and require users to start and stop the program through the terminal. *Needless to say, a party is the worst time to have to open up ssh and start a program.* 

Aurora addresses these issues with a unified REST API. The API allows you to display:

* Static Presets (All the functionality of the IR remote)
	* Solid colors 
	* Fades between two or more colors
	* Sequences containing colors, fades or other sequences
* Music Visualization (based on [LightshowPi](lightshowpi.org)) 
	* Uses spectrum analysis to generate colors from music.
	* Music can be sourced from any program capable of writing audio to a FIFO. In my examples I use [Mopidy](https://www.mopidy.com/) since it can stream music from Spotify, SoundCloud, and Google Play.


## Getting Started

### Prerequisities
This project was designed specifically to run on a Raspberry Pi. It's been confirmed to work on the Raspberry Pi 3 and Zero, but should work on any model.

#### Hardware
For a simple hardware setup, follow [this tutorial](http://dordnung.de/raspberrypi-ledstrip). Other multi-strip configurations are possible too. 

#### Python

Before running the project you need to install python 3.6. On Raspbian, you can use the Advanced Package Tool:

```
$ sudo apt-get update
$ sudo apt-get install python3
``` 

#### Mopidy
This project uses the mopidy sound server to stream music from the internet. You can see instructions on how to install Mopidy [here](https://docs.mopidy.com/en/latest/installation/). Before starting the project, make sure all your custom settings in the file `config/mopidy.conf`. Ensure that the mopidy command has been added to your system PATH variable. 

### Installation

To install the server from source, first clone the repository:

```
#HTTP
$ git clone https://github.com/barrymcandrews/aurora-server.git
#SSH
$ git clone git@github.com:barrymcandrews/aurora-server.git
```

Next, build the project with Cython and install the dependencies:

```
$ cd aurora-server
$ sudo python3.6 setup.py build_ext --inplace
```


## How to Use

To start the server execute the file `aurora/main.py` with root privileges:

```
$ sudo ./aurora/root.py
```

### Setting Colors and Patterns

[Under Construction]

##### Sample Response to GET/presets/(id)

```json
{
   "type":" levels",
   "red": 0,
   "green": 0,
   "blue": 100
}
```


##### Sample POST Request to /presets

```json
{
	"device": "led-strip-1",
	"payload": {
		"type": "sequence",
   		"sequence": [
      		{
         		"type": "levels",
         		"red": 100,
         		"green": 0,
         		"blue": 50
      		},
      		{
         		"type": "fade",
         		"levels": [
            		{
            			"type": "levels",
               			"red": 100,
               			"green": 100,
               			"blue": 50
            		},
            		{
            			"type": "levels",
               			"red": 0,
               			"green": 0,
               			"blue": 0
            		}
         		]
      		}
   		]
	}	
}
```
