# winservicewatch (under development)

Library for Python WinService with observer design pattern.

## Introduction
This simple library gives you more control over the part of your app
you wish to run as a Windows service. The code included not only show you how
to run your script as a service, but also how to schedule repeated task and share
the information about service state when only task is in progress.

I have made this classes for my commercial app. What I needed was to set up
repeating task on Windows Server as a service. On the other hand, app users should have
access to settings and database of the app through the GUI. One of the features
I had to take care of was to know exactly when the scheduled task in the service
is running to avoid collisions.

## Technologies
Project was written entirely in **Python 3.7**

I used following Python libraries:
* Schedule
* RPyC
