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
#Uncomment set_custom_wt_size function only if you plan to define a custom WT
# pwc.set_custom_wt_size(height_ext = 200, side_ext = 200,
#                        inflow_ext = 200, outflow_ext = 500)

pwc.set_region_of_interest(radius = 300, center = [50,0], ground_height = 0, 
                           north_angle = 0, 
                           wt_size = 'moderate') #moderate, large, custom 

pwc.set_simulation_spec()

