import easygui as g

class PropertiesFileInput:
    
    def __init__(self, db_type='', 
                 db_sqlite_file='', 
                 image_table='',
                 object_table='', 
                 image_id='', 
                 object_id='', 
                 plate_id='', 
                 well_id='', 
                 series_id='', 
                 group_id='', 
                 timepoint_id='', 
                 object_name='', 
                 plate_type='', 
                 cell_x_loc='', 
                 cell_y_loc='', 
                 cell_z_loc='',
                 image_path_cols='',
                 image_file_cols='',
                 image_names='',
                 image_width='',
                 image_height='',
                 image_channel_colors='',
                 channels_per_image=''):
        
        self.db_type = db_type
        self.db_file_path = db_sqlite_file
        self.image_table = image_table
        self.object_table = object_table
        self.image_id = image_id
        self.object_id = object_id
        self.plate_id = plate_id
        self.well_id = well_id
        self.series_id = series_id  # TODO analyist doesnt like this why?
        self.group_id = group_id  # TODO analyist doesnt like this why?
        self.timepoint_id = timepoint_id  # TODO analyist doesnt like this why?
        self.object_name = object_name
        self.plate_type = plate_type

        self.cell_x_loc = cell_x_loc
        self.cell_y_loc = cell_y_loc
        self.cell_z_loc = cell_z_loc # TODO analyist doesnt like this why?
        
        self.image_path_cols = image_path_cols
        self.image_file_cols = image_file_cols
        self.image_names = image_names          # important for when analyist goes to grab per image measurments?
        
        self.image_width = image_width
        self.image_height = image_height
        
        self.image_channel_colors = image_channel_colors
        self.channels_per_image = channels_per_image
        '''
        self.image_thumbnail_cols = None
        self.image_channel_blend_modes = None
        '''

        

        '''
        self.classifier_ignore_columns = None

        self.classification_type = None
        self.training_set = None
        self.area_scoring_column = None
        self.class_table = None
        self.check_tables = None

        self.force_bioformats = None
        self.use_legacy_fetcher = None
        self.process_3D = None
        '''

    def set_input(self):
    # Define the prompts and titles for each input field
        field2 = [
            "Image Table Name",
            "Object Table Name",
            "Image ID Column Name",
            "Object ID Column Name",
            "Plate ID Column Name",
            "Well ID Column Name",
            "Series ID Column Name",
            "Group ID Column Name",
            "Timepoint ID Column Name",
        ]
        
        fields = [
            "Image Table Name",
            "Object Table Name",
            "Image ID Column Name",
            "Object ID Column Name",
            "Plate ID Column Name",
            "Well ID Column Name",
            "Series ID Column Name",
            "Group ID Column Name",
            "Timepoint ID Column Name",
            "Object Name",
            "Plate Type"
        ]

        # Prompt the user for input
        input_values = g.multenterbox(
            msg="Enter the required information:",
            title="Input Information",
            fields=fields
        )

         # Ensure the input_values list has the expected number of elements
        if input_values and len(input_values) == 11:
            (
                self.image_table,
                self.object_table,
                self.image_id,
                self.object_id,
                self.plate_id,
                self.well_id,
                self.series_id,
                self.group_id,
                self.timepoint_id,
                self.object_name,
                self.plate_type
            ) = input_values
        else:
            print("Error: Input values are not correct or incomplete.")
            
        print("Properties input worked")


        # You can add additional validation here if needed

    #-----------------------Getter methods----------------------
    def get_db_type(self):
        return self.db_type

    def get_db_file_path(self):
        return self.db_file_path

    def get_image_table(self):
        return self.image_table

    def get_object_table(self):
        return self.object_table

    def get_image_id(self):
        return self.image_id

    def get_object_id(self):
        return self.object_id

    def get_plate_id(self):
        return self.plate_id

    def get_well_id(self):
        return self.well_id

    def get_series_id(self):
        return self.series_id

    def get_group_id(self):
        return self.group_id

    def get_timepoint_id(self):
        return self.timepoint_id

    def get_object_name(self):
        return self.object_name

    def get_plate_type(self):
        return self.plate_type
    
    def get_cell_x_loc(self):
        return self.cell_x_loc

    def get_cell_y_loc(self):
        return self.cell_y_loc

    def get_cell_z_loc(self):
        return self.cell_z_loc
    
    def get_image_path_cols(self):
        return self.image_path_cols

    def get_image_file_cols(self):
        return self.image_file_cols
    
    def get_image_names(self):
        return self.image_names
    
    def get_image_width(self):
        return self.image_width
    
    def get_image_height(self):
        return self.image_height
    
    def get_image_channel_colors(self):
        return self.image_channel_colors
    
    def get_channels_per_image(self):
        return self.channels_per_image
    
    '''
    # def get_image_thumbnail_cols(self):
    #     return self.image_thumbnail_cols

    # def get_image_channel_blend_modes(self):
    #     return self.image_channel_blend_modes
    '''

    def run(self):

        print("Properites file input instance starting...")
        #self.set_input()
        # Perform additional operations if needed
        



        

        
