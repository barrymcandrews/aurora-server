# Aurora Server

This server allows you to control an RGB LED strip, and other services on a Raspberry Pi through a RESTful web API.

## Getting Started

### Prerequisities
Although it may be possible to run this project on Windows, this server is designed to run on a Raspberry Pi, so it will work best on a POSIX system. (Debian, Red Hat, macOS, etc.)

####Python
Before running the project you need to install python 3. On macOS you can do this with homebrew:

```
$ brew update
$ brew install python3
``` 

You also need to install the `flask` and `gTTS` python packages:

```
$ pip3 install flask gTTS
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
