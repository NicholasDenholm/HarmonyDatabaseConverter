import sqlite3
import tkinter as tk
from tkinter import ttk
import os
import re
import tqdm

class TableLinker:

    def __init__(self, db_path, table_names, image_files, progress_bar=None):
        
        self.db_path = db_path
        self.table_name = None # current table 
        self.column_data_type = 'NUMERIC'
        self.table_names = table_names # list of all tables

        self.image_files = image_files
        self.image_info = None  ### Later defined dictionary to hold image info by plate
        self.plate_count = None # defined in check_folders()
        self.image_fodlers = []
        self.channels = []
        self.result_dict = {}

        self.channel_link_to_table = {} # this is really like: table to channel
        # {'Hoechst': 'HOECHST 33342', 'PDGFSelected': 'Alexa 647', 'O4Final': 'Alexa 488narrow'}
        self.image_size_list = []

        self.object_tables = []
        
        self.table_and_measurement_names = {}
        self.table_and_measurement_names_prefix = {}
        self.table_and_object_count = {}

        # Passed progress bar from main
        self.progress_bar = progress_bar  
        
    def run_1(self):
        
        # Update progress bar to match number of tables to process
        if self.progress_bar:
            self.progress_bar.set_postfix({"step": "run_1"})
            self.progress_bar.reset(total=(2*len(self.table_names)))

        for table in self.table_names:
            self.table_name = table
            print(f"\nStarting to link {table}\n")
            
            if self.table_name == self.table_names[0]:
                self.channel_name_getter()
                self.channel_name_and_id_getter()
                self.create_variable_selector(False)
                
                self.add_image_num_index()
                print(f"\nThe {table} has been succesfully updated\n")
                
                if self.progress_bar:
                    self.progress_bar.update(1)

                self.drop_column_in_table(table, "URL")
                self.drop_column_in_table(table, "Unnamed:18")
                self.add_column_in_table(table, "Image_Path")
                self.add_column_in_table(table, "Image__URL")
                
                self.check_folders()

                self.add_image_URL_into_column(table, "Image__URL", self.image_info)
                self.add_image_path_into_column(table, "Image_Path", self.image_info)

            elif self.table_name == self.table_names[-1]: # The results table
                if self.progress_bar:
                    self.progress_bar.update(1)
                # Does this at then end for effeicency
                self.image_size_finder(self.table_names[0])

            else: # object tables
                self.object_tables.append(table)

                cur_channel_name = self.channel_link_to_table[self.table_name] # 'HOECHST 33342' or 'Alexa 647'
                channel_number = self.result_dict[cur_channel_name]
                '''
                #self.add_column_to_object_table(cur_channel_name, "ImageNumber")
                #self.add_column_to_object_table(cur_channel_name, "Sequence")
                #self.add_column_to_object_table(cur_channel_name, "Group_id")
                #self.add_column_to_object_table(cur_channel_name, "ChannelID")

                # Adding and updating the columns in one go instead of ^^^ these 4 ops 
                #self.add_column_list_to_object_table(cur_channel_name, ["ImageNumber", "Sequence", "Group_id", "ChannelID"])


                # Only imgnum is really important, this is a timeconsuming task !!!
                #self.add_column_list_in_batches_to_object_table(cur_channel_name, ["ImageNumber", "Sequence", "Group_id", "ChannelID"])
                # changed it from channel_name str --> channel number int, should go much faster now
                #self.add_column_list_in_batches_to_object_table(channel_number, ["ImageNumber"])

                # These do not matter, but can minimize size of final database
                #self.update_nulls_in_col(table, "NULL", "Compound")
                #self.update_nulls_in_col(table, "NULL", "Concentration")
                #self.update_nulls_in_col(table, "NULL", "CellType")
                #self.update_nulls_in_col(table, "NULL", "CellCount")

                # Batch process if needed
                #self.update_nulls_in_cols_batch(table, "NULL", ["Compound", "Concentration", "CellType", "CellCount"])
                '''
                if self.progress_bar:
                    self.progress_bar.update(1)

                self.add_column_in_table(self.table_names[0], f"Image_Path_{table}")
                self.add_column_in_table(self.table_names[0], f"Image__URL_{table}")
                self.sync_img_path_and_URL(self.table_names[0], cur_channel_name, f"Image_Path_{table}", f"Image__URL_{table}")

                # Flatten table by taking unique Row, Column, Plane, Timepoint, Sequence, Field, ChannelType - ImageSizeY, (PositionXm - ImageNumber), Image_Path_{OBJ}, Image_URL_{OBJ}
                self.flatten_table(self.table_names[0], cur_channel_name, f"Image_Path_{table}", f"Image__URL_{table}")

                # Adds file name into table
                self.add_column_in_table("ImageTable", f"Image_FileName_{table}")
                self.add_file_names("ImageTable", table, f"Image_FileName_{table}")

                measurments = self.get_column_names(table, table)
                print("Measurments are", measurments)
                self.table_and_measurement_names[table] = measurments

                print(f"\nTable {self.table_name} succesfully updated\n")
            
            # always the 2nd iteration of the updated progress since always at least 1 type of table
            if self.progress_bar:
                self.progress_bar.update(1)

        # Optionally, set the progress bar to show completion
        if self.progress_bar:
            self.progress_bar.set_postfix({"step": "Completed"})
            self.progress_bar.update(self.progress_bar.total - self.progress_bar.n)  # Ensure progress reaches 100%
            self.progress_bar.close()  # Finalize the progress bar
        
        self.drop_table(self.table_names[0]) # Drops the index_table
        print("\nFinished updating tables")
        print("--------------------------\n")
        
    def run_2(self):
        print("Gathering well counts\n")

        # Update progress bar to match number of object tables to process
        if self.progress_bar:
            self.progress_bar.set_postfix({"step": "run_2"})
            self.progress_bar.reset(total=(5*len(self.object_tables)))
        
        for table_name in self.object_tables:
            # Define the new column name for object counts
            object_count_col_name = f"{table_name}_Number_Object_Number"
            self.add_column_in_table(table_name, object_count_col_name)
            
            if self.progress_bar:
                self.progress_bar.update(1) 

            # Copy values from ObjectNo to the new column
            #TODO This method is slow
            self.copy_column_values("ObjectNo", object_count_col_name, table_name)
            #self.copy_column_values_fast("ObjectNo", object_count_col_name, table_name)
            
            #TODO This method is slow
            # Drop the original ObjectNo column
            self.drop_column_in_table(table_name, "ObjectNo")
            #self.drop_column_in_table_fast(table_name, "ObjectNo")
            
            if self.progress_bar:
                self.progress_bar.update(1)
            
            # Do the same for X and Y
            object_X_col = f"{table_name}_Location_Center_X"
            object_Y_col = f"{table_name}_Location_Center_Y"
            self.add_column_in_table(table_name, object_X_col)
            self.add_column_in_table(table_name, object_Y_col)
            
            #TODO this method is very slow
            self.copy_column_values("X", object_X_col, table_name)
            self.copy_column_values("Y", object_Y_col, table_name)
            #self.copy_column_values_fast("X", object_X_col, table_name)
            #self.copy_column_values_fast("Y", object_Y_col, table_name)
            
            if self.progress_bar:
                self.progress_bar.update(1)

            #TODO this method is very slow
            # Drop the original X, Y columns
            self.drop_column_in_table(table_name, "X")
            self.drop_column_in_table(table_name, "Y")
            #self.drop_column_in_table_fast(table_name, "X")
            #self.drop_column_in_table_fast(table_name, "Y")
            
            if self.progress_bar:
                self.progress_bar.update(1)

            # Create a new column in ImageTable for object sums
            obj_sum_col = f"Image_Count_{table_name}"
            self.add_column_in_table("ImageTable", obj_sum_col)

            # Count objects per image and store the result
            self.table_and_object_count = self.count_objects_per_image(table_name, object_count_col_name)

            updates = []  # List to collect updates

            # Iterate through the counts and prepare the update data
            for well_id, fields_and_counts_list in self.table_and_object_count.items():
                for field, count in fields_and_counts_list:
                    # Append the data to updates list, in the format (well, field_id, measurement, measurement_column)
                    # Assuming obj_sum_col is the measurement column
                    updates.append((well_id, field, count, obj_sum_col))  # Adding the column name to each tuple
            
            # Once all updates are collected, call the batch update method
            if updates:
                self.update_image_table_batch(updates)  # Pass the updates to the batch method
                
            if self.progress_bar:
                self.progress_bar.update(1)

        # Optionally, set the progress bar to show completion
        if self.progress_bar:
            self.progress_bar.set_postfix({"step": "Completed"})
            self.progress_bar.update(self.progress_bar.total - self.progress_bar.n)  # Ensure progress reaches 100%
            self.progress_bar.close()  # Finalize the progress bar

        print("\nDone counting wells")
        print("--------------------------\n")

    def run_3(self):

        print("Gathering Measurments")
        # Update the measurements using the helper function with a specified prefix
        self.table_and_measurement_names_prefix = self.prepend_prefix_to_measurements(self.table_and_measurement_names, "Per_Field")

        # Update progress bar to match number of measurement tasks to process
        if self.progress_bar:
            self.progress_bar.set_postfix({"step": "run_3"})
            self.progress_bar.reset(total=len(self.table_and_measurement_names_prefix))

        for obj_table, measurements in self.table_and_measurement_names_prefix.items():
            # The measure_list is now correctly fetched inside the loop
            measure_list = self.table_and_measurement_names[obj_table]

            # Make sure that measure_list and measurements have the same length and correspond correctly
            assert len(measure_list) == len(measurements), f"Mismatch between measure_list and measurements for {obj_table}"

            # Collect updates for batch processing
            batch_updates = []

            # Process each measurement
            for index in range(len(measure_list)):
                # Used for single column updates
                measure_name = measure_list[index]
                
                # Calculate the mean values using the helper function {Well : [Field, mean_measurement]}
                print(f"Calculating mean for: {measure_name}")
                # A dictionary mapping well_id to a list of [field_id, average_value]
                mean_values = self.calculate_average_per_well_and_field(obj_table, measure_name)

                measurement_column = measurements[index]
                # Add the column to the ImageTable for each measurement
                self.add_column_in_table("ImageTable", measurement_column)

                # Collect updates for each measurement (well_id, field_id, mean_measurement, column)
                for well_id, field_and_measurements in mean_values.items():
                    for field_id, mean_measurement in field_and_measurements:
                        batch_updates.append((well_id, field_id, mean_measurement, measurement_column))

            # Now call the optimized batch processing method for all measurements in the batch
            if batch_updates:

                self.update_image_table_batch(batch_updates)

            if self.progress_bar:
                self.progress_bar.update(1) 

        # Optionally, set the progress bar to show completion
        if self.progress_bar:
            self.progress_bar.set_postfix({"step": "Completed"})
            self.progress_bar.update(self.progress_bar.total - self.progress_bar.n)  # Ensure progress reaches 100%
            self.progress_bar.close()  # Finalize the progress bar

        print("\nDone gathering measurments")
        print("--------------------------\n")
        
    #--------------------Methods----------------------

    def channel_name_getter(self):

        unique_channels=[]

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            cursor.execute(f"SELECT DISTINCT ChannelName FROM {self.table_name};")

            unique_channels = [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as error:
                print(f"Error accessing SQLite database to retrieve channel names: {error}")
        finally:
            # close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        self.channels = unique_channels

    def channel_name_and_id_getter(self):
        """
        Sets a dictionary to {ChannelName : ChannelID} which is a str and int
        Args: None
        """
        # Initialize an empty dictionary to store the ChannelID -> ChannelName mapping
        result_dict = {}

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Fetch distinct ChannelID and ChannelName pairs
            cursor.execute(f"SELECT DISTINCT ChannelID, ChannelName FROM {self.table_name};")
            rows = cursor.fetchall()

            # Map each ChannelID to its corresponding ChannelName
            for row in rows:
                channel_id, channel_name = row
                result_dict[channel_name] = channel_id

        except sqlite3.Error as error:
            print(f"Error accessing SQLite database: {error}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        # Store the result dictionary as an instance variable
        self.result_dict = result_dict

    def create_variable_selector(self, test_mode=False):
        # If in test mode, just set the variables and return immediately
        if test_mode:

            # Hardcoded channel-table pairings for test mode
            self.channels = ['HOECHST 33342', 'Alexa 647', 'Alexa 488narrow']
            self.channel_link_to_table = {'Hoechst': 'HOECHST 33342', 'PDGFSelected': 'Alexa 647', 'O4Final': 'Alexa 488narrow'}

            # Set the class variables without opening the GUI
            print("Test mode active. Variables set:")
            print(f"Channels: {self.channels}")
            print(f"Table-Link: {self.channel_link_to_table}")
            return  # Skip further processing and return
        
        # Exclude the first and last table names
        filtered_tables = self.table_names[1:-1]

        def on_link():

            if test_mode:
                print("Test mode is active. No linking will occur.")
                return  # Exits early if in test mode
            
            selected_channel = channel_combo.get()
            selected_table = table_combo.get()
            print(f"Linking channel '{selected_channel}' to table '{selected_table}'.")
            self.channel_link_to_table[selected_table] = selected_channel

            # Remove the linked channel from the dropdown
            '''
            if selected_channel in self.channels:
                self.channels.remove(selected_channel)
                channel_combo['values'] = self.channels  # Update the combobox values
            '''
            # Optionally remove the selected table from the dropdown as well
            if selected_table in filtered_tables:
                filtered_tables.remove(selected_table)
                table_combo['values'] = filtered_tables  # Update the combobox values

        def on_done():
            print("Done button clicked. Closing the application.")
            root.destroy()  # Close the window

        # Create the main application window
        root = tk.Tk()
        root.title("Channel-Table Linker")
        root.geometry("300x250")
        root.configure(bg='#DCDCDC')

        # Create a label for channel selection
        channel_label = tk.Label(root, text="Select a channel:", bg='#f0f0f0', fg='#333333')
        channel_label.grid(row=0, column=0, pady=10, padx=20)  # Align to the right

        # Create a dropdown (combobox) for channels
        channel_combo = ttk.Combobox(root, values=self.channels, width=40)  # Set width here
        channel_combo.grid(row=1, column=0, pady=10, padx=20)

        # Create a label for table selection
        table_label = tk.Label(root, text="Select a object table:", bg='#f0f0f0', fg='#333333')
        table_label.grid(row=2, column=0, pady=10, padx=20)  # Align to the right

        # Create a dropdown (combobox) for tables
        table_combo = ttk.Combobox(root, values=filtered_tables, width=40)  # Set width here
        table_combo.grid(row=3, column=0, pady=10, padx=20)

        # Create a button to link the selected channel and table
        link_button = tk.Button(root, text="Link", command=on_link, bg='#4CAF50', fg='white')
        link_button.grid(row=4, column=0, pady=10, padx=(0, 40))  # Align right with padding

        # Create a "Done" button to close the window
        done_button = tk.Button(root, text="Done", command=on_done, bg='#f44336', fg='white')
        done_button.grid(row=4, column=0, pady=10, padx=(40, 0))  # Next to the link button

        # Start the GUI event loop
        root.mainloop()

    def sync_img_path_and_URL(self, table, channel ,col1, col2):
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Execute query to retrieve rows and columns
            cursor.execute(f"SELECT ImageNumber, Image_Path, Image__URL FROM {table} WHERE ChannelName = ?;", (channel,))
            # Fetch all rows (ChannelName, ImageNumber, Image_Path_table, Image_URL_table) from the result set
            rows = cursor.fetchall()

            for row in rows:
                image_number, image_path, image_URL = row
                
                cursor.execute(f"UPDATE {table} SET {col1} = ?, {col2} = ? WHERE ChannelName = ? AND ImageNumber = ?;",
                    (image_path, image_URL, channel, image_number))

            connection.commit()

        except sqlite3.Error as error:
            print(f"Error syncing the image path and URL {error}")
        finally: # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_file_names(self, table, channel, col):

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Check if ImageTable exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ImageTable';")
            exists = cursor.fetchone()

            if (exists):
                cursor.execute(f"SELECT ImageNumber, Image__URL_{channel} FROM {table};")

                # Fetch all rows (ImageNumber, Row, Column, Field, Image_Path_table, Image_URL_table) from the result set
                rows = cursor.fetchall()

                for row in rows:

                    image_number, url = row

                    match = re.search(r'[^\\]+$', url)
                    if match:
                        file_name = match.group(0) 
                    else:
                        print(f"No file name for {url}")

                    cursor.execute(f"UPDATE ImageTable SET {col} = ? WHERE ImageNumber = ?;",
                        (file_name, image_number))
                    
                connection.commit()
                print("ImageTable created successfully.\n")
            else:
                print("error adding image names to table")

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            
        finally:
            if connection:
                connection.close()
    
    def flatten_table(self, table, channel ,col1, col2):

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Check if ImageTable exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ImageTable';")
            exists = cursor.fetchone()
        
            if not (exists):
                # Adjusted SQL query with aggregation
                query = f"""
                CREATE TABLE IF NOT EXISTS ImageTable AS  
                SELECT 
                    ImageNumber, 
                    Row, 
                    Column, 
                    Plane, 
                    Timepoint, 
                    Sequence, 
                    Field, 
                    ChannelType, 
                    ImageSizeX, 
                    ImageSizeY, 
                    PositionXm, 
                    PositionYm, 
                    Well, 
                    WellRow, 
                    WellColumn, 
                    MAX({col1}) AS {col1},
                    MAX({col2}) AS {col2}
                FROM 
                    {table}
                GROUP BY 
                    ImageNumber, Row, Column, Plane, Timepoint, Sequence, Field, ChannelType, ImageSizeX, ImageSizeY, PositionXm, PositionYm, Well, WellRow, WellColumn;
                """
                cursor.execute(query)
                print("ImageTable created successfully.\n")
            else:
                self.add_column_in_table("ImageTable", col1)
                self.add_column_in_table("ImageTable", col2)

                # If the table exists, aggregate data into a temporary table first
                temp_query = f"""
                CREATE TEMP TABLE TempImageTable AS  
                SELECT 
                    ImageNumber, 
                    Row, 
                    Column, 
                    Plane, 
                    Timepoint, 
                    Sequence, 
                    Field, 
                    ChannelType, 
                    ImageSizeX, 
                    ImageSizeY, 
                    PositionXm, 
                    PositionYm, 
                    Well, 
                    WellRow, 
                    WellColumn, 
                    MAX({col1}) AS {col1},
                    MAX({col2}) AS {col2}
                FROM 
                    {table}
                GROUP BY 
                    ImageNumber, Row, Column, Plane, Timepoint, Sequence, Field, ChannelType, ImageSizeX, ImageSizeY, PositionXm, PositionYm, Well, WellRow, WellColumn;
                """
                cursor.execute(temp_query)

                cursor.execute(f"SELECT ImageNumber, Row, Column, Field, {col1}, {col2} FROM TempImageTable;")
                # Fetch all rows (ImageNumber, Row, Column, Field, Image_Path_table, Image_URL_table) from the result set
                rows = cursor.fetchall()

                for row in rows:
                    
                    image_number, row, col, field, image_path, image_URL = row
                    
                    cursor.execute(f"UPDATE ImageTable SET {col1} = ?, {col2} = ? WHERE ImageNumber = ? AND Row = ? AND Column = ? AND Field = ?;",
                        (image_path, image_URL, image_number, row, col, field))

                connection.commit()
                print("ImageTable updated successfully.")


        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            if connection:
                connection.close()

    def prepend_prefix_to_measurements(self, table_and_measurement_names, prefix):
        """
        Prepend a specified prefix to each measurement in the given dictionary.

        Args:
            table_and_measurement_names (dict): A dictionary where keys are table names
                                                and values are lists of measurement names.
            prefix (str): The prefix to prepend to each measurement name.

        Returns:
            dict: Updated dictionary with the specified prefix prepended to each measurement name.
        """
        updated_dict = {}
        prefix_length = len(prefix) + 1  # Length of prefix plus underscore

        for table, measurements in table_and_measurement_names.items():
            # Prepend the specified prefix and truncate to 64 characters
            updated_measurements = [
                f"{prefix}_{measurement}"[:64] for measurement in measurements
            ]
            
            # If the combined length exceeds 64 characters, adjust the measurement name
            updated_measurements = [
                f"{prefix}_{measurement}"[:64] if len(f"{prefix}_{measurement}") <= 64
                else f"{prefix}_{measurement[:64 - prefix_length]}"  # Truncate measurement part if needed
                for measurement in measurements
            ]
            
            # Store the updated measurements in the new dictionary
            updated_dict[table] = updated_measurements

        return updated_dict

    #--------------------Arithmetic----------------------

    def calculate_average_per_well_and_field(self, obj_table, column):
        """
        Calculate the average values for each field for each well.

        Args:
            db_path (str): Path to the SQLite database.

        Returns:
            dict: A dictionary mapping well_id to a list of [field_id, average_value].
        """
        averages = {}

        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = f"""
        SELECT 
            Well,
            Field,
            AVG({column}) AS {column}
        FROM 
            {obj_table}
        GROUP BY 
            Well, Field;
        """

        try:
            cursor.execute(query)
            results = cursor.fetchall()

            # Debugging: Print the results to ensure grouping is correct
            '''
            print("Query Results (Well, Field, Average):")
            for row in results:
                print(row)
                '''

            # Structure results into a dictionary
            for well_id, field_id, average_value in results:
                if well_id not in averages:
                    averages[well_id] = []
                averages[well_id].append([field_id, average_value])

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        finally:
            # Close the database connection
            conn.close()

        # Debugging: Print the averages to ensure they are calculated correctly
        '''
        print("Averages by Well:")
        for well, fields in averages.items():
            print(f"Well {well}: {fields}")
            '''

        return averages
    

    # COUNT works here!!
    def update_image_table_batch(self, batch_updates):
        """
        Perform a batch update for the image table.
        
        Args:
            batch_updates (list): A list of tuples containing (well, field_id, mean_measurement, measurement_column)
        """
        try:
            # Ensure the column name is valid and part of the query
            if not batch_updates:
                return

            # Open the database connection
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                cursor.execute("PRAGMA synchronous = OFF;")
                cursor.execute("PRAGMA journal_mode = MEMORY;")
                
                # Begin a transaction
                cursor.execute("BEGIN TRANSACTION;")

                # Group updates by measurement column
                # This will create a dictionary of column_name -> list of updates
                updates_by_column = {}
                for well, field_id, mean_measurement, measurement_column in batch_updates:
                    if measurement_column not in updates_by_column:
                        updates_by_column[measurement_column] = []
                    updates_by_column[measurement_column].append((well, field_id, mean_measurement))
                
                # Now process each measurement column batch separately
                for measurement_column, updates in updates_by_column.items():
                    # Create the query for the batch update with dynamic column name
                    query = f"""
                    UPDATE ImageTable
                    SET {measurement_column} = ?
                    WHERE Well = ? AND Field = ?
                    """

                    # Prepare data for batch update (excluding column name from parameters)
                    data_to_update = [(mean_measurement, well, field_id) for well, field_id, mean_measurement in updates]

                    # Perform the batch update for this column
                    cursor.executemany(query, data_to_update)


                # Commit all changes after batch processing
                conn.commit()

                print(f"Batch update completed with {len(batch_updates)} updates.\n") 
               
        except sqlite3.Error as e:
            print(f"SQLite error during batch update: {e}")

    def update_image_table(self, well_id, field_id, value_to_insert, column):
        """
        Update the specified measurement column in ImageTable with the mean value, 
        but only if the column is not already occupied.

        Args:
            well_id (str): The identifier for the well to update.
            field_id (str): The identifier for the field to update.
            value_to_insert (float): The mean value to set in the column.
            column (str): The name of the column to update.
        """
        # TODO make this work for multiple plates
        # TODO Idea use image number to specify this, since plate 1 and 2 A01 will have different img nums

        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor() 

        try:
            # First, check if the column already contains a value for this well and field
            check_query = f"""
            SELECT {column} FROM ImageTable
            WHERE Well = ? AND Field = ?;
            """
            cursor.execute(check_query, (well_id, field_id))
            existing_value = cursor.fetchone()

            if existing_value is None or existing_value[0] is None:
                # If no value exists or the value is None, proceed with the update
                update_query = f"""
                UPDATE ImageTable
                SET {column} = ?
                WHERE Well = ? AND Field = ?;
                """
                cursor.execute(update_query, (value_to_insert, well_id, field_id))
                conn.commit()
                #print(f"Column {column} updated for Well {well_id} and Field {field_id}")
            else:
                print(f"Column {column} for Well {well_id} and Field {field_id} is already occupied. Skipping update.")
                
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            # Close the database connection
            conn.close()

    def count_objects_per_image(self, obj_table, column):
        obj_count = {}

        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Execute the SQL query to count objects in each Well and Field
        query = f"""
        SELECT 
            Well,
            Field,
            COUNT(*) AS object_count  -- Count the number of rows (objects) per Well and Field
        FROM 
            {obj_table}
        GROUP BY 
            Well, Field;
        """

        try:
            cursor.execute(query)
            results = cursor.fetchall()

            # Structure results into a dictionary
            for well_id, field_id, num_of_obj in results:
                if well_id not in obj_count:
                    obj_count[well_id] = []
                # Check if num_of_obj is None (NULL) and assign 0 if it is
                if num_of_obj is None:
                    num_of_obj = 'nan'
                obj_count[well_id].append([field_id, num_of_obj])

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        finally:
            # Close the database connection
            conn.close()
        return obj_count

    #--------------------Adding and Dropping----------------------

    def drop_column_in_table(self, table_name: str, col_to_del: str):
        try:
            # Using 'with' statement to handle the connection automatically
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()

                # Retrieve the columns from the table
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [column[1] for column in cursor.fetchall()]

                if col_to_del not in columns:
                    # If the column doesn't exist, print a message and return
                    print(f"{col_to_del} doesn't exist in {table_name}. No action taken.")
                    return  # Exit early if the column doesn't exist

                # For debugging
                #print(f"Column '{col_to_del}' exists. Proceeding to drop it.")

                # Drop the column using the ALTER TABLE command
                cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN '{col_to_del}';")

                # Commit changes to the database
                connection.commit()
                print(f"Column '{col_to_del}' was deleted successfully.")

        except sqlite3.Error as error:
            print(f"Error while dropping the column '{col_to_del}' in table '{table_name}': {error}")

    def add_column_in_table(self, table_name: str, col_to_add: str):
        try:
            # Using 'with' statement to handle the connection automatically
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()

                # Retrieve the columns from the table
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [column[1] for column in cursor.fetchall()]

                if col_to_add not in columns:  # Check if the column doesn't exist
                    # If the column doesn't exist, add it
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_to_add} {self.column_data_type};")
                    # Commit changes to the database
                    connection.commit()
                    print(f"The {col_to_add} column was added successfully.")
                else:
                    print(f"The {col_to_add} column already exists.")

        except sqlite3.Error as error:
            print(f"Error while adding the column '{col_to_add}' in table '{table_name}': {error}")

    # NOT used
    def drop_column_in_table_fast(self, table_name: str, col_to_del: str):
        try:
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()

                # PRAGMA settings to optimize speed
                cursor.execute("PRAGMA synchronous = OFF;")
                cursor.execute("PRAGMA journal_mode = MEMORY;")
                cursor.execute("PRAGMA temp_store = MEMORY;")

                # Retrieve the columns from the table
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [column[1] for column in cursor.fetchall()]

                if col_to_del not in columns:
                    print(f"{col_to_del} doesn't exist in {table_name}. No action taken.")
                    return

                # Create a new table with all columns except the one to delete
                new_columns = [col for col in columns if col != col_to_del]
                new_table_name = f"{table_name}_temp"

                column_definitions = ", ".join([f"`{col}`" for col in new_columns])
                cursor.execute(f"CREATE TABLE {new_table_name} AS SELECT {column_definitions} FROM {table_name};")

                # Drop the old table
                cursor.execute(f"DROP TABLE {table_name};")

                # Rename the new table to the original table name
                cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name};")

                # Commit the changes
                connection.commit()

                print(f"Column '{col_to_del}' was deleted successfully from '{table_name}'.")

        except sqlite3.Error as error:
            print(f"Error while dropping the column '{col_to_del}' in table '{table_name}': {error}")

    def add_image_URL_into_column(self, table_name:str, col_to_alter:str, image_info):

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [column[1] for column in cursor.fetchall()]
            if col_to_alter not in columns: 
                print(f"{col_to_alter} doesnt exist")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_to_alter} {self.column_data_type};")
            else:
                print(f"{col_to_alter} column exists")
                

            # Insert data into the specified table
            for plate_label, images in image_info.items():
                #print(f"{plate_label}\n", images)
                for image, key in images.items():
                    #print(f"Image is: {image}, key is: {key}")
                    # key = (Row, Column, Field, Plane, ChannelID, Sequence)
                    row_number = key[0]
                    column_number = key[1]
                    field_number = key[2]
                    channel_number = key[4]
            
                    # Now update the ImageNumber based on the stored mapping
                    cursor.execute(f"UPDATE {self.table_name} SET {col_to_alter} = ? WHERE Row = ? AND Column = ? AND Field = ? AND ChannelID = ?;",
                                (image, row_number, column_number, field_number, channel_number))

            # Commit changes and close the connection
            connection.commit()
            print(f"The {col_to_alter} column updated successfully.")

        except sqlite3.Error as error:
            print(f"While adding values to the {col_to_alter} column there was an error {error}")
            #connection.rollback()

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_image_path_into_column(self, table_name:str, col_to_alter:str, image_info):

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [column[1] for column in cursor.fetchall()]
            if col_to_alter not in columns: 
                print(f"{col_to_alter} doesnt exist")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_to_alter} {self.column_data_type};")
            else:
                print(f"\n{col_to_alter} column exists")
                
            # Insert data into the specified table
            for plate_label, images in image_info.items():
                for image, key in images.items():
                    row_number = key[0]
                    column_number = key[1]
                    field_number = key[2]
                    channel_number = key[4]
                    folder = self.image_fodlers[plate_label-1] #
                    # key = (Row, Column, Field, Plane, ChannelID, Sequence)
                    # Now update the ImageNumber based on the stored mapping
                    cursor.execute(f"UPDATE {self.table_name} SET {col_to_alter} = ? WHERE Row = ? AND Column = ? AND Field = ? AND ChannelID = ?;",
                                (folder, row_number, column_number, field_number, channel_number))

            # Commit changes and close the connection
            connection.commit()
            print(f"The {col_to_alter} column updated successfully.")

        except sqlite3.Error as error:
            print(f"While adding values to the {col_to_alter} column there was an error {error}")

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def copy_column_values(self, source_column, target_column, table_name):
        """
        Copy values from one column to another in the specified table.

        Args:
            source_column (str): The column from which to copy values.
            target_column (str): The column to which values will be assigned.
            table_name (str): The name of the table where the operation will take place.
        """
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Prepare the SQL update statement
            update_query = f"""
            UPDATE {table_name}
            SET {target_column} = {source_column};
            """

            # Execute the update statement
            cursor.execute(update_query)

            # Commit the changes
            conn.commit()

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            # Close the database connection
            conn.close()
    
    # NOT used
    def copy_column_values_fast(self, source_column, target_column, table_name):
        """
        Copy values from one column to another in the specified table.

        Args:
            source_column (str): The column from which to copy values.
            target_column (str): The column to which values will be assigned.
            table_name (str): The name of the table where the operation will take place.
        """
        print(f"Copying values from {source_column} to {target_column} in table {table_name}...")

        # Connect to the database (reuse the same connection if possible for better performance)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Set optimal SQLite settings for performance
            cursor.execute("PRAGMA synchronous = OFF;")  # Disable disk sync for faster writes
            cursor.execute("PRAGMA journal_mode = MEMORY;")  # Store journal in memory
            cursor.execute("PRAGMA temp_store = MEMORY;")  # Use memory for temp files
            cursor.execute("PRAGMA cache_size = 10000;")  # Increase cache size (adjust as needed)

            # Begin the transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Prepare the SQL update statement
            update_query = f"""
            UPDATE {table_name}
            SET {target_column} = {source_column};
            """

            # Execute the update statement
            cursor.execute(update_query)

            # Commit the transaction
            conn.commit()

            print(f"Values from {source_column} successfully copied to {target_column}.")

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            # Ensure that the connection is closed
            if conn:
                conn.close()
    
    
    def add_image_num_index(self):

        """
        Adds ImageNumber column to SQLite table and updates its values based on column numbers.
        """
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            
            cursor.execute(f"PRAGMA table_info({self.table_name});")
            columns = [column[1] for column in cursor.fetchall()]
            if 'ImageNumber' not in columns: # Check if the 'ImageNumber' column exists
                cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN ImageNumber {self.column_data_type};")
            else:
                print("ImageNumber column exists")

            # Execute query to retrieve rows and columns
            cursor.execute(f"SELECT Row, Column, Field FROM {self.table_name};")
            # Fetch all rows (Row, Column, Field) from the result set
            rows = cursor.fetchall()

            # Create a dictionary to store unique combinations
            image_number_dict = {}
            img_num=1

            for row_number, column_number, field_number in rows:

                # Skip rows with any missing fields
                if row_number is None or column_number is None or field_number is None:
                    continue

                key = (row_number, column_number, field_number)
                # Assign a unique ImageNumber for each unique key
                if key not in image_number_dict:
                    image_number_dict[key] = img_num
                    img_num+=1

            # Now update the ImageNumber based on the stored mapping
            for (row_number, column_number, field_number), image_number in image_number_dict.items():
                cursor.execute(f"UPDATE {self.table_name} SET ImageNumber = ? WHERE Row = ? AND Column = ? AND Field = ?;",
                    (image_number, row_number, column_number, field_number))
                
                '''print("\nimage number is: ", image_number,
                      "\nrow number is: ", row_number, 
                      "\ncol number is: ", column_number, 
                      "\nfield number is: ", field_number)'''
            
            # Commit changes to the database
            connection.commit()
            print("Image Numbers updated successfully.")

        except sqlite3.Error as error:
            print(f"Error accessing SQLite database: {error}")

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()


    def drop_table(self, table_name):
        """
        Drops the table specified.
        """
        try:
            # Open a connection to the database
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()

                # Drop the table if it exists
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                print(f"Table {table_name} has been dropped successfully.")

                # Commit the changes (although this is not necessary for DROP TABLE)
                connection.commit()

        except sqlite3.Error as error:
            print(f"Error occurred while dropping the table {table_name}: {error}")

    #--------------------Helper Functions----------------------
    # Helper function for getting reference data
    
    def populate_image_number_dict(self, reference):
        # TODO factor this into all the functions that end up using this
        # TODO see if this aught to be initialized? --> to speed up process
        """Populates a dictionary with unique combinations from the reference data."""
        image_number_dict = {}
        for row, column, field, channel, value in reference:
            if row is None or column is None or field is None or channel is None or value is None:
                continue
            key = (row, column, field, channel)
            if key not in image_number_dict:
                image_number_dict[key] = value
        return image_number_dict
    
    def check_folders(self):
        # TODO initialize a plate counter so I know how many plates there are
        self.plate_count = 0
        # Create a dictionary to store lists of images by folder
        folder_dict = {}
        
        for image in self.image_files:
            folder = os.path.dirname(image)  # Get the folder path
            if folder not in folder_dict:
                folder_dict[folder] = []
            folder_dict[folder].append(image)

        # Pass each list of images to image_regex_extractor with a label
        for index, (folder, images) in enumerate(folder_dict.items(), start=1):
            plate_label = f"Plate {index}"
            print(f"Processing {plate_label}: {folder} with {len(images)} images.")
            
            #TODO check if this works for multiple plates
            self.image_fodlers.append(folder)
            plate_label = index

            self.plate_count += 1
            self.image_regex_extractor(images, plate_label, False)

    def image_regex_extractor(self, image_files, plate_label, test:bool):

        #row, col, field, position, channel, cycle = ""

        #pattern = r"^r(?P<myRow>\d+)c(?P<myCol>\d+)f(?P<myField>\d+)p(?P<myPosition>\d+)-ch(?P<myChannel>\d+)sk(?P<myCycle>\d+).*\."
        pattern = r".*\\r(?P<myRow>\d+)c(?P<myCol>\d+)f(?P<myField>\d+)p(?P<myPosition>\d+)-ch(?P<myChannel>\d+)sk(?P<myCycle>\d+).*\.tiff$"

        # TODO what if there are multiple plates?
        #image_info = {}

        # Dictionary to hold image info by plate
        image_info = {plate_label: {}}

        for image in image_files:
            result = re.fullmatch(pattern, image)
            if result:
                # Extract values from the match
                '''
                row = result.group('myRow')
                col = result.group('myCol')
                field = result.group('myField')
                position = result.group('myPosition')
                channel = result.group('myChannel')
                cycle = result.group('myCycle')
                '''
                row = int(result.group('myRow'))
                col = int(result.group('myCol'))
                field = int(result.group('myField'))
                position = int(result.group('myPosition'))
                channel = int(result.group('myChannel'))
                cycle = int(result.group('myCycle'))

                key = (row, col, field, position, channel, cycle)
                
                #image_info[image] = key
                image_info[plate_label][image] = key
                
                if test == True:
                    print(f"Row: {row}, Col: {col}, Field: {field}, Position: {position}, Channel: {channel}, Cycle: {cycle}")
                #else:
                    #print(f"No match for image: {image}")

        print(f"Plate {plate_label} has been processed succsesfully")
        self.image_info = image_info

    def image_size_finder(self, table):
        '''
        Finds the size of each channels image
        '''
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [column[1] for column in cursor.fetchall()]

            if 'ImageSizeX' not in columns or 'ImageSizeY' not in columns:
                print("No size column exists")
            else:
                print("ImageSize columns exist")

                # Execute query to retrieve rows and columns
                cursor.execute(f"SELECT DISTINCT ImageSizeX, ImageSizeY, ChannelName FROM {table};")
                results = cursor.fetchall()
                print("Retrieved sizes and channels:", results)
                self.image_size_list = results

        except sqlite3.Error as e:
            print(f"Database error occured when finding Image sizes: {e}")
        finally:
            # Ensure the connection is closed
            if connection:
                connection.close()

    def filter_column_names(self, column_names, keyword):
        """
        Filter the column names to only include those containing the specified keyword.
        Args:
            column_names (list): List of column names.
            keyword (str): Keyword to filter the column names.

        Returns:
            list: Filtered list of column names containing the keyword.
        """
        return [name for name in column_names if keyword in name]
    
    def get_column_names(self, table_name, keyword=None):
        """
        Retrieve column names from a specified SQLite table.

        Args:
            db_path (str): Path to the SQLite database file.
            table_name (str): Name of the table to get column names from.

        Returns:
            list: A list of column names from the specified table.
        """
        try:
            # Connect to the SQLite database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Execute a query to retrieve the column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()

            # Extract column names from the results
            column_names = [column[1] for column in columns_info]

            # If a keyword is provided, filter the column names
            if keyword:
                column_names = self.filter_column_names(column_names, keyword)

            return column_names

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return []
        
        finally:
            # Close the database connection
            if conn:
                conn.close()

    def update_nulls_in_col(self, table_name, value_to_insert, column):
        try:
            # Using 'with' statement to manage connection automatically
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prepare the SQL update statement for batch processing
                update_query = f"""
                UPDATE {table_name}
                SET {column} = ?
                WHERE {column} IS NULL;
                """

                # Execute the update statement with parameters
                cursor.execute(update_query, (value_to_insert,))

                # Commit the changes
                conn.commit()
                print(f"Nulls in column '{column}' of table '{table_name}' updated successfully.")

        except sqlite3.Error as e:
            print(f"SQLite error when trying to fix nulls in column '{column}': {e}")

    def update_nulls_in_cols_batch(self, table_name, value_to_insert, columns):
        try:
            # Construct the SET clause dynamically for multiple columns
            set_clause = ", ".join([f"{column} = ?" for column in columns])

            # Using 'with' statement to manage the connection automatically
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Prepare the SQL update statement to set multiple columns to NULL
                update_query = f"""
                UPDATE {table_name}
                SET {set_clause}
                WHERE {', '.join([f'{column} IS NULL' for column in columns])};
                """

                # Execute the update statement with parameters for all columns
                cursor.execute(update_query, [value_to_insert] * len(columns))

                # Commit the changes
                conn.commit()

                print(f"Nulls in columns {', '.join(columns)} of table '{table_name}' updated successfully.")

        except sqlite3.Error as e:
            print(f"SQLite error when trying to fix nulls in columns '{', '.join(columns)}': {e}")
    
    #--------------------Getters----------------------------
    def get_db_path(self):
        return self.db_path

    # Getter for table_name
    def get_table_name(self):
        return self.table_name

    # Getter for table_names
    def get_table_names(self):
        return self.table_names

    # Getter for channels
    def get_channels(self):
        return self.channels

    # Getter for channel_link_to_table
    def get_channel_link_to_table(self):
        return self.channel_link_to_table

    def get_image_size_list(self):
        return self.image_size_list

    def get_plate_count(self):
        return self.plate_count
    
    def get_object_tables(self):
        return self.object_tables
    