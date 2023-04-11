# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 10:09:40 2022

@author: mkdei
"""

import utilities as util 
import pathlib 
# import simscale_sdk as sim_sdk

pwc = util.PedestrianWindComfort()

"""Setup the API connection"""
pwc.set_api_connection()

"""Create Project"""
pwc.create_project("pwc_test1234", "123")

"""Upload Geometry"""
#Provide the name of the files to upload, if it is a directory simply give the name,
#if it is a file then add the file extension to the name ex: example.stl

name_of_files_to_upload = ["AccucitiesBristol"] #AccucitiesBristol Shapes
# name_of_files_to_upload = ["Boston_Design2_with_terrain", "Design_1_Boston", "Design_2_Boston"]

base_path = pathlib.Path().cwd() / "Geometries" 
geometry_path = pwc.zip_cad_for_upload(name_of_files_to_upload,base_path)

#Keys are just a name that is a reference. Values are the layer names that are predefined in the CAD tool
# layers  = ["Terrain",  "TerrainPatches",
#            "Roads", "ManMadeSurfaces",
#            "Buildings", "ExtendedTerrain"]

layers  = {"terrain" : "Terrain", "terrain_patches" : "TerrainPatches",
            "roads" : "Roads", "Man_made_surfaces" : "ManMadeSurfaces",
            "buidlings" : "Buildings", "extended_terrain" : "ExtendedTerrain"}  


entities = []
#Iterate over the CAD models and run the simulations of each design in parallel
for i, cad in enumerate(name_of_files_to_upload): 
    #Upload the list of provided CAD models to the SimScale project
    
    pwc.upload_geometry(cad, geometry_path[i])
    print(pwc.project_id)
    print(pwc.geometry_id)
    
    for i , (key, value)in enumerate(layers.items()) :
        print(value)
        print(i)
        entities.append(value)
        #Get geometry mappings
        pwc.get_geometry_mapping(pwc.project_id, pwc.geometry_id, 
                                 entities_list= entities, layer_key = key, layer_number = i)
        

    """Simulation Setup"""
    """STEP 1: Region Of Interest"""
    #Uncomment the function below only if you plan to define a custom WT
    # pwc.set_custom_wt_size(height_ext = 200, side_ext = 200,
    #                        inflow_ext = 200, outflow_ext = 500)
    
    pwc.set_region_of_interest(radius = 300, center = [0,0], ground_height = 14.4, 
                                north_angle = 0, 
                                wt_size = 'moderate') #moderate, large, custom 
    
    """STEP 2: The Wind Conditions"""
    #Define information that characterizes the incoming wind
    pwc.set_geographical_location(latitude = 42.3600825, longitude = -71.0588801)
    pwc.set_num_wind_directions(8)
    pwc.set_wind_engineering_standard("EU") #["EU", "AS_NZS", "NEN8100", "LONDON"]
    pwc.set_wind_exposure_category(["EC2"]* 8) #["EC1", "EC2", "EC3", "EC4", "EC5", "EC6"]
    pwc.set_surface_roughness(surface_roughness= True)
    pwc.set_wind_data_source("METEOBLUE") #METEOBLUE, USER_UPLOAD
    pwc.set_wind_rose()
    
    """STEP 3: Pedestrian Comfort Map"""
    pwc.set_pedestrian_comfort_map_name("ComfortMap1")
    pwc.set_height_above_ground(2)
    pwc.set_pedestrian_comfort_ground_absolute() 
    pwc.set_pedestrian_comfort_map()
    
    pwc.add_more_comfort_maps("ComfortMap2", 3, "relative",
                              layers_key = ['terrain', 'roads', 'terrain_patches']) # call this for each new comfort map 
    
    """Simulation Control"""
    pwc.set_maximum_run_time(10000)
    pwc.set_num_fluid_passes(3)
    pwc.set_simulation_control()
    
    """Mesh Settings"""
    #call this function only when fineness is going to be set as "TargetSize"
    # pwc.set_mesh_min_cell_size(0.25) 
    
    pwc.set_mesh_fineness("VeryCoarse") #VeryCoarse,Coarse,Moderate,Fine,VeryFine,TargetSize
    pwc.set_reynolds_scaling(scaling = 0.1, auto_scale= True) #The value of scaling is used only when auto_scale = False
    pwc.set_mesh_settings()
    
    """Start Simulation"""
    pwc.set_simulation_spec(simulation_name= "Design{}".format(i))
    pwc.create_simulation()
    pwc.check_simulation_setup()
    pwc.estimate_simulation()
    pwc.start_simulation_run(run_name = "Design{}_8WD".format(i))
    
    
    
    
    
# layers  = {"terrain" : "Terrain", "terrain_patches" : "TerrainPatches",
#            "roads" : "Roads", "Man_made_surfaces" : "ManMadeSurfaces",
#            "buidlings" : "Buildings", "extended_terrain" : "ExtendedTerrain"}  

        # geometry_mappings = pwc.geometry_api.get_geometry_mappings(
        #     pwc.project_id, pwc.geometry_id, _class="face", entities=['ExtendedTerrain']
        # )
        # entities = [mapping.name for mapping in geometry_mappings._embedded]
        # print(f"entities: {entities}")
        
    