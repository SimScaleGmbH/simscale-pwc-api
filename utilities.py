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
from simscale_sdk import Configuration, ApiClient, ProjectsApi, StorageApi, GeometryImportsApi, GeometriesApi, \
    SimulationsApi, SimulationRunsApi, ReportsApi, Project, GeometryImportRequest, ApiException, WindData
from simscale_sdk import GeometryImportRequestLocation, GeometryImportRequestOptions
from simscale_sdk import SimulationSpec, SimulationRun
from simscale_sdk import UserInputCameraSettings, ProjectionType, Vector3D, ModelSettings, Part, \
    ScreenshotOutputSettings, Color, ResolutionInfo, ScreenshotReportProperties, ReportRequest
from simscale_sdk import WindComfort, RegionOfInterest, DimensionalLength, DimensionalVector2dLength, DecimalVector2d, \
    DimensionalAngle, AdvancedROISettings, WindTunnelSizeModerate, WindConditions, GeographicalLocation, WindRose, \
    WindRoseVelocityBucket, PedestrianComfortSurface, GroundAbsolute, WindComfortSimulationControl, AdvancedModelling, \
    TransientResultControl, CoarseResolution, StatisticalAveragingResultControlV2, PacefishFinenessVeryCoarse, \
    WindComfortMesh, DimensionalTime, FluidResultControls

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
        self.api_client  = None
        self.project_api = None
        self.storage_api = None
        self.geometry_import_api = None
        self.geometry_api = None
        self.simulation_api = None
        self.simulation_run_api = None
        self.table_import_api =None
        self.reports_api = None
        
        #Project variables 
        self.project_name = ""
        self.project_id   = ""
        
        #Geometry variables
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
        
        """ If a custom wind tunnel size is to be chosen, make sure to run 
        the function set_custom_wt_size to define the size of the custom 
        wind tunnel"""
        
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
            
            pass
    
        return self.wind_tunnel_size_obj
        
    def set_custom_wt_size(self, height_ext, side_ext, inflow_ext, outflow_ext):
        
        self.wind_tunnel_type = 'WIND_TUNNEL_SIZE_CUSTOM'
        self.height_extension  = sim_sdk.DimensionalLength(height_ext, "m")
        self.side_extension    = sim_sdk.DimensionalLength(side_ext, "m")
        self.inflow_extension  = sim_sdk.DimensionalLength(inflow_ext, "m")
        self.outflow_extension = sim_sdk.DimensionalLength(outflow_ext, "m")
        
      
    def set_simulation_spec(self):
        # Define simulation spec
        model = WindComfort(
            # region_of_interest=RegionOfInterest(
            #     disc_radius=DimensionalLength(150, "m"),
            #     center_point=DimensionalVector2dLength(DecimalVector2d(0, 0), "m"),
            #     ground_height=DimensionalLength(5, "m"),
            #     north_angle=DimensionalAngle(0, "°"),
            #     advanced_settings=AdvancedROISettings(WindTunnelSizeModerate()),
            # )
            region_of_interest= self.region_of_interest
            ,
            wind_conditions=WindConditions(
                geographical_location=GeographicalLocation(
                    latitude=DimensionalAngle(48.135125, "°"), longitude=DimensionalAngle(11.581981, "°")
                ),
                wind_rose=WindRose(
                    num_directions=4,
                    velocity_buckets=[
                        WindRoseVelocityBucket(_from=None, to=1.234, fractions=[0.1, 0.1, 0.1, 0.1]),
                        WindRoseVelocityBucket(_from=1.234, to=2.345, fractions=[0.0, 0.1, 0.1, 0.1]),
                        WindRoseVelocityBucket(_from=2.345, to=3.456, fractions=[0.0, 0.0, 0.1, 0.1]),
                        WindRoseVelocityBucket(_from=3.456, to=None, fractions=[0.0, 0.0, 0.0, 0.1]),
                    ],
                    velocity_unit="m/s",
                    exposure_categories=["EC2", "EC2", "EC2", "EC2"],
                    wind_engineering_standard="EU",
                    wind_data_source="USER_UPLOAD",
                    add_surface_roughness=False,
                ),
            ),
            pedestrian_comfort_map=[
                PedestrianComfortSurface(
                    name="Pedestrian level 1", height_above_ground=DimensionalLength(1.5, "m"), ground=GroundAbsolute()
                )
            ],
            simulation_control=WindComfortSimulationControl(
                max_direction_run_time=DimensionalTime(10000, "s"), number_of_fluid_passes=0.2
            ),
            advanced_modelling=AdvancedModelling(),
            additional_result_export=FluidResultControls(
                transient_result_control=TransientResultControl(
                    write_control=CoarseResolution(),
                    fraction_from_end=0.1,
                ),
                statistical_averaging_result_control=StatisticalAveragingResultControlV2(
                    sampling_interval=CoarseResolution(),
                    fraction_from_end=0.1,
                ),
            ),
            mesh_settings=WindComfortMesh(wind_comfort_fineness=PacefishFinenessVeryCoarse()),
        )

        simulation_spec = SimulationSpec(name="PWC_CustomWT", geometry_id= self.geometry_id, model=model)

        # Create simulation
        simulation_id = self.simulation_api.create_simulation(self.project_id, simulation_spec).simulation_id
        print(f"simulationId: {simulation_id}")
