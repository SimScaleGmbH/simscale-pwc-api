# PWC-API
The main goal of this code is to demonstrate how to run Pedestrian Wind Comfort (PWC) simulations on SimScale via the API.

The repository already contains a working example that can be used for testing. An example is a model of a project in the city of Bristol.

This code should serve the purpose of showing: (All the functions can be found in the utilities.py file)

1. How to set up the API connection.
2. How to create a project and upload geometries
3. How to retrieve entity IDs of parts and surfaces, so they can be used to assign relative pedestrian comfort maps, surface roughness, porous media, etc.   
4. How to set up a region of interest and define the size of the wind tunnel 
5. How to import wind data directly from Meteoblue. 
6. How to define a pedestrian comfort map, there is an option to either define absolute or relative pedestrian comfort maps.
7. How to define mesh settings, Reynolds scaling, and target mesh size if needed. 
8. How to check for the computing resources of a mesh and a simulation
9. Run the simulation

To use the code, you need to have a SimScale API key.
