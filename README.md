== Setup: 

Install xcode, go to preferences, downloads, install command line tools
Install Sublime text editor

Install homebrew (http://brew.sh/)

$ brew install redis
$ sudo easy_install pip

$ pip install PIL
$ pip install bottle
$ pip install redis

== Run redis locally: 

$ redis-server

== Run the simulator locally: 

$ cd visualizer
$ python fake_blitter.py

Go to http://localhost:8080/ in a web browser

== Run when plugged in to the controller: 

$ python blitter.py

== Run examples: 

$ PYTHONPATH=. python examples/sparkline.py 
