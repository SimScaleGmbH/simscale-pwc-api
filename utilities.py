# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 10:09:12 2022

@author: mkdei
"""
import os
import time
import zipfile
import shutil

import isodate
import urllib3

import json 
import requests

import simscale_sdk as sim_sdk

class PedestrianWindComfort():
    
    def __init__(self): 
        
        #API Variables
        self.api_key        = ""
        self.api_url        = ""
        self.api_key_header = "X-API-KEY"
        self.version        = "/v0"
        self.host           = ""
        self.server         = "prod"
        
        #Client Variables
        self.api_client  = None
        self.project_api = None
        self.storage_api = None
        self.geometry_import_api = None
        self.geometry_api = None
        self.simulation_api = None
        self.simulation_run_api = None
        self.table_import_api =None
        self.reports_api = None
        self.wind_api = None 
        
        #Project Variables 
        self.project_name = ""
        self.project_id   = ""
        
        #Geometry Variables
        self.geometry_name = ""
        self.geometry_id   = ""
        self.geometry_path = ""
        
        #Region Of Interest Variables
        self.region_of_interest = None
        self.roi_radius = 300
        self.center = [0,0]
        self.ground_height = 0 
        self.north_angle = 0 
        self.wind_tunnel_size = "" # moderate, large, custom
        self.wind_tunnel_size_obj = None
        self.wind_tunnel_type = None # only used when defining custom WT
        self.height_extension = None
        self.side_extension = None
        self.inflow_extension = None 
        self.outflow_extension = None 
        
        #Wind Condition Variables
        self.wind_conditions = None 
        self.latitude = None 
        self.longitude = None 
        self.latitude_meteoblue = None
        self.longitude_meteoblue = None
        self.geo_location_obj = None 
        self.wind_rose = None 
        self.wind_data_source = '' #METEOBLUE, USER_UPLOAD
        self.wind_engineering_standard = '' #["EU", "AS_NZS", "NEN8100", "LONDON"]
        self.number_wind_directions = None 
        self.exposure_category = []  #["EC1", "EC2", "EC3", "EC4", "EC5", "EC6"] 
        self.wind_velocity_unit = "m/s"
        self.add_surface_roughness = True 
        
        #Pedestrian Comfort Map Variables
        self.pedestrian_comfort_map = []
        self.pedestrian_comfort_surface = None
        self.pedestrian_surface_name = None 
        self.height_above_ground = None
        self.comfort_ground_type = None
        
        #Simulation Control Variables 
        self.max_dir_run_time = 10000
        self.num_of_fluid_passes = 3
        self.sim_control = None 
        
        #Mesh Settings Variables
        self.mesh_fineness = None
        self.reynolds_scaling = None 
        self.mesh_master = None 
        self.min_cell_size = None 
        
        #Simulation Creation Variables
        self.model = None 
        self.simulation_spec = None
        self.simulation_id   = None
        self.simulation_run  = None 
        self.run_id = None
        
    """Functions that allows setting up the API connection"""
    
    def _get_variables_from_env(self):
        
        '''
        looks in your environment and reads the API variables
        
        SimScale API key and URL are read if they are set in the 
        environment as:
            
            SIMSCALE_API_KEY
            SIMSCALE_API_URL

        Returns
        -------
        None.

        '''
        try:
            self.api_key = os.getenv('SIMSCALE_API_KEY')
            self.api_url = os.getenv('SIMSCALE_API_URL')
            self.host = self.api_url + self.version
        except:
            raise Exception("Cannot get Keys from Environment Variables")
        
    def check_api(self):
        '''
        Check API key is set, returns boolean True if not set.
    
        Raises
        ------
        Exception
            If the API key and URL is not set, rasie an exception.
    
        Returns
        -------
        is_not_existent : boolean
            True if not set.
    
        '''
        is_not_existent = not os.getenv("SIMSCALE_API_KEY") or not os.getenv("SIMSCALE_API_URL")
        if is_not_existent:
            raise Exception(
                "Either `SIMSCALE_API_KEY` or `SIMSCALE_API_URL`",
                " environment variable is missing.")
            return is_not_existent
        else:
            print("SimScale API Key and URL found in environment variables.")

    def set_api_connection(self, version=0, server='prod'):
        '''
        Reads API key and URL and returns API clients required.
        
        ----------
        version : int
            Version of SimScale API, at time of writing, only 0 is valid.
            Default is 0.
        
        Returns
        -------
        api_client : object
            An API client that represents the user, and their login 
            credentials.
        api_key_header : object
        api_key : string
            A string that is your API key, read from the environment 
            variables.
        credential : SimscaleCredentials object
            An object contain api keys and credential information
    
        '''
        #Get the API url and key variables from env variables and do a sanity check 
        self._get_variables_from_env()
        self.check_api()
        
        #Setup the API configuration (define host and link the associated key)
        configuration = sim_sdk.Configuration()
        configuration.host = self.host
        configuration.api_key = {self.api_key_header: self.api_key}
        
        #Setup the API client connection 
        self.api_client = sim_sdk.ApiClient(configuration)
        retry_policy = urllib3.Retry(connect=5, read=5, redirect=0, status=5, backoff_factor=0.2)
        self.api_client.rest_client.pool_manager.connection_pool_kw["retries"] = retry_policy
       
        #Define the required API clients for the simulation 
        self.project_api = sim_sdk.ProjectsApi(self.api_client)
        self.storage_api = sim_sdk.StorageApi(self.api_client)
        self.geometry_import_api = sim_sdk.GeometryImportsApi(self.api_client)
        self.geometry_api = sim_sdk.GeometriesApi(self.api_client)
        self.simulation_api = sim_sdk.SimulationsApi(self.api_client)
        self.simulation_run_api = sim_sdk.SimulationRunsApi(self.api_client)
        self.table_import_api = sim_sdk.TableImportsApi(self.api_client)
        self.reports_api = sim_sdk.ReportsApi(self.api_client) 
        self.wind_api = sim_sdk.WindApi(self.api_client)


    def create_project(self, name, description, measurement_system = "SI"):
        '''
        Take a name and description and create a new workbench project

        Parameters
        ----------
        name : str
            A string with the exact name for the new project.
            
        description : str
            A string with the exact description for the new project.

        Returns
        -------
        None.

        '''
        
        try:
            #Check if the project already exists
            projects = self.project_api.get_projects(limit=1000).to_dict()['embedded']
            found = None
            for project in projects:
                if project['name'] == name:
                    found = project
                    print('Project found: \n' + str(found['name']))
                    break
            if found is None:
                raise Exception('could not find project with name: ' + name)
            
            self.project_id = found['project_id']
            self.project_name = name
            print("Cannot create project with the same name, using existing project")
        except:
            #If not then create a new project
            project = sim_sdk.Project(name=name, description=description,
                                      measurement_system = measurement_system)
            project = self.project_api.create_project(project)
            self.project_id = project.project_id
            self.project_name = name        
             
    def zip_cad_for_upload(self, file_name, base_path): 
        
        '''
        Take a list of the CAD file names and their associated path then zips 
        each CAD file separately and submits it for upload 
        
        Note: Have all the CAD files stored in the same directory
        
        Parameters
        ----------
        file_name : list
            A list with the exact names of the CAD files to upload
            
        base_path : Pathlib Path
            path to the directory that contains the CAD files 

        Returns
        -------
        geometry_path : path of the zipped file

        '''
        geometry_path = []
        
        #Loop over the CAD files needed for upload
        for cad in file_name:
            
            #Get the path of each CAD file
            path = base_path / cad
            
            # The output_filename variable saves the zip file at a desired path; 
            # in this case it is same directory
            output_filename = path
             
            #Retruns a zip file(s) path of the associated CAD, 
            geometry_path.append(shutil.make_archive(output_filename, 'zip', path)) 

        return geometry_path
    
    def upload_geometry(self, name, path=None, units="m", _format="STL", facet_split=False):
        '''
        Upload a geometry to the SimScale platform to a preassigned project.
        
        Parameters
        ----------
        name : str
            The name given to the geometry.
            
        path : pathlib.Path, optional
            The path to a geometry to upload. 
            
        units : str, optional
            the unit in which to upload the geometry to SimScale.
            
            The default is "m".
            
        _format : str, optional
            The file format. 
            
            The default is "STL".
            
        facet_split : bool, optional
            Decide on weather to split facet geometry (such as .stl file 
            types). We prefer not to do this for API use.
            
            The default is False.

        Raises
        ------
        TimeoutError
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        self.geometry_name = name
        
        #Check if the geometry already exists
        try:
            project_id = self.project_id
            geometry_api = self.geometry_api
        
            geometries = geometry_api.get_geometries(project_id).to_dict()['embedded']
            found = None
            for geometry in geometries:
                if geometry['name'] == name:
                    found = geometry
                    print('Geometry found: \n' + str(found['name']))
                    break
                        
            if found is None:
                raise Exception('could not find geometry with id: ' + name)
                
            self.geometry_name = found
            self.geometry_id = found["geometry_id"]
            print("Cannot upload geometry with the same name, using existing geometry")

        except:
            
            self.geometry_path = path

            storage = self.storage_api.create_storage()
            with open(self.geometry_path, 'rb') as file:
                self.api_client.rest_client.PUT(url=storage.url, headers={'Content-Type': 'application/octet-stream'},
                                                body=file.read())
            self.storage_id = storage.storage_id

            geometry_import = sim_sdk.GeometryImportRequest(
                name=name,
                location=sim_sdk.GeometryImportRequestLocation(self.storage_id),
                format=_format,
                input_unit=units,
                options=sim_sdk.GeometryImportRequestOptions(facet_split=facet_split, sewing=False, improve=True,
                                                         optimize_for_lbm_solver=True),
            )

            geometry_import = self.geometry_import_api.import_geometry(self.project_id, geometry_import)
            geometry_import_id = geometry_import.geometry_import_id

            geometry_import_start = time.time()
            while geometry_import.status not in ('FINISHED', 'CANCELED', 'FAILED'):
                # adjust timeout for larger geometries
                if time.time() > geometry_import_start + 900:
                    raise TimeoutError()
                time.sleep(10)
                geometry_import = self.geometry_import_api.get_geometry_import(self.project_id, geometry_import_id)
                print(f'Geometry import status: {geometry_import.status}')
            self.geometry_id = geometry_import.geometry_id
        
            
    def set_region_of_interest(self, radius, center ,ground_height, north_angle, wt_size = 'moderate'):
        
        '''
        Define the region of interest of the PWC simulation 
        
        Parameters
        ----------
        radius : int
            radius of the region of interest 
                
        center : list
            list containing the x and y coordinates of the roi center
                
        ground_height: float 
            defines the bottom floor of the wind tunnel 
                
        north_angle: int/float
            defines the north direction of your CAD model 
        
        wt_size : str Optional 
            possiblity to choose from three different wind tunnel sizes 
            modreate, large or custom sizing
                
            The default is moderate
            
        Returns
        -------
        None.

        '''
        
        
        self.roi_radius , self.center   = radius , center
        self.ground_height , self.north_angle = ground_height , north_angle
        self.set_wind_tunnel_size(wt_size)
        
        
        self.region_of_interest = sim_sdk.RegionOfInterest(
                disc_radius=sim_sdk.DimensionalLength(self.roi_radius, "m"),
                center_point=sim_sdk.DimensionalVector2dLength(sim_sdk.DecimalVector2d(self.center[0],self.center[1]), "m"),
                ground_height=sim_sdk.DimensionalLength(self.ground_height, "m"),
                north_angle=sim_sdk.DimensionalAngle(self.north_angle, "°"),
                advanced_settings=sim_sdk.AdvancedROISettings(self.wind_tunnel_size_obj),
                )
      
    def set_wind_tunnel_size(self, wt_size = "moderate"):
        
        '''
        Defines the size of the wind tunnel
        
        note: If a custom wind tunnel size is to be chosen, make sure to run 
        the function set_custom_wt_size to define the size of the custom 
        wind tunnel
        
        Parameters
        ----------
        wt_size : str Optional 
            possiblity to choose from three different wind tunnel sizes 
            modreate, large or custom sizing

        Returns
        -------
        wind_tunnel_size_obj
        
        '''
                
        self.wind_tunnel_size =  wt_size
        
        if self.wind_tunnel_size  == "moderate" : 
            
            self.wind_tunnel_size_obj = sim_sdk.WindTunnelSizeModerate()
        
        elif self.wind_tunnel_size  == "large" : 
            
            self.wind_tunnel_size_obj = sim_sdk.WindTunnelSizeLarge()
      
        else : 
            
            self.wind_tunnel_size_obj  = sim_sdk.WindTunnelSizeCustom(
                self.wind_tunnel_type,
                self.height_extension, 
                self.side_extension, 
                self.inflow_extension, 
                self.outflow_extension,
                )
                
        return self.wind_tunnel_size_obj
        
    def set_custom_wt_size(self, height_ext, side_ext, inflow_ext, outflow_ext):
        
         '''
         Defines the dimensions of the custom wind tunnel
         
         Parameters
         ----------
         height_ext : int 
             height extension of the wind tunnel 
             
        side_ext : int 
            side extension of the wind tunnel
            
        inflow_ext: int 
            extension of the inlet face of the wind tunnel
            
        outflow_ext: int 
            extension of the outlet face of the wind tunnel
    
         Returns
         -------
         None. 
         
         '''
         self.wind_tunnel_type  = 'WIND_TUNNEL_SIZE_CUSTOM'
         self.height_extension  = sim_sdk.DimensionalLength(height_ext, "m")
         self.side_extension    = sim_sdk.DimensionalLength(side_ext, "m")
         self.inflow_extension  = sim_sdk.DimensionalLength(inflow_ext, "m")
         self.outflow_extension = sim_sdk.DimensionalLength(outflow_ext, "m")
        
    
    def set_num_wind_directions(self, num_wind_dir): 
        
         '''
         sets the number of wind directions to be submitted for simulation
         
         Parameters
         ----------
         num_wind_dir : int 
             number of wind directions a choice from : 2, 4, 6, 8, 12, 16 ,36 
             
             note: 36 wind directions is only possible when the wind data is 
             either manually imported or if the simulation is done using 
             the City of London standard 
             
         Returns
         -------
         number_wind_directions  
         
         '''
        
         self.number_wind_directions = num_wind_dir
            
    def set_wind_engineering_standard(self, wind_eng_std):
        
        '''
        set the wind engineering standard type 
        
        choice from : ["EU", "AS_NZS", "NEN8100", "LONDON"]
        
        Parameters
        ----------
        wind_eng_std: str 
            a string of one of the standars mentioned above 
            
        Returns 
        -------
        wind_engineering_standard 
        
        '''
        
        self.wind_engineering_standard = wind_eng_std
    
    def set_wind_exposure_category(self, exposure_categories):
        
        '''
        Set the wind exposure category associated with each incoming wind 
        direction 
        
        The order of the expsure category list must start with north and progress
        in a clockwise fashion
                
        choice from : ["EC1", "EC2", "EC3", "EC4", "EC5", "EC6"] 
        
        Parameters
        ----------
        exposure_categories: list 
            list of the exposure categories of each respective wind direction            
        Returns 
        -------
        exposure_category 
        
        '''
        self.exposure_category = exposure_categories
        
    def set_surface_roughness(self, surface_roughness = True): 
        
        '''
        Set the surface roughness of the wind tunnel floor
        Based on the exposure cateogry of the each wind direction the surface
        roughness of the wind tunnel floor would be mapped accordingly 
        
        Defaults is True 
        
        Parameters
        ----------
        surface_roughness: boolean 
            option to add or ignore surface roughness 
            
        Returns 
        -------
        add_surface_roughness 
        
        '''
        
        self.add_surface_roughness = surface_roughness
        
    def set_wind_data_source(self, data_source): 
        
        '''
        Sets the type of wind data import 
        
        Choice from : [METEOBLUE, USER_UPLOAD]    
        
        Parameters
        ----------
        data_source: str
            string of the name of the wind data type 
            
        Returns 
        -------
        wind_data_source 
        
        '''
        
        self.wind_data_source = data_source 
        
    def set_geographical_location(self, latitude, longitude): 
        '''
        Set the coordinats of the location of interest 
                
        Parameters
        ----------
        latitude: float
            latitudal coordinates
        
        longitude: float
            longitudenal coordinates
         
        Returns 
        -------
        None.  
        
        '''
        #For Meteoblue
        self.latitude_meteoblue  = str(latitude)
        self.longitude_meteoblue = str(longitude)
        # Required for simulation setup and for manual wind data input
        self.latitude  = sim_sdk.DimensionalAngle(latitude, "°")
        self.longitude = sim_sdk.DimensionalAngle(longitude, "°")
        
        self.geo_location_obj = sim_sdk.GeographicalLocation(
            latitude= self.latitude, 
            longitude=self.longitude)       

    def set_velocity_buckets(self): 
        #create a function that allows the user to define up to 16 WD using 
        #velocity buckets
            pass 
        
    def set_wind_rose(self):
    
        '''
        Based on the user choice, the logic for either setting the wind conditons 
        using meteoblue or user upload is invoked. 
        
        note: 
        The user upload method requires the addition of a function that would 
        allow to define the velocity buckets (number of directions)
                        
        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        
        if self.wind_data_source == "METEOBLUE" : 
            
            print("Importing wind data from Meteoblue..")
            try:
                wind_rose_response = self.wind_api.get_wind_data (self.latitude_meteoblue , 
                                                                  self.longitude_meteoblue)
                self.wind_rose = wind_rose_response.wind_rose
                self.wind_rose.num_directions = self.number_wind_directions
                self.wind_rose.exposure_categories = self.exposure_category # ["EC4"] * wind_rose.num_directions
                self.wind_rose.wind_engineering_standard = self.wind_engineering_standard
                self.wind_rose.add_surface_roughness = self.add_surface_roughness
                
            except sim_sdk.ApiException as ae:
                if ae.status == 429:
                    print(
                        f"Exceeded max amount requests, please retry in {ae.headers.get('X-Rate-Limit-Retry-After-Minutes')} minutes")
                    raise sim_sdk.ApiException(ae)
                else:
                    raise ae
        
        else: 
            
            print("Importing wind data from user input..")
            
            self.wind_rose = sim_sdk.WindRose(
                num_directions= self.number_wind_directions, 
                velocity_buckets=[
                    sim_sdk.WindRoseVelocityBucket(_from=None, to=1.234, fractions=[0.1, 0.1, 0.1, 0.1]),
                    sim_sdk.WindRoseVelocityBucket(_from=1.234, to=2.345, fractions=[0.0, 0.1, 0.1, 0.1]),
                    sim_sdk.WindRoseVelocityBucket(_from=2.345, to=3.456, fractions=[0.0, 0.0, 0.1, 0.1]),
                    sim_sdk.WindRoseVelocityBucket(_from=3.456, to=None, fractions=[0.0, 0.0, 0.0, 0.1]),
                ],
                velocity_unit= self.wind_velocity_unit,
                exposure_categories= self.exposure_category,
                wind_engineering_standard= self.wind_engineering_standard,
                wind_data_source= self.wind_data_source ,
                add_surface_roughness= self.add_surface_roughness ,
            )

    def set_wind_conditions(self): 
        
        '''
        Collects the geographical location and wind rose input and submits them
        to the wind conditions setup of the simulation 
        
        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        self.wind_conditions = sim_sdk.WindConditions(
            geographical_location= self.geo_location_obj,
            wind_rose= self.wind_rose)
    
    def set_pedestrian_comfort_map_name(self, name): 
        
        '''
        Define the name of the pedestrian comfort map 
                
        Parameters
        ----------
        name: str
            name of the pedestrian comfort map 
    
        Returns 
        -------
        None.  
        
        '''
        
        self.pedestrian_surface_name = name
    
    def set_height_above_ground(self, height): 
        
        '''
        Define the height above ground of the pedestrian comfort map 
                
        Parameters
        ----------
        height: float 
            comfort map above ground height
    
        Returns 
        -------
        None.  
        
        '''
        self.height_above_ground = sim_sdk.DimensionalLength(height, "m")
        
    
    def set_pedestrian_comfort_ground(self, ground_type): 
        
        '''
        Define the type of the pedestrian comfort map. Choice of: 
            [absolute, relative]
            
        note: 
            The logic for the relative comfort map is not implemented yet. 
            Currently, only absolute comfort maps are supported
                
        Parameters
        ----------
        ground_type: str 
            type of the pedestrian comfort map 
    
        Returns 
        -------
        None.  
        
        '''
        
        if ground_type == "absolute":
        
            self.comfort_ground_type = sim_sdk.GroundAbsolute()
        
        else: 
            #Add code that allows the user to select a face and use that as 
            # a comfort surface
            pass
        
    
    def set_pedestrian_comfort_map(self):
        
        '''
        Submit the information of the pedestrian comfort map to the simulation 
        setup
                
        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        self.pedestrian_comfort_map = [    
            sim_sdk.PedestrianComfortSurface(
            name= self.pedestrian_surface_name,
            height_above_ground=self.height_above_ground,
            ground=self.comfort_ground_type)]
            
            
    def add_more_comfort_maps(self,name,height,ground):
        
        '''
        Allows the user to add more comfort maps depending on the height above 
        ground
                
        Parameters
        ----------
        name: str 
            name of the pedestrian comfort map 
            
        height: float 
            comfort map above ground height
                
        ground_type: str 
            type of the pedestrian comfort map 
    
        Returns 
        -------
        None.  
        
        '''
        
        self.pedestrian_comfort_map.append(   
            sim_sdk.PedestrianComfortSurface(
            name= name,
            height_above_ground= sim_sdk.DimensionalLength(height, "m"), 
            ground=self.comfort_ground_type))
         
    def set_maximum_run_time(self, max_run_time):
        
        '''
        set the maximum runtime of the simulation 
        Parameters
        ----------
        max_run_time: int
        
            maximum simulation runtime

        Returns 
        -------
        None.  
        
        '''
        
        self.max_dir_run_time = sim_sdk.DimensionalTime(max_run_time, "s")
    
    def set_num_fluid_passes(self, fluid_pass = 3): 
        
        '''
        set the number of fluid passes
        Default is 3 
        
        Parameters
        ----------
        fluid_pass: int
            number of fluid passes 
            
        Returns 
        -------
        None.  
        
        '''
        self.num_of_fluid_passes = fluid_pass
    
    def set_simulation_control(self):
        
        '''
        submit the simulation control settings to the simulation setup 
        Default is 3 
        
        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        self.sim_control = sim_sdk.WindComfortSimulationControl(
            max_direction_run_time =self.max_dir_run_time, 
            number_of_fluid_passes = self.num_of_fluid_passes)
    
    
    def set_mesh_min_cell_size(self, min_cell_size): 
        
        '''
        set the minimum cell size in case a 'TargetSize' meshing method is 
        chosen
        
        Parameters
        ----------
        min_cell_size: float 
            minimum cell size of the desired mesh            
            
        Returns 
        -------
        None.  
        
        '''
        
        self.min_cell_size = sim_sdk.DimensionalLength(min_cell_size, "m")
        
    def set_mesh_fineness(self,fineness): 
        
        '''
        Set the fineness of the mesh 
        
        choice from: [VeryCoarse, Coarse, Moderate, Fine, VeryFine, TargetSize]
        
        Parameters
        ----------
        fineness: str 
            fineness  of mesh to be generated             
            
        Returns 
        -------
        None.  
        
        '''
        if fineness == "VeryCoarse": 
            self.mesh_fineness = sim_sdk.PacefishFinenessVeryCoarse()
            
        elif fineness == "Coarse":
            self.mesh_fineness = sim_sdk.PacefishFinenessCoarse()

        elif fineness == "Moderate":
            self.mesh_fineness = sim_sdk.PacefishFinenessModerate()

        elif fineness == "Fine":
            self.mesh_fineness = sim_sdk.PacefishFinenessFine()

        elif fineness == "VeryFine":
            self.mesh_fineness = sim_sdk.PacefishFinenessVeryFine()
    
        elif fineness == "TargetSize": 
            
            self.mesh_fineness = sim_sdk.PacefishFinenessTargetSize(
            type ="TARGET_SIZE",
            minimum_cell_size= self.min_cell_size)
    
                              
    def set_reynolds_scaling(self, scaling = 1.0 , auto_scale = True):
        
        '''
        Set the reynolds scaling of the simulation 
        
        Default is automatic reynolds scaling
        
        note: 
            if auto_scale is set to True then the value of scaling is not 
            taken into consideration 
            
        Parameters
        ----------
        scaling: float  
            reynolds scaling factor 
            
        auto_scale: boolean 
            True for autoscaling and False for manual scaling
            
        Returns 
        -------
        None.  
        
        '''
        if auto_scale == True: 
            
            self.reynolds_scaling = sim_sdk.AutomaticReynoldsScaling(
                            type='AUTOMATIC_REYNOLDS_SCALING')        
        else: 
            
            self.reynolds_scaling = sim_sdk.ManualReynoldsScaling(
                                        type='MANUAL_REYNOLDS_SCALING', 
                                        reynolds_scaling_factor=scaling)
            
    def set_mesh_settings(self):
        
        '''
        Submit the mesh settings to the simulation setup

        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        
        self.mesh_master = sim_sdk.WindComfortMesh(
                            wind_comfort_fineness= self.mesh_fineness,
                            reynolds_scaling_type= self.reynolds_scaling)
        
    def set_simulation_spec(self, simulation_name):
        
        '''
        Set the complete simulation spec and submit to the simulation setup 

        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
                
        self.model = sim_sdk.WindComfort(
            region_of_interest= self.region_of_interest
            ,
            wind_conditions=  sim_sdk.WindConditions(
                     geographical_location= self.geo_location_obj,
                     wind_rose = self.wind_rose)
            ,
            pedestrian_comfort_map=
                    self.pedestrian_comfort_map
            ,
            simulation_control= self.sim_control
            ,
            advanced_modelling=sim_sdk.AdvancedModelling(),
            additional_result_export=sim_sdk.FluidResultControls(
                transient_result_control=sim_sdk.TransientResultControl(
                    write_control=sim_sdk.CoarseResolution(),
                    fraction_from_end=0.1,
                ),
                statistical_averaging_result_control=sim_sdk.StatisticalAveragingResultControlV2(
                    sampling_interval=sim_sdk.CoarseResolution(),
                    fraction_from_end=0.1,
                ),
            ),
            mesh_settings=self.mesh_master,
        )

        self.simulation_spec = sim_sdk.SimulationSpec(name=simulation_name, geometry_id= self.geometry_id, model=self.model)
        
        
    def create_simulation(self):
        
        '''
        Create the simulation setup based on the simulation spec 

        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        self.simulation_id = self.simulation_api.create_simulation(self.project_id, self.simulation_spec).simulation_id
        print(f"simulationId: {self.simulation_id}")


    def estimate_simulation(self):
        '''
        Provide an estimation of the maximum and minimum number of cells, 
        the amount of resources to be used and the total estimated duration of 
        the simulation 

        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        try:
            estimation = self.simulation_api.estimate_simulation_setup(self.project_id, self.simulation_id)
            # print(f"Simulation estimation: {estimation}\n")
            print("*"*10)
            print(f"Simulation estimation:")    
            print("Number of cells: {i} - {k}".format(i = estimation.cell_count.interval_min,
                                                     k = estimation.cell_count.interval_max ))
            print("-"*10)
            print("GPUh consumption: {i} - {k}".format(i = estimation.compute_resource.interval_min,
                                                      k = estimation.compute_resource.interval_max ))
            print("-"*10)
            print("Simulation Time: {i} - {k}".format(i = estimation.duration.interval_min,
                                                      k = estimation.duration.interval_max ))
            print("*"*10)
            
            if estimation.compute_resource is not None and estimation.compute_resource.value > 10.0:
                raise Exception("Too expensive", estimation)
        
            if estimation.duration is not None:
                max_runtime = isodate.parse_duration(estimation.duration.interval_max).total_seconds()
                max_runtime = max(3600, max_runtime * 2)
            else:
                max_runtime = 36000
                print(f"Simulation estimated duration not available, assuming max runtime of {max_runtime} seconds")
        except sim_sdk.ApiException as ae:
            if ae.status == 422:
                max_runtime = 36000
                print(f"Simulation estimation not available, assuming max runtime of {max_runtime} seconds")
            else:
                raise ae
              
                
    def check_simulation_setup(self):
        
        '''
        Conduct a sanity check on the simulation setup before submitting for 
        solve and report back an error message in the terminal in case the setup
        is faulty 
        
        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        check = self.simulation_api.check_simulation_setup(self.project_id, self.simulation_id)
        warnings = [entry for entry in check.entries if entry.severity == "WARNING"]
        print(f"Simulation check warnings: {warnings}")
        errors = [entry for entry in check.entries if entry.severity == "ERROR"]
        if errors:            
            raise Exception("Simulation check failed - Correct the following error:"
                            , check.entries[0].message)

    def start_simulation_run(self, run_name): 
        
        '''
        Start the simulation run 
        Parameters
        ----------

        Returns 
        -------
        None.  
        
        '''
        # Create simulation run
        self.simulation_run = sim_sdk.SimulationRun(name="Run 1")
        self.simulation_run = self.simulation_run_api.create_simulation_run(self.project_id, self.simulation_id, self.simulation_run)
        self.run_id = self.simulation_run.run_id
        print(f"runId: {self.run_id}")
        
        #Start Simulation Run 
        self.simulation_run_api.start_simulation_run(self.project_id, self.simulation_id, self.run_id)
        self.simulation_run = self.simulation_run_api.get_simulation_run(self.project_id, self.simulation_id, self.run_id)

