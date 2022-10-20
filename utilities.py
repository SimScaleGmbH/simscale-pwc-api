# -*- coding: utf-8 -*-
"""
Created on Thu Oct 20 10:09:12 2022

@author: mkdei
"""
import os
import time
import zipfile

import isodate
import urllib3
# from simscale_sdk import Configuration, ApiClient, ProjectsApi, StorageApi, GeometryImportsApi, GeometriesApi, \
#     SimulationsApi, SimulationRunsApi, ReportsApi, Project, GeometryImportRequest, ApiException, WindData
# from simscale_sdk import GeometryImportRequestLocation, GeometryImportRequestOptions
# from simscale_sdk import SimulationSpec, SimulationRun
# from simscale_sdk import UserInputCameraSettings, ProjectionType, Vector3D, ModelSettings, Part, \
#     ScreenshotOutputSettings, Color, ResolutionInfo, ScreenshotReportProperties, ReportRequest
# from simscale_sdk import WindComfort, RegionOfInterest, DimensionalLength, DimensionalVector2dLength, DecimalVector2d, \
#     DimensionalAngle, AdvancedROISettings, WindTunnelSizeModerate, WindConditions, GeographicalLocation, WindRose, \
#     WindRoseVelocityBucket, PedestrianComfortSurface, GroundAbsolute, WindComfortSimulationControl, AdvancedModelling, \
#     TransientResultControl, CoarseResolution, StatisticalAveragingResultControlV2, PacefishFinenessVeryCoarse, \
#     WindComfortMesh, DimensionalTime, FluidResultControls

import simscale_sdk as sim_sdk

class PedestrianWindComfort():
    
    def __init__(self): 
        
        #API variables
        self.api_key        = ""
        self.api_url        = ""
        self.api_key_header = "X-API-KEY"
        self.version        = "/v0"
        self.host           = ""
        self.server         = "prod"
        
        #Client Variables
        self.project_api = None
        self.storage_api = None
        self.geometry_import_api = None
        self.geometry_api = None
        self.simulation_api = None
        self.simulation_run_api = None
        self.table_import_api =None
        self.reports_api = None
        
        #Project related variables 
        self.project_name = ""
        self.project_id   = ""
        
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
        api_client = sim_sdk.ApiClient(configuration)
        retry_policy = urllib3.Retry(connect=5, read=5, redirect=0, status=5, backoff_factor=0.2)
        api_client.rest_client.pool_manager.connection_pool_kw["retries"] = retry_policy
       
        #Define the required API clients for the simulation 
        self.project_api = sim_sdk.ProjectsApi(api_client)
        self.storage_api = sim_sdk.StorageApi(api_client)
        self.geometry_import_api = sim_sdk.GeometryImportsApi(api_client)
        self.geometry_api = sim_sdk.GeometriesApi(api_client)
        self.simulation_api = sim_sdk.SimulationsApi(api_client)
        self.simulation_run_api = sim_sdk.SimulationRunsApi(api_client)
        self.table_import_api = sim_sdk.TableImportsApi(api_client)
        self.reports_api = sim_sdk.ReportsApi(api_client) 

    def create_project(self, name, description):
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
            project = sim_sdk.Project(name=name, description=description)
            project = self.project_api.create_project(project)
            self.project_id = project.project_id
            self.project_name = name        