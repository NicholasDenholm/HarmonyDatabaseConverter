from DatabaseCreator import DatabaseCreator
from PropertiesFileInput import PropertiesFileInput
from PropertiesCreator import PropertiesCreator
from TableLinker import TableLinker
from Input import Input 
import os
import time
import sys
from tqdm import tqdm
import threading
import sqlite3
import pandas as pd

# Function to display a spinner
def spinning_cursor():
    spinner_chars = ['|', '/', '-', '\\']
    idx = 0
    while not stop_spinner_flag:
        sys.stdout.write(f"\r{spinner_chars[idx]} ")  # Overwrite the line
        sys.stdout.flush()  # Force the terminal to update
        idx = (idx + 1) % len(spinner_chars)  # Rotate the spinner characters
        time.sleep(1.0)  # Adjust the spinner speed if needed

def main():

    global stop_spinner_flag
    stop_spinner_flag = False
    
    # Start the spinner in a separate thread
    spinner_thread = threading.Thread(target=spinning_cursor)
    spinner_thread.start()

    try:
        # =======================Input===========================#
        input_instance = Input()
        input_instance.run()

        input_folder = Input.get_input_folder(input_instance) # Main extracted output folder
        input_files = Input.get_input_files(input_instance) # [index, obj1, obj2, ... , PlateResults]
        image_folder = Input.get_image_folder(input_instance) # Main extracted output folder
        image_files = Input.get_image_files(input_instance) # [index, obj1, obj2, ... , PlateResults]
        output_folder = Input.get_output_folder(input_instance)
        database_info = Input.get_database_info(input_instance) # [db_name, db_type, db_path]
        db_file_path = f"{output_folder}\\{database_info[0]}"

        # Start the main timer
        main_start_time = time.time()
        # ===================Database Creation====================== #
        # TODO Take the plate_data from Input_instance and proccess per plate input files
        
        table_names = []
        db_instances = []
        # Create a loading bar for the database creation
        with tqdm(total=len(input_files), desc="Creating Databases", ncols=100) as bar:
            for file in input_files:
                file_name = file.split('\\')[-1]
                table_name = file_name.replace('-', '').replace(' ', '').replace('.csv', '').replace('Index', 'Index_file').replace('_trimmed', '').replace('Objects_Population', '')
                table_names.append(table_name)
                database_instance = DatabaseCreator(file, db_file_path, table_name, input_folder)
                database_instance.run()
                db_instances.append(database_instance)
                print(f"database '{database_info[0]}', and table: {table_name}' succesfully created and populated")
                bar.update(1)  # Update the progress bar after each table is processed
            
        # assuming alphabetical (index table -> 0, object tables... , plate results -> -1)
        object_instances = db_instances[1:-1]

        TableLinker_instance_index = TableLinker(db_file_path, table_names, image_files)
        TableLinker_instance_index.table_name = "Index_file"
        TableLinker_instance_index.add_image_num_index()
        
        cnx = sqlite3.connect(db_file_path) 
        index_df = pd.read_sql_query("SELECT * FROM Index_file", cnx) 
        index_df = index_df[["Row","Column","Field","ImageNumber"]]
        
        #Bug fix and speed up for adding Well db columns
        for instance in object_instances:

            instance.data_frame = pd.merge(instance.data_frame, index_df, how='left', left_on=['Row','Column','Field'], right_on=['Row','Column','Field'])
            instance.column_names.append("ImageNumber")
            instance.trimmed_data_frame = instance.data_frame.iloc[8:, :]
            cnx.cursor().execute(f"ALTER TABLE {instance.table_name} ADD COLUMN ImageNumber NUMERIC;")
            cnx.commit()
            instance.reset_data_and_insert_data_into_table()
        
        cnx = sqlite3.connect(db_file_path) 
        index_df = pd.read_sql_query("SELECT * FROM Index_file", cnx) 
        index_df = index_df[["Row","Column","Field","Well","WellRow","WellColumn"]]
        
        for instance in object_instances:
                
            instance.data_frame = pd.merge(instance.data_frame, index_df, how='left', left_on=['Row','Column','Field'], right_on=['Row','Column','Field'])
            instance.column_names.append("Well")
            instance.column_names.append("WellRow")
            instance.column_names.append("WellColumn")
            instance.trimmed_data_frame = instance.data_frame.iloc[8:, :]
            cnx.commit()
            instance.reset_data_and_insert_data_into_table()

        # Cleanup of temp folders
        input_instance.cleanup_files()
        print("\nDone making tables\n--------------------------\n")

        # ==========================Table Linking============================= #
        # Progress bar for table linking steps
        with tqdm(total=3, desc="Table Linking Progress", ncols=100) as bar:
            # Start the timer
            start_time = time.time()

            TableLinker_instance = TableLinker(db_file_path, table_names, image_files, progress_bar=bar)
            TableLinker_instance.run_1() # main functions
            TableLinker_instance.run_2() # Counting objects in fields
            TableLinker_instance.run_3() # Math functions like mean per field

            # End the timer
            end_time = time.time()

        if bar:
            bar.set_postfix({"step": "Completed"})
            bar.update(bar.total - bar.n)  # Ensure progress reaches 100%
            bar.close()  # Finalize the progress bar
        
        # Calculate elapsed time
        elapsed_time = end_time - start_time
        print(f"Total time taken for Tablelinking: {elapsed_time:.2f} seconds")
        print(f"The {database_info[0]} and the tables {table_names[:]} have been updated\n--------------------------\n")
        
        channel_linked_to_tables = TableLinker_instance.get_channel_link_to_table() #print(channel_linked_to_tables) # {'Hoechst': 'HOECHST 33342', 'PDGFSelected': 'Alexa 647', 'O4Final': 'Alexa 488narrow'}

        image_size_list = TableLinker_instance.get_image_size_list() # [('1080', '1080', 'HOECHST 33342'), , ('1080', '1080', 'Alexa 647'), ('1080', '1080', 'Alexa 488narrow')

        plate_count = TableLinker_instance.get_plate_count()
        print("Plate count is: ", plate_count)
        db_type = database_info[1]
        #TODO make a selector for plate_type from xml file
        #plate_type = "96"

        obj_tables = TableLinker_instance.get_object_tables()
        print("\nObject tables are: ", obj_tables) # Object tables are: ['Hoechst', 'O4Final', 'PDGFSelected']

        # ===================Properties Input===================== #
        with tqdm(total=(len(table_names[1:-1])), desc="Creating Properties Files", ncols=100) as bar:
          
            for table in table_names[1:-1]:

                print(f"\nStarting to create properties file for {table}")

                ChannelName = channel_linked_to_tables[table] # -> 'HOECHST 33342'

                for channels in image_size_list:
                    image_size_x, image_size_y, channel = channels

                    if ChannelName == channel:
                        image_width = image_size_x
                        image_height = image_size_y
                #print(f"for {ChannelName} the image height and width are {image_height}, {image_width}\n")

                # List of strings that are inputted into properties file.
                image_path_cols = [] # Image_Path_Hoechst,Image_Path_O4Final, ...
                image_file_cols = [] # Image_URL_Hoechst,Image_URL_O4Final, ...
                image_name_cols = [] # Hoechst,O4Final, ...
                channels_per_image_cols = [] # 1,1, ...
                valid_image_colors = ["blue", "red", "green", "magenta", "cyan", "yellow", "gray"]
                colour_per_image_cols = []
                count = 0
                for obj in obj_tables:
                    image_path_col_name = f"Image_Path_{obj}"
                    image_file_col_name = f"Image__URL_{obj}"
                    image_name_var_name = f"{obj}"
                    channel_per_image_var = '1'
                    colour_var = valid_image_colors[count]
                    count += 1
                    # Append to the respective lists
                    image_path_cols.append(image_path_col_name)
                    image_file_cols.append(image_file_col_name)
                    image_name_cols.append(image_name_var_name)
                    channels_per_image_cols.append(channel_per_image_var)
                    colour_per_image_cols.append(colour_var)
                # Join the list into a comma-separated string
                image_path_cols_str = ','.join(image_path_cols)
                image_file_cols_str = ','.join(image_file_cols)
                image_name_var_str = ','.join(image_name_cols)
                channel_per_image_var_str = ','.join(channels_per_image_cols) # 1,1,1
                color_per_image_var_str = ','.join(colour_per_image_cols) # blue,red,green

                object_count_name = f"{table}_Number_Object_Number"
                object_X_col = f"{table}_Location_Center_X"
                object_Y_col = f"{table}_Location_Center_Y"
                
                Properties_input_instance = PropertiesFileInput(db_type, 
                                                                db_file_path, 
                                                                image_table="ImageTable", 
                                                                object_table=table, 
                                                                image_id='ImageNumber', 
                                                                object_id=object_count_name, 
                                                                plate_id='Plane', 
                                                                well_id='Well', 
                                                                series_id='Sequence', 
                                                                group_id='Group_id', 
                                                                timepoint_id='Timepoint', 
                                                                object_name='cell,cells', 
                                                                plate_type='96', 
                                                                cell_x_loc=object_X_col, 
                                                                cell_y_loc=object_Y_col, 
                                                                cell_z_loc='',
                                                                image_path_cols=f'{image_path_cols_str}',
                                                                image_file_cols=f'{image_file_cols_str}',
                                                                image_names=f'{image_name_var_str}',
                                                                image_width=image_width,
                                                                image_height=image_height,
                                                                image_channel_colors=f'{color_per_image_var_str}',
                                                                channels_per_image=f'{channel_per_image_var_str}')
            
                Properties_input_instance.run()

                print("PropertiesFileInput finished running")

                # ===================Properties Creation===================== #
                db_type = Properties_input_instance.get_db_type()
                object_table = Properties_input_instance.get_object_table()
                output_filename = f"{output_folder}\\{object_table}.properties"
                
                plate_type = Properties_input_instance.get_plate_type()
                image_names = Properties_input_instance.get_image_names()

                # Get the current directory where the script is located
                current_directory = os.path.dirname(os.path.abspath(__file__))
                # Construct the full path to the template .ini file
                template_filename = os.path.join(current_directory, "PropertiesFileTemplate.ini")
                
                #template_filename = r'C:\Users\nickd\Python\DatabaseCreator\PropertiesFileTemplate.ini'
                
                #print("output filename is: ", output_filename, "plate type is: ", plate_type, "db type is: ", db_type, "Image name: ", image_names, "\n")
                #print("Image names: ", image_names)

                propertiesCreator_instance = PropertiesCreator(Properties_input_instance, template_filename, output_filename, output_folder)
                
                print(f"Instance creation worked for {output_filename}\n")
                propertiesCreator_instance.run()
            
                bar.update(1) 

        # Optionally, set the progress bar to show completion
        if bar:
            bar.set_postfix({"step": "Completed"})
            bar.update(bar.total - bar.n)  # Ensure progress reaches 100%
            bar.close()  # Finalize the progress bar

    except Exception as e:
        print(f"An error occurred at main: {str(e)}")

    finally:
        # Stop the spinner when the task is done
        stop_spinner_flag = True
        spinner_thread.join()  # Wait for the spinner thread to finish
        print("\nALL DONE!!!\n")

    try:
        # End the timer
        main_end_time = time.time()

        # Calculate total elapsed time
        main_elapsed_time = main_end_time - main_start_time
        print(f"Total time for full conversion: {main_elapsed_time:.2f} seconds")
        stop_spinner_flag = True
        spinner_thread.join()  # Wait for the spinner thread to finish
        input("Press Enter to close...")
    
    except KeyboardInterrupt:
        # Handle any interruption gracefully
        stop_spinner_flag = True
        spinner_thread.join()  # Wait for the spinner thread to finish
        sys.stdout.write("\nBye!\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
