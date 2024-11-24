# STATS 604 Project 4 (CCEM)

This repository contains files which were used to create a Docker image (aedozie/stats604-project4-ccem) for the Stats 604 weather prediction project regarding 20 cities (refer to data/cities.txt for the full list). You can pull and run this image locally using Docker. Below are the instructions to help you set it up and run the container in an interactive mode or with a single command that quits after execution.
<br><br>


**Prerequisites**

Ensure you have Docker installed on your local machine.
<br><br>


**Pulling the Docker Image**

To pull the image from Docker Hub, use the following command:

`docker pull aedozie/stats604-project4-ccem`

This command will download the image and make it available locally on your system.
<br><br>


**Running the Docker Image Interactively**

Once the image is pulled, you can run it interactively to work within the container's environment. This will start a terminal session inside the container, allowing you to run commands as if you were on the system inside the container.

To run the container interactively, use this command:

`docker run -it aedozie/stats604-project4-ccem`

After running the above command, you will be inside the container, and you can execute any scripts or the following commands in the container environment:

`make clean` -- deletes everything except for the code (i.e., markdown files) and raw data (as originally downloaded). Takes < 1 minute.

`make` -- runs all analyses (except downloading raw data and making current predictions). Takes 6:03

`make predictions` -- makes current predictions and outputs them to the screen

  The output will look like this:
  "YYYY-MM-DD", XX.X, XX.X, XX.X, ..., XX.X
  
  where
  
  "YYYY-MM-DD" is the current date
  
  There are 300 numbers of the form XX.X where each X is a digit
  
  The numbers are predictions in degrees fahrenheit
  
  The order is given by:
  
  Anchorage +1 day, minimum; Anchorage +1 day, average; Anchorage +1 day, maximum;
  
  Anchorage +2 days, minimum; ...; Washington DC +5 days, maximum

  Note: use the data/cities.txt file to recall the order of the output.

`make rawdata` -- deletes and re-downloads the raw data. Takes ~10 minutes.

When you're done and want to exit the interactive session, simply type:

`exit`

This will stop and exit the container.
<br><br>


**Running the Docker Image and Quitting Afterwards**

If you want to run the image and have the container automatically exit after execution (for example, if you have a script to run), you can do so with the following command:

`docker run -it --rm aedozie/stats604-project4-ccem <<insert command>>`

Replace `<<insert command>>` with what you wish to run. For example, `make predictions`, the other commands listed above, or any scripts within the container.
This is useful if you only need the container to run a command and then automatically stop without needing to manually exit.
<br><br>


**Summary of Commands**

To pull the image:

`docker pull aedozie/stats604-project4-ccem`

To run interactively (stay inside the container until you exit):

`docker run -it aedozie/stats604-project4-ccem`

To run and quit automatically (container removes itself after execution):

`docker run -it --rm aedozie/stats604-project4-ccem <<insert command>>` 
