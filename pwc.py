# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 10:09:40 2022

@author: mkdei
"""

import utilities as util 
import pathlib 

pwc = util.PedestrianWindComfort()

"""Setup the API connection"""
pwc.set_api_connection()

"""Create Project"""
pwc.create_project("pwc_test123", "123")

"""Upload Geometry"""
#Provide the name of the files to upload, if it is a directory simply give the name,
#if it is a file then add the file extension to the name ex: example.stl
name_of_files_to_upload = ["Base_Design_Boston", "Design_1_Boston", "Design_2_Boston"]
base_path = pathlib.Path().cwd() / "Geometries" 
geometry_path = pwc.zip_cad_for_upload(name_of_files_to_upload,base_path)
for i, cad in enumerate(name_of_files_to_upload): 
    pwc.upload_geometry(cad, geometry_path[i])

"""Simulation Setup"""
"""STEP 1: Define Region Of Interest"""
#Uncomment the function below only if you plan to define a custom WT
# pwc.set_custom_wt_size(height_ext = 200, side_ext = 200,
#                        inflow_ext = 200, outflow_ext = 500)

pwc.set_region_of_interest(radius = 300, center = [50,0], ground_height = 0, 
                           north_angle = 0, 
                           wt_size = 'moderate') #moderate, large, custom 

"""STEP 2: Define The Wind Conditions"""
#Define information that characterizes the incoming wind
pwc.set_geographical_location(latitude = 42.3600825, longitude = -71.0588801)
pwc.set_num_wind_directions(4)
pwc.set_wind_engineering_standard("EU")
pwc.set_wind_exposure_category(["EC2"]* 4)
pwc.set_surface_roughness(surface_roughness= True)
pwc.set_wind_data_source("METEOBLUE")
pwc.set_wind_rose()


pwc.set_simulation_spec()


