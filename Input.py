import easygui as g
import os
import sys
import csv
import pandas as pd

class Input:

    def __init__(self) -> None:
        self.input_folder = None
        self.input_files = None
        self.image_folder = None
        self.image_files = None
        self.output_folder = None
        self.db_name = None
        self.db_type = None
        self.db_path = None
        self.table_name = None

        self.plate_data = {}

        cleanup_file_list = None

    def run(self):
        self.set_input_folder()
        self.set_input_files()

        #TODO test
        self.set_image_folder()
        self.set_image_files()

        self.set_output_folder()
        self.set_database_info()
        self.check_database()
        #self.set_table_name()
        print("\n----Input methods done----\n")

    #--------------------Setters----------------------------

    def set_input_folder(self):

        # Getting the Harmony file
        msg = "Do you want to convert a Harmony csv file to a database file?"
        title = "Please Confirm"
    
        if g.ynbox(msg, title):  # show a Continue/Cancel dialog
            input_folder = g.diropenbox(msg="Choose the Harmony output folder")

            if input_folder:
                print("Input folder Path:", input_folder)
                self.input_folder = input_folder
                return input_folder
            else:
                print("No folder selected. Exiting.")
                sys.exit(0)
        else:
            print("Conversion canceled. Exiting.")
            sys.exit(0)

    def set_input_files(self):

        text_files = []

        # Walk through the directory
        for root, dirs, files in os.walk(self.input_folder):
            # Filter text files
            for file in files:

                if file.endswith('.txt') and not (file.endswith('_trimmed.txt')):
                    # Get full path to the file
                    full_path = os.path.join(root, file)
                    text_files.append(full_path)
        
        self.convert_txt_to_csv(text_files)

    def set_image_folder(self):

         # Getting the image folder
        msg = "Choose the image folder"
        title = "Please Confirm"
        
        if g.ccbox(msg, title):  # show a Continue/Cancel dialog
            image_folder = g.diropenbox(msg="Choose the image folder")

            if image_folder:
                print("image folder Path:", image_folder)
                self.image_folder = image_folder
                return image_folder
            else:
                print("No folder selected. Exiting.")
                sys.exit(0)
        else:
            print("Conversion canceled. Exiting.")
            sys.exit(0)

    def set_image_files(self):

        image_files = []

        # Walk through the directory
        for root, dirs, files in os.walk(self.image_folder):
            # Filter text files
            for file in files:

                if file.endswith('.tiff'):
                    # Get full path to the file
                    full_path = os.path.join(root, file)
                    image_files.append(full_path)
        
        self.image_files = image_files

    def convert_txt_to_csv(self, input_files, delimiter='\t'):
        """
        Converts a list of text files to CSV files.

        Parameters:
        - input_files (list of str): List of paths to the .txt files to be converted.
        - delimiter (str): The delimiter used in the .txt files.

        Returns:
        - list of str: List of paths to the resulting .csv files.
        """
        csv_files = []

        # Ensure input_files is a list
        if not isinstance(input_files, list):
            raise TypeError("input_files must be a list of file paths.")


        for txt_file in input_files:
            print(f"Processing file: {txt_file}")  # Debugging line
            
            if not isinstance(txt_file, str):
                print(f"Skipping invalid file (not a string): {txt_file}")
                continue  # Skip if it's not a string
            if not txt_file.lower().endswith('.txt'):
                print(f"Skipping non-txt file: {txt_file}")
                continue

            try:
                # Open the file
                with open(txt_file, 'r') as file:
                    #print(file.read())
                    first_line = file.readline().strip()  # Read and strip whitespace
                    # Split the string into a list of words
                    words = first_line.split()
                    #print(words[0])

                    # Check the first line
                    if words[0] == "Row":
                        # Do something if the first line is "Row"
                        print("First line is 'Row'. Reading the dataframe as normal...")

                        # Read the text file into a DataFrame
                        #df = pd.read_csv(txt_file, delimiter=delimiter, engine='python')
                        df = pd.read_csv(f'{txt_file}', delimiter=delimiter, encoding='cp1252')
                        
                        # Define the path for the new CSV file
                        base_directory = os.path.dirname(txt_file)
                        csv_file_path = os.path.join(base_directory, os.path.basename(txt_file).replace('.txt', '.csv'))
                        
                        # Save the DataFrame to CSV
                        df.to_csv(csv_file_path, index=False)
                        
                        csv_files.append(csv_file_path)
                        print(f'File saved as CSV at: {csv_file_path}')

                        

                    else:
                        # Do something else if the first line is not "Row"
                        print("First line is not 'Row'. Cutting dataframe until row...")
                        
                        # Step 1: Extract metadata (including Plate Name) from the file
                        metadata = self.extract_metadata(txt_file)
                        # Step 2: Extract Plate Name from metadata
                        plate_name = metadata.get('Plate Name')
                        if not plate_name:
                            print(f"Plate Name not found in the metadata of {txt_file}")
                        # TODO init the plate_data field and associated matched plate_names 
                        # with coressponding object csv files
                        # in Main or here take these values and enum them and add a plate column 
                        # in each object table then merger/flatten the object tables 
                        print(f"Plate Name extracted: {plate_name}\n")


                        # Create a trimmed file with content starting from "Row"
                        trimmed_content = self.delete_until_row(file.read())
                        trimmed_file = txt_file.replace('.txt', '_trimmed.txt')
                        
                        with open(trimmed_file, 'w') as temp_file:
                            #print("\ncreating trimmed file: ")
                            temp_file.write(trimmed_content)
                            print("Saved trimmed file: \n")

                        # Read the trimmed text file into a DataFrame
                        df = pd.read_csv(trimmed_file, delimiter=delimiter, engine='python', encoding='ISO-8859-1') 
                        
                        # Remove unnamed columns
                        df = df.loc[:, ~df.columns.str.contains('^Unnamed')] #TODO fix this: sql command doesnt work, there seems to be all "?" as values

                        # Define the path for the new CSV file
                        base_directory = os.path.dirname(trimmed_file)
                        csv_file_path = os.path.join(base_directory, os.path.basename(trimmed_file).replace('.txt', '.csv'))
                        
                        # Save the DataFrame to CSV
                        df.to_csv(csv_file_path, index=False)
                        
                        csv_files.append(csv_file_path)
                        print(f'File saved as CSV at: {csv_file_path}')

                        # Step 5: Store the CSV file's path in the plate_data dictionary
                        if plate_name in self.plate_data:
                            # If the plate already exists in the dictionary, append the CSV filename
                            self.plate_data[plate_name].append(csv_file_path)
                        else:
                            # If the plate is not in the dictionary, initialize with the CSV filename in a list
                            self.plate_data[plate_name] = [csv_file_path]

                file.close()

            except Exception as e:
                print(f"An error occurred while processing {txt_file}: {e}")
        
        self.input_files = csv_files

        #TODO this ^^^ doesnt work, it only adds the index file why??

    def extract_metadata(self, txt_file):
        """
        Extracts metadata from the first 7 lines of the text file.

        Parameters:
        - txt_file (str): Path to the text file.

        Returns:
        - dict: Dictionary containing metadata keys and values.
        """
        metadata = {}
        try:
            with open(txt_file, 'r') as file:
                # Read the first few lines to inspect them
                raw_lines = [file.readline().strip() for _ in range(7)]
                #print(f"Raw lines from {txt_file}:\n{raw_lines}")  # Print raw lines for debugging
                
                for line in raw_lines:
                    if line:
                        key_value = line.split('\t') 
                        if len(key_value) == 2:  # Ensure there's a key-value pair
                            metadata[key_value[0].strip()] = key_value[1].strip()

        except Exception as e:
            print(f"Error reading metadata from {txt_file}: {e}")
        
        # Print the metadata for debugging
        #print(f"Metadata for file {txt_file}:\n{metadata}")
        return metadata
    
    def delete_until_row(self, input_str):
        # Find the index of "Row"
        row_index = input_str.find("Row")
        print("Row index is: ", row_index)
        
        # If "Row" is found, slice the string from that index
        if row_index != -1:
            return input_str[row_index:]
        else:
            return input_str  # Return the original string if "Row" is not found

    def convert_txt_to_csv_v1 (self, input_files:list, delimiter = '\t'):
        """
        Converts a list of text files to CSV files.

        Parameters:
        - input_files (list of str): List of paths to the .txt files to be converted.
        - delimiter (str): The delimiter used in the .txt files.

        Returns:
        - list of str: List of paths to the resulting .csv files.
        """
        csv_files = []

        for txt_file in input_files:
            # Ensure the file has a .txt extension
            if not txt_file.lower().endswith('.txt'):
                print(f"Skipping non-txt file: {txt_file}")
                continue
            
            # Read the contents of the original file
            with open(txt_file, 'r') as file:
                lines = file.readlines()
            
            # Define the path for the new CSV file
            base_directory = os.path.dirname(txt_file)
            csv_file_path = os.path.join(base_directory, os.path.basename(txt_file).replace('.txt', '.csv').replace(' - ', '').replace(' ', ''))
            
            # Write the processed data to the CSV file
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for line in lines:
                    # Split each line using the defined delimiter
                    row = line.strip().split(delimiter)
                    # Write the row to the CSV file
                    writer.writerow(row)
            
            csv_files.append(csv_file_path)
            print(f'File saved as CSV at: {csv_file_path}')
        
        self.input_files = csv_files

    def set_output_folder(self):

        # Getting the output folder
        msg = "Choose the output folder"
        title = "Please Confirm"
        
        if g.ccbox(msg, title):  # show a Continue/Cancel dialog
            output_folder = g.diropenbox(msg="Choose the output folder")

            if output_folder:
                #print("Output Folder:", output_folder)
                self.output_folder = output_folder
                #return output_folder
            
            else:
                print("No folder selected. Exiting.")
                sys.exit(0)
        else:
            print("Output folder selection canceled. Exiting.")
            sys.exit(0)

    def database_name(self):
        
        msg = "Enter in your Database info"
        title = "Database creator"
        fieldNames = ["New Database name"]
        
        while True:
            fieldValues = g.multenterbox(msg, title, fieldNames)

            if fieldValues is None:
                return None  # Exit if user cancels the input

            errmsg = ""
            if fieldValues[0].strip() == "":
                errmsg = f'"{fieldNames[0]}" is a required field.\n\n'
            
            if fieldValues[0][-3:] != '.db':
                #print("no .db at the end of the datbase name")
                # Concecates the end of the str with the database file type
                #fieldValues[0] = f"{fieldValues[0]}.db"
                fieldValues[0] = f"{fieldValues[0]}.db"
                print ("This should be the correct db name now: ",fieldValues[0])
                return fieldValues[0]

            if errmsg == "":
                #print("Reply was: ", fieldValues[0])
                return fieldValues[0]  # Return the database name if valid
            else:
                g.msgbox(errmsg, title="Input Error")
                

        #self.db_name = fieldValues1[0]
        #self.db_type = buttonvalues[0]

        #self.db_path = os.path.join(self.output_folder, self.db_name)

    def database_type(self):
        
        msg = "Choose your database type"
        title = "Database type"
        #buttonlist = ["sqlite", "MySQL"]
        buttonlist = ["sqlite"]
        
        while True:
            db_type = g.buttonbox(msg, title, choices=buttonlist)
            
            if db_type is None:
                return None  # Exit if user cancels the selection
            
            return db_type  # Return the selected database type

    def set_database_info(self):
        
        db_name = self.database_name()
        if db_name is None:
            print("Error with db name")
            return  # Exit if user cancels the input for database name

        db_type = self.database_type()
        if db_type is None:
            print("Error with db type")
            return  # Exit if user cancels the selection for database type


        # Set attributes
        self.db_name = db_name
        self.db_type = db_type
        self.db_path = os.path.join(self.output_folder, self.db_name)

    def check_database(self):

        if os.path.exists(self.db_path):
            msg = f"Database '{self.db_name}' already exists. Do you want to overwrite it?"
            title = "Database exists"
            print(f"'{self.db_type}' database '{self.db_name}' already exists at location '{self.db_path}'...")
            
            if g.ccbox(msg, title):  # User chose to overwrite
                print(f"Deleting the existing database at '{self.db_path}'...")
                os.remove(self.db_path)  # Remove the existing database file
                print(f"Existing database '{self.db_name}' removed.")

            if not g.ccbox(msg, title):
                print("Database creation cancled. Exiting now")
                sys.exit(0)

    def set_table_name(self):
        
        msg = "Enter your Table name"
        title = "Table creator"
        fieldNames = ["New Table name"]
        fieldValues = g.multenterbox(msg, title, fieldNames)

        while True:
            if fieldValues is None:
                return None  # User canceled

            errmsg = ""

            for i in range(len(fieldNames)):
                if fieldValues[i].strip() == "":
                    errmsg += f'"{fieldNames[i]}" is a required field.\n\n'
                # No Spaces allowed
                if fieldValues[i].isspace():
                    errmsg += f'"{fieldNames[i]}" No spaces allowed.\n\n'

            #fieldValues = g.multenterbox(errmsg, title, fieldNames, fieldValues)
            self.table_name = fieldValues[0]

            if errmsg == "":
                break  # No problems in input found

    def cleanup_files(self):
        
        print("\n")
        cleanup_file_list = []
        # Walk through the directory
        for root, dirs, files in os.walk(self.input_folder):
            # Filter text files
            for file in files:

                if file.endswith('_trimmed.txt'):
                    # Get full path to the file
                    full_path = os.path.join(root, file)
                    cleanup_file_list.append(full_path)
        
        for csv_file in self.input_files:
            cleanup_file_list.append(csv_file)

        for item in cleanup_file_list:
            
            try:
                os.remove(item)
                print(f"succsessfully cleaned up this: {item}")
            except OSError as error: 
                print(error) 
                print(f"{item} can not be removed") 

    #--------------------Getters----------------------------
    
    #def get_excel_path(self):
        #return self.excel_path
    
    def get_input_folder(self):
        return self.input_folder
    
    def get_input_files(self):
        return self.input_files
    
    def get_image_folder(self):
        return self.image_folder
    
    def get_image_files(self):
        return self.image_files
    
    def get_output_folder(self):
        return self.output_folder
    
    def get_database_info(self):
        db_info = [self.db_name, self.db_type, self.db_path]
        return db_info
    
    def get_table_name(self):
        return self.table_name

 