import configparser
from datetime import datetime
import os
from PropertiesFileInput import PropertiesFileInput

class PropertiesCreator(PropertiesFileInput):

    def __init__(self, properties_input_instance, template_filename, output_filename, output_folder):

        self.db_type = properties_input_instance.get_db_type()
        self.db_file_path = properties_input_instance.get_db_file_path()

        self.image_table = properties_input_instance.get_image_table()
        self.object_table = properties_input_instance.get_object_table()
        self.image_id = properties_input_instance.get_image_id()
        self.object_id = properties_input_instance.get_object_id()
        self.plate_id = properties_input_instance.get_plate_id()
        self.well_id = properties_input_instance.get_well_id()
        self.series_id = properties_input_instance.get_series_id()
        self.group_id = properties_input_instance.get_group_id()
        self.timepoint_id = properties_input_instance.get_timepoint_id()
        self.object_name = properties_input_instance.get_object_name()
        self.plate_type = properties_input_instance.get_plate_type()

        self.cell_x_loc = properties_input_instance.get_cell_x_loc()
        self.cell_y_loc = properties_input_instance.get_cell_y_loc()
        self.cell_z_loc = properties_input_instance.get_cell_z_loc()

        self.template_filename = template_filename
        self.output_filename = output_filename
        self.output_folder = output_folder

        self.image_path_cols = properties_input_instance.get_image_path_cols()
        self.image_file_cols = properties_input_instance.get_image_file_cols()
        self.image_names = properties_input_instance.get_image_names()

        self.image_height = properties_input_instance.get_image_height()
        self.image_width = properties_input_instance.get_image_width()

        self.image_channel_colors = properties_input_instance.get_image_channel_colors()
        self.channel_per_image = properties_input_instance.get_channels_per_image()

    def format_value(self, value):
        """Helper function to format values with single quotes."""
        return f"{value}"

    def run(self):
        # Create a ConfigParser object
        config = configparser.ConfigParser()

        # Define sections and their options
        config['Database Info'] = {
            'db_type': self.format_value(self.db_type),
            'db_sqlite_file': self.format_value(self.db_file_path)
        }

        config['Database Tables'] = {
            'image_table': self.format_value(self.image_table),
            'object_table': self.format_value(self.object_table)
        }

        config['Database Columns'] = {
            'image_id': self.format_value(self.image_id),
            'object_id': self.format_value(self.object_id),
            'plate_id': self.format_value(self.plate_id),
            'well_id': self.format_value(self.well_id),
            'series_id': self.format_value(self.series_id),
            'group_id': self.format_value(self.group_id),
            'timepoint_id': self.format_value(self.timepoint_id),
            'cell_x_loc': self.format_value(self.cell_x_loc),
            'cell_y_loc': self.format_value(self.cell_y_loc),
            'cell_z_loc': self.format_value(self.cell_z_loc)
        }

        config['Image Path and File Name Columns'] = {
            'image_path_cols': self.format_value(self.image_path_cols),
            'image_file_cols': self.format_value(self.image_file_cols),
            'image_thumbnail_cols': self.format_value(''),
            'image_names': self.format_value(self.image_names),
            'image_channel_colors': self.format_value(self.image_channel_colors),
            'channels_per_image': self.format_value(self.channel_per_image),
            'image_channel_blend_modes': self.format_value('')
        }

        config['Dynamic Groups'] = {
            'groups': self.format_value(''),
            'group_SQL_Well': self.format_value(''),
            'group_SQL_Gene': self.format_value(''),
            'group_SQL_Well+Gene': self.format_value('')
        }

        config['Image Filters'] = {
            'filters': self.format_value(''),
            'filter_SQL_EMPTY': self.format_value(''),
            'filter_SQL_CDKs': self.format_value('')
        }

        config['Meta data'] = {
            'object_name': self.format_value(self.object_name),
            'plate_type': self.format_value(self.plate_type)
        }

        config['Excluded Columns'] = {
            'classifier_ignore_columns': self.format_value('')
        }

        config['Other'] = {
            'image_width' : self.format_value(self.image_width),
            'image_height' : self.format_value(self.image_height),
            'image_tile_size': self.format_value('100'),
            'classification_type': self.format_value(''),
            'training_set': self.format_value(''),
            'area_scoring_column': self.format_value(''),
            'class_table': self.format_value(''),
            'check_tables': self.format_value('no'),
            'force_bioformats': self.format_value('no'),
            'use_legacy_fetcher': self.format_value('no'),
            'process_3D': self.format_value('False')
        }

        #print("here")
        # Ensure the output folder exists
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        """Writes the formatted content to the output file."""
        with open(self.output_filename, 'w') as file:
            # Adding a timestamp comment
            timestamp = datetime.now().strftime('%a %b %d %H:%M:%S %Y')
            
            #TODO check if this works
            file.write(f"#{timestamp}\n")
            file.write("\n# ==============================================\n")
            file.write("#\n")
            file.write("# CellProfiler Analyst 3.0 properties file\n")
            file.write("#\n")
            file.write("# ==============================================\n\n")
            #config.write(configfile, space_around_delimiters=False)
            
            # ==== Database Info ====
            file.write("# ==== Database Info ====\n")
            file.write(f"db_type         = {config.get('Database Info', 'db_type', fallback='')}\n")
            file.write(f"db_sqlite_file  = {config.get('Database Info', 'db_sqlite_file', fallback='')}\n\n")

            # ==== Database Tables ====
            file.write("# ==== Database Tables ====\n")
            file.write(f"image_table   = {config.get('Database Tables', 'image_table', fallback='')}\n")
            file.write(f"object_table  = {config.get('Database Tables', 'object_table', fallback='')}\n\n")

            # ==== Database Columns ====
            file.write("# ==== Database Columns ====\n")
            file.write("# Specify the database column names that contain unique IDs for images and\n")
            file.write("# objects (and optionally tables).\n")
            file.write("#\n")
            file.write("# table_id (OPTIONAL): This field lets Classifier handle multiple tables if\n")
            file.write("#          you merge them into one and add a table_number column as a foreign\n")
            file.write("#          key to your per-image and per-object tables.\n")
            file.write("# image_id: must be a foreign key column between your per-image and per-object\n")
            file.write("#           tables\n")
            file.write("# object_id: the object key column from your per-object table\n\n")

            file.write(f"image_id      = {config.get('Database Columns', 'image_id', fallback='')}\n")
            file.write(f"object_id     = {config.get('Database Columns', 'object_id', fallback='')}\n")
            file.write(f"plate_id      = {config.get('Database Columns', 'plate_id', fallback='')}\n")
            file.write(f"well_id       = {config.get('Database Columns', 'well_id', fallback='')}\n")

            # TODO fix this here
            file.write(f"# series_id     = {config.get('Database Columns', 'series_id', fallback='')}\n")
            file.write(f"# group_id      = {config.get('Database Columns', 'group_id', fallback='')}\n")
            file.write(f"# timepoint_id  = {config.get('Database Columns', 'timepoint_id', fallback='')}\n")

            file.write("\n")
            file.write("# Also specify the column names that contain X and Y coordinates for each\n")
            file.write("# object within an image.\n")
            file.write(f"cell_x_loc    = {config.get('Database Columns', 'cell_x_loc', fallback='')}\n")
            file.write(f"cell_y_loc    = {config.get('Database Columns', 'cell_y_loc', fallback='')}\n")
            file.write(f"# cell_z_loc    = {config.get('Database Columns', 'cell_z_loc', fallback='')}\n\n")

            # ==== Image Path and File Name Columns ====
            file.write("# ==== Image Path and File Name Columns ====\n")
            file.write("# Classifier needs to know where to find the images from your experiment.\n")
            file.write("# Specify the column names from your per-image table that contain the image\n")
            file.write("# paths and file names here.\n")
            file.write("#\n")
            file.write("# Individual image files are expected to be monochromatic and represent a single\n")
            file.write("# channel. However, any number of images may be combined by adding a new channel\n")
            file.write("# path and filename column to the per-image table of your database and then\n")
            file.write("# adding those column names here.\n")
            file.write("#\n")
            file.write("# Note that these lists must have equal length!\n\n")

            file.write(f"image_path_cols = {config.get('Image Path and File Name Columns', 'image_path_cols', fallback='')}\n")
            file.write(f"image_file_cols = {config.get('Image Path and File Name Columns', 'image_file_cols', fallback='')}\n")
            file.write(f"image_thumbnail_cols = {config.get('Image Path and File Name Columns', 'image_thumbnail_cols', fallback='')}\n")
            file.write(f"image_names = {config.get('Image Path and File Name Columns', 'image_names', fallback='')}\n")
            file.write(f"image_channel_colors = {config.get('Image Path and File Name Columns', 'image_channel_colors', fallback='')}\n")
            file.write(f"channels_per_image  = {config.get('Image Path and File Name Columns', 'channels_per_image', fallback='')}\n")
            file.write(f"image_channel_blend_modes = {config.get('Image Path and File Name Columns', 'image_channel_blend_modes', fallback='')}\n\n")

            # ==== Dynamic Groups ====
            file.write("# ==== Dynamic Groups ====\n")
            file.write("# Here you can define groupings to choose from when classifier scores your experiment.  (e.g., per-well)\n")
            file.write("# This is OPTIONAL, you may leave \"groups = \".\n")
            file.write("# FORMAT:\n")
            file.write("#   group_XXX  =  MySQL select statement that returns image-keys and group-keys.  This will be associated with the group name \"XXX\" from above.\n")
            file.write("# EXAMPLE GROUPS:\n")
            file.write("#   groups               =  Well, Gene, Well+Gene,\n")
            file.write("#   group_SQL_Well       =  SELECT Per_Image_Table.TableNumber, Per_Image_Table.ImageNumber, Per_Image_Table.well FROM Per_Image_Table\n")
            file.write("#   group_SQL_Gene       =  SELECT Per_Image_Table.TableNumber, Per_Image_Table.ImageNumber, Well_ID_Table.gene FROM Per_Image_Table, Well_ID_Table WHERE Per_Image_Table.well=Well_ID_Table.well\n")
            file.write("#   group_SQL_Well+Gene  =  SELECT Per_Image_Table.TableNumber, Per_Image_Table.ImageNumber, Well_ID_Table.well, Well_ID_Table.gene FROM Per_Image_Table, Well_ID_Table WHERE Per_Image_Table.well=Well_ID_Table.well\n\n")
            '''
            file.write(f"groups = {config.get('Dynamic Groups', 'groups', fallback='')}\n")
            file.write(f"group_sql_well = {config.get('Dynamic Groups', 'group_sql_well', fallback='')}\n")
            file.write(f"group_sql_gene = {config.get('Dynamic Groups', 'group_sql_gene', fallback='')}\n")
            file.write(f"group_sql_well+gene = {config.get('Dynamic Groups', 'group_sql_well+gene', fallback='')}\n\n")
            '''
            # ==== Image Filters ====
            file.write("# ==== Image Filters ====\n")
            file.write("# Here you can define image filters to let you select objects from a subset of your experiment when training the classifier.\n")
            file.write("# FORMAT:\n")
            file.write("#   filter_SQL_XXX  =  MySQL select statement that returns image keys you wish to filter out.  This will be associated with the filter name \"XXX\" from above.\n")
            file.write("# EXAMPLE FILTERS:\n")
            file.write("#   filters           =  EMPTY, CDKs,\n")
            file.write("#   filter_SQL_EMPTY  =  SELECT TableNumber, ImageNumber FROM CPA_per_image, Well_ID_Table WHERE CPA_per_image.well=Well_ID_Table.well AND Well_ID_Table.Gene=\"EMPTY\"\n")
            file.write("#   filter_SQL_CDKs   =  SELECT TableNumber, ImageNumber FROM CPA_per_image, Well_ID_Table WHERE CPA_per_image.well=Well_ID_Table.well AND Well_ID_Table.Gene REGEXP 'CDK.*'\n\n")
            file.write("\n\n")
            '''
            file.write(f"filters = {config.get('Image Filters', 'filters', fallback='')}\n")
            file.write(f"filter_sql_empty = {config.get('Image Filters', 'filter_sql_empty', fallback='')}\n")
            file.write(f"filter_sql_cdks = {config.get('Image Filters', 'filter_sql_cdks', fallback='')}\n\n")
            '''
            # ==== Meta data ====
            file.write("# ==== Meta data ====\n")
            file.write("# What are your objects called?\n")
            file.write("# FORMAT:\n")
            file.write("#   object_name  =  singular object name, plural object name,\n\n")

            file.write(f"object_name = {config.get('Meta data', 'object_name', fallback='')}\n")
            file.write(f"plate_type = {config.get('Meta data', 'plate_type', fallback='')}\n\n")

            # ==== Excluded Columns ====
            file.write("# ==== Excluded Columns ====\n")
            file.write("# OPTIONAL\n")
            file.write("# Classifier uses columns in your per_object table to find rules. It will\n")
            file.write("# automatically ignore ID columns defined in table_id, image_id, and object_id\n")
            file.write("# as well as any columns that contain non-numeric data.\n")
            file.write("#\n")
            file.write("# Here you may list other columns in your per_object table that you wish the\n")
            file.write("# classifier to ignore when finding rules.\n")
            file.write("#\n")
            file.write("# You may also use regular expressions here to match more general column names.\n")
            file.write("#\n")
            file.write("# Example: classifier_ignore_columns = WellID, Meta_.*, .*_Position\n")
            file.write("#   This will ignore any column named \"WellID\", any columns that start with\n")
            file.write("#   \"Meta_\", and any columns that end in \"_Position\".\n")
            file.write("#\n")
            file.write("# A more restrictive example:\n")
            file.write("# classifier_ignore_columns = ImageNumber, ObjectNumber, .*Parent.*, .*Children.*, .*_Location_Center_.*,.*_Metadata_.*\n\n")

            #file.write(f"classifier_ignore_columns = {config.get('Excluded Columns', 'classifier_ignore_columns', fallback='')}\n\n")
            file.write(f"classifier_ignore_columns = table_number_key_column, image_number_key_column, object_number_key_column\n\n")

            # ==== Other ====
            file.write("# ==== Other ====\n")
            file.write("# Specify the approximate diameter of your objects in pixels here.\n")
            file.write("#\n")
            file.write("# Provides the image width and height. Used for per-image classification.\n")
            file.write("# If not set, it will be obtained from the Image_Width and Image_Height\n")
            file.write("# measurements in CellProfiler.\n")
            file.write("\n")
            file.write(f"image_width  = {config.get('Other', 'image_width', fallback='')}\n")
            file.write(f"image_height = {config.get('Other', 'image_height', fallback='')}\n")
            file.write("\n")
            file.write("# OPTIONAL\n")
            file.write("# Image Gallery can use a different tile size (in pixels) to create thumbnails for images\n")
            file.write("# If not set, it will be the same as image_tile_size\n")

            file.write(f"image_tile_size = {config.get('Other', 'image_tile_size', fallback='')}\n\n")

            file.write("# ======== Classification type ========\n")
            file.write("# OPTIONAL\n")
            file.write("# CPA 2.2.0 allows image classification instead of object classification.\n")
            file.write("# If left blank or set to \"object\", then Classifier will fetch objects (default).\n")
            file.write("# If set to \"image\", then Classifier will fetch whole images instead of objects.\n\n")

            file.write(f"classification_type  = {config.get('Other', 'classification_type', fallback='')}\n\n")

            file.write("# ======== Auto Load Training Set ========\n")
            file.write("# OPTIONAL\n")
            file.write("# You may enter the full path to a training set that you would like Classifier\n")
            file.write("# to automatically load when started.\n\n")
            file.write(f"training_set  = {config.get('Other', 'training_set', fallback='')}\n\n")

            file.write("# ======== Area Based Scoring ========\n")
            file.write("# OPTIONAL\n")
            file.write("# You may specify a column in your per-object table which will be summed and\n")
            file.write("# reported in place of object-counts when scoring.  The typical use for this\n")
            file.write("# is to report the areas of objects on a per-image or per-group basis.\n\n")
            file.write(f"area_scoring_column = {config.get('Other', 'area_scoring_column', fallback='')}\n\n")

            file.write("# ======== Output Per-Object Classes ========\n")
            file.write("# OPTIONAL\n")
            file.write("# Here you can specify a MySQL table in your Database where you would like\n")
            file.write("# Classifier to write out class information for each object in the\n")
            file.write("# object_table\n\n")
            file.write(f"class_table  = {config.get('Other', 'class_table', fallback='')}\n\n")

            file.write("# ======== Check Tables ========\n")
            file.write("# OPTIONAL\n")
            file.write("# [yes/no]  You can ask classifier to check your tables for anomalies such\n")
            file.write("# as orphaned objects or missing column indices.  Default is off.\n")
            file.write("# This check is run when Classifier starts and may take up to a minute if\n")
            file.write("# your object_table is extremely large.\n\n")
            file.write(f"check_tables = {config.get('Other', 'check_tables', fallback='no')}\n\n")

            file.write("# ======== Force BioFormats ========\n")
            file.write("# OPTIONAL\n")
            file.write("# [yes/no]  By default, CPA will try to use the imageio library to load images\n")
            file.write("# which are in supported formats, then fall back to using the older BioFormats\n")
            file.write("# loader if something goes wrong. ImageIO is faster but some unusual file\n")
            file.write("# compression formats can cause errors when loading. This option forces CPA to\n")
            file.write("# always use the BioFormats reader. Try this if images aren't displayed correctly.\n\n")
            file.write(f"force_bioformats = {config.get('Other', 'force_bioformats', fallback='no')}\n\n")

            file.write("# ======== Use Legacy Fetcher ========\n")
            file.write("# OPTIONAL\n")
            file.write("# [yes/no]  In CPA 3.0 the object fetching system has been revised to be more\n")
            file.write("# efficient. In the vast majority of cases it should be faster than the previous\n")
            file.write("# versions. However, some complex object filters can still cause problems. If you\n")
            file.write("# encounter slowdowns this setting allows you to switch back to the old method of\n")
            file.write("# fetching and randomisation.\n\n")
            file.write(f"use_legacy_fetcher = {config.get('Other', 'use_legacy_fetcher', fallback='no')}\n\n")

            file.write("# ======== Process as 3D (visualize a different z position per object) ========\n")
            file.write("# OPTIONAL\n")
            file.write("# [yes/no]  In 3D datasets, this optionally displays in CPA classifier a separate\n")
            file.write("# z slice for each object depending on that object's center position in z. Useful\n")
            file.write("# for classifying cells from 3D data.\n\n")
            file.write(f"# process_3D = {config.get('Other', 'process_3D', fallback='False')}\n")

            '''      
            # Write the configuration to the output file
            output_file_path = os.path.join(self.output_folder, self.output_filename)
            with open(output_file_path, 'w') as configfile:
                config.write(configfile)
            print(f"Configuration written to {output_file_path}")
            '''   
        