# Aurora Server

This server allows you to control an RGB LED strip connected to a Raspberry Pi ([like this setup](http://dordnung.de/raspberrypi-ledstrip/)) through a RESTful API.

### About

The server has two main functions:

1. Static Light
	* This displays solid colors, fading colors, and sequences containing both solid and fading colors.
2. Light Show (based on [LightshowPi](lightshowpi.org))
	* This uses spectrum analysis to generate colors from music.
	* The music plays through a program called [Mopidy](https://www.mopidy.com/) which can be configured to stream from services like Spotify, SoundCloud, and Google Play.


## Getting Started

### Prerequisities
Although it may be possible to run this project on Windows, this server is designed to run on a Raspberry Pi, so it will work best on a POSIX system.

#### Python

Before running the project you need to install python 3.6. On Raspbian, you can use the Advanced Package Tool:

```
$ sudo apt-get update
$ sudo apt-get install python3 libasound2-dev
``` 

#### Mopidy
This project uses the mopidy sound server to stream music from the internet. You can see instructions on how to install Mopidy [here](https://docs.mopidy.com/en/latest/installation/). Before starting the project, make sure all your custom settings in the file `config/mopidy.conf`. Ensure that the mopidy command has been added to your system PATH variable. 

### Installation

To use and contribute to this project clone it directly from this repository:

```
#HTTP
$ git clone https://github.com/barrymcandrews/aurora-server.git
#SSH
$ git clone git@github.com:barrymcandrews/aurora-server.git
```


## How to Use

To start the server execute the file `aurora_server.py` with root privileges:

```
$ sudo ./aurora_server.py
```

### Managing Services

Depending on your configuration file at config/aurora.conf, the static light service or the light show service may run when the program is started. To check what services are running, send a `GET` request to the endpoint `/api/v1/services`.

##### Sample Response to GET http://localhost:5000/api/v1/services

```json
HEADERS:
	Content-Type: application/json
BODY:
{
   "active-threads":2,
   "services":[
      {
         "name":"STATIC_LIGHT",
         "status":"started"
      },
      {
         "name":"LIGHT_SHOW",
         "status":"stopped"
      }
   ]
}
```

#### Starting and Stopping Services

To start or stop a service, send a `POST` request to the endpoint `/api/v1/services/service-name` where service-name is the name of the service. The two valid service names are: light_show and static_light.

##### Sample POST Request to http://localhost:5000/api/v1/services/light_show

```json
HEADERS:
	Content-Type: application/json
BODY:
{
  "status":"started | stopped"
}
```

### Setting Colors and Patterns

Make sure the Static Light Service is running before trying to set a color or pattern. The endpoint for controlling patterns is `/api/v1/s/static-light`. Sending a `GET` request to this endpoint will return a JSON Object with the current pattern.

##### Sample Response to GET http://localhost:5000/api/v1/s/static-light

```json
HEADERS:
	Content-Type: application/json
BODY:
{
   "type":"color",
   "red":0,
   "green":0,
   "blue":100
}
```

You can also send a `POST` request to this endpoint to set the pattern. The pattern can be either a JSON Object or a custom syntax for this project called Borealis.

##### Sample POST Request to http://localhost:5000/api/v1/s/static-light with JSON

```json
HEADERS:
	Content-Type: application/json
BODY:
{
   "type":"sequence",
   "sequence":[
      {
         "type":"color",
         "red":100,
         "green":0,
         "blue":50
      },
      {
         "type":"fade",
         "colors":[
            {
               "red":100,
               "green":100,
               "blue":50
            },
            {
               "red":0,
               "green":0,
               "blue":0
            }
         ]
      }
   ]
}
```

##### Sample POST Request to http://localhost:5000/api/v1/s/static-light with Borealis

```
HEADERS:
	Content-Type: application/borealis
BODY:

#delay .5
set 100 0 50
fade
	set 100 100 50
	set 0 0 0
```


As you can see, Borealis is a much more concise way to convey pattern data to the server. Both of the examples above will cause the server to display the same pattern.
