# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 10:09:40 2022

@author: mkdei
"""

import utilities as util 
import pathlib 

pwc = util.PedestrianWindComfort()

#Setup the API connection 
pwc.set_api_connection()

#Create project 
pwc.create_project("pwc_test123", "123")

#Upload Geometry 
geometry_path = pathlib.Path().cwd() / "Geometries" / "AccucitiesBristol.stl"  
pwc.upload_geometry("Bristol_test", geometry_path)
