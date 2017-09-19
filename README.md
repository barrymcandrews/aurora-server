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

Before running the project you need to install python 3.6. To do this you need to build the latest version from source.

1. Install the following build tools on your system.

	```
	$ sudo apt-get update
	$ sudo apt-get install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev
	```
2. Download and install the latest version of python from source. Replace the url in the wget command with the latest version from the [official site](https://www.python.org/downloads/source/).

	```
	$ wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tar.xz
	$ tar xf Python-3.6.0.tar.xz
	$ cd Python-3.6.0
	$ ./configure
	$ make
	$ sudo make altinstall
	```

#### Audio Source (Mopidy)
This server reads audio for the visualizer from a UNIX named pipe or FIFO. Any program that is capable of outputting audio to a FIFO can be used as the audio source. In my examples, I use Mopidy since it can stream from Spotify, SoundCloud and Google Music. You can see instructions on how to install Mopidy [here](https://docs.mopidy.com/en/latest/installation/). I also provide an example configuration file for mopidy located at `config/mopidy.conf`.

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
$ sudo chmod +x aurora/main.py
$ sudo ./aurora/main.py
```

### *(Under Construction Beyond this Point)*

### Setting Colors and Patterns

A very limited Swagger documentation page is also available by running the project and navigating to `localhost:5000/swagger`

#### Getting available devices for a server
Before you can set the lights to a color you need to know what lights are connected to the server. You can find this out by making a `GET` request to `/api/v2/channels`

##### Sample Response to GET /channels

```json
[
    {
        "device": "main",
        "label": "green",
        "pin": 3
    },
    {
        "device": "main",
        "label": "red",
        "pin": 2
    },
    {
        "device": "main",
        "label": "blue",
        "pin": 0
    },
    {
        "device": "secondary",
        "label": "green",
        "pin": 23
    },
    {
        "device": "secondary",
        "label": "red",
        "pin": 22
    },
    {
        "device": "secondary",
        "label": "blue",
        "pin": 21
    }
]
```

#### Managing Presets
When setting the lights to a color or pattern you create a "preset" on the server. Presets are handled as [CRUD resources](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) at the endpoint `/api/v2/presets`. 


To get a list of all running presets on the server make a `GET` request to `/api/v2/presets`. 

##### Sample Response to GET /api/v2/presets

```json
[
    {
        "id": 1,
        "name": "main-blue",
        "channels": [
            {
                "device": "main",
                "label": "blue",
                "pin": 0
            },
            {
                "device": "main",
                "label": "red",
                "pin": 2
            },
            {
                "device": "main",
                "label": "green",
                "pin": 3
            }
        ],
        "payload": {
            "type": "levels",
            "blue": 100,
            "red": 0,
            "green": 0
        }
    },
    ...
]
```

To create a new preset make a `POST` request to `/api/v2/presets`


##### Sample POST Request to /api/v2/presets

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
