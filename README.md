# PWC-API
The main goal of this code is to demonstrate how to run Pedestrian Wind Comfort (PWC) simulations on SimScale via the API.

The repository already contains a working example that can be used for testing. An example is a model of a project in the city of Bristol.

This code should serve the purpose of showing: (All the functions can be found in the utilities.py file)

How to set up the API connection.
How to create a project and upload geometries
How to retrieve entity IDs of parts and surfaces, so that they can be used to assign relative pedestrian comfort maps, surface roughness, porous media, etc.   
How to set up a region of interest and define the size of the wind tunnel 
How to import wind data directly from Meteoblue. 
How define a pedestrian comfort map, there is an option either to define absolute or relative pedestrian comfort maps.
How to define mesh settings, Reynolds scaling, and target mesh size if needed. 
How to check for the computing resources of a mesh and a simulation
Run the simulation

To use the code you would need to have a SimScale API key - you can receive one after you contact the SimScale team.
