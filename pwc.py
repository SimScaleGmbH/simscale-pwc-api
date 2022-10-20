# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 10:09:40 2022

@author: mkdei
"""

import utilities as util 


#Setup the API connection 

pwc = util.PedestrianWindComfort()

pwc.set_api_connection()

#Create project 
pwc.create_project("pwc_test", "123")
