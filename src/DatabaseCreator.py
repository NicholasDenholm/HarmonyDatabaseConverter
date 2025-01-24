import sqlite3
import pandas as pd
import re

class DatabaseCreator:

    def __init__(self, excel_path, db_path, table_name, input_folder):
        self.excel_path = excel_path
        self.db_path = db_path
        self.table_name = table_name
        self.input_folder = input_folder
        self.data_frame = None
        self.trimmed_data_frame = None
        self.column_names = None
        self.column_data_type = 'NUMERIC'

    def run(self):
        print("\n----Starting Database creation methods----\n")
        self.excel_to_dataframe()
        self.results_or_index() 
        self.create_sqlite_table()
        self.insert_data_into_table()

        # Find out why plate results table cant be passed through this correctly?
        #self.add_plate_map_column_slow()
        #self.add_well_row_and_col_slow("WellRow")
        #self.add_well_row_and_col_slow("WellColumn")
        
        print(f"Updating Plate map values for {self.table_name}")
        #TODO this vvv is slow
        self.add_plate_map_column()
        
        self.add_well_row_and_col("WellRow")
        self.add_well_row_and_col("WellColumn")
        print(f"{self.table_name} Well values updated successfully.\n")
        
    def run2(self):
        print(f"Updating Plate map values for {self.table_name}")
        self.add_plate_map_column()
        self.add_well_row_and_col("WellRow")
        self.add_well_row_and_col("WellColumn")
        print(f"{self.table_name} Well values updated successfully.\n")


    #--------------------Methods----------------------
    
    #TODO change back to normal encoding
    def excel_to_dataframe(self):
        '''
        Read the csv file into a pandas dataframe
        '''
        try:
            self.data_frame = pd.read_csv(self.excel_path, encoding= 'unicode_escape', engine = 'python')
            #self.data_frame = pd.read_csv(self.excel_path, encoding='ISO-8859-1', on_bad_lines='warn')
        
        except Exception as e:
            print(f"Error reading cvs file {str(e)}")
            self.dataframe = None
        
    def results_or_index(self):
        '''
        Chooses the proper rename column function
        '''
        print("\nColumns found: \n", self.data_frame.columns[0:])
        if self.data_frame.columns[1] == 'Opera':
            #self.rename_columns_results()
            self.rename_columns_regex()
        else: 
            #self.rename_columns_Index()
            self.rename_columns_regex()


    def rename_columns_regex(self):
        """
        Renames DataFrame columns to adhere to database naming rules.
        """
        try:
            correct_col_names = []

            for col_name in self.data_frame.columns:
                # Apply the regex to retain only alphanumeric characters and underscores
                correct_name = re.sub(r'[^a-zA-Z0-9_]', '', col_name)

                # Append to the list of corrected names
                correct_col_names.append(correct_name)

            # TODO: Check that column names are not longer than 64 characters!
            self.column_names = correct_col_names
            self.data_frame.columns = self.column_names
            print("\nColumns after: \n", self.data_frame.columns[0:])

            self.trimmed_data_frame = self.data_frame

        except Exception as e:
            print(f"Error renaming columns: {str(e)}")
            self.trimmed_data_frame = None
            self.column_names = None
    
    #--------------------Table Modifing----------------------#
    def create_sqlite_table(self):

        try:
            # Establish a connection to the SQLite database
            print("db_path: ", self.db_path)
            connection = sqlite3.connect(self.db_path)
            # Create a cursor object using the connection
            cursor = connection.cursor()

            # Default data type if none is provided (e.g., NUMERIC)
            #default_type = "NUMERIC"

            # Quote the table name to handle reserved keywords and special characters
            quoted_table_name = f'"{self.table_name}"'
            if quoted_table_name.startswith('"Objects_Population'):
                #quoted_table_name = f'"{quoted_table_name[19:]}'  # Keep the quote before the remaining part
                quoted_table_name = quoted_table_name.removeprefix("Objects_Population")
                print(f"{quoted_table_name}")
                
           # Construct the SQL query to create the table
            columns_with_types = []
            for column in self.column_names:
                # Quote column names to handle reserved keywords and special characters
                quoted_column = f'"{column}"'  # Use double quotes to handle reserved keywords
                columns_with_types.append(f"{quoted_column} {self.column_data_type}")

            # SQL query to create table in SQLite database
            create_table_query = f"CREATE TABLE {quoted_table_name} ({', '.join(columns_with_types)});"

            #print("\nSQL Query: \n", create_table_query) # for debugging
            # Execute SQL query to create table
            cursor.execute(create_table_query)

            connection.commit()
            connection.close()
            print(f"SQLite table '{self.table_name}' created successfully.")

        except sqlite3.Error as error:
            print(f"Error occurred creating table: {error}")

    def insert_data_into_table(self):
        """
        Inserts data from Pandas DataFrame into SQLite table.
        """
        print("\nInputing data now ...\n")

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            #for index, row in self.trimmed_data_frame.iterrows(): does index matter?
            for index, row in self.trimmed_data_frame.iterrows():
                row_values = row.tolist()

                # Check if lengths match
                if len(row_values) != len(self.column_names):
                    print(f"Row values length {len(row_values)} does not match column names length {len(self.column_names)}")
                    continue

                #insert_query = f"INSERT INTO `{self.table_name}` (`{', '.join(self.column_names)}`) VALUES ({', '.join(['?'] * len(row_values))});"
                insert_query = f"INSERT INTO `{self.table_name}` ({', '.join([f'`{col}`' for col in self.column_names])}) VALUES ({', '.join(['?'] * len(self.column_names))});"

    
                try:
                    cursor.execute(insert_query, row_values)
                except sqlite3.Error as e:
                    print(f"An error occurred while inserting row {index}: {e}")

                #cursor.execute(insert_query, row_values)

            connection.commit()
            connection.close()

            print(f"Data inserted into SQLite table '{self.table_name}' successfully.")

        except sqlite3.Error as error:
            print(f"Error inserting data into SQLite table: {error}")

    def reset_data_and_insert_data_into_table(self):
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            delete_query = f"DELETE FROM `{self.table_name}`;"

            try:
                cursor.execute(delete_query)
            except sqlite3.Error as e:
                print(f"An error occurred while deleting")

            connection.commit()
            connection.close()
            print(f"Old table deleted successfully.")
            
            #self.insert_data_into_table()
            self.insert_data_into_table_fast()

        except sqlite3.Error as error:
            print(f"SQlite error deleteing old table {self.table_name}: {error}")

    #TODO Is this faster?
    def insert_data_into_table_fast(self):
        """
        Inserts data from Pandas DataFrame into SQLite table.
        """
        print("\nInserting data now ...\n")

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            # SQLite optimizations for better insert performance
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Prepare insert query (only once, outside of loop)
            insert_query = f"""
                INSERT INTO `{self.table_name}` ({', '.join([f'`{col}`' for col in self.column_names])})
                VALUES ({', '.join(['?'] * len(self.column_names))});
            """

            # Convert the DataFrame to a list of tuples (this step is faster than row by row)
            rows_to_insert = self.trimmed_data_frame[self.column_names].values.tolist()

            # Insert the data in batches
            batch_size = 20000  # You can adjust the batch size based on your environment
            for i in range(0, len(rows_to_insert), batch_size):
                cursor.executemany(insert_query, rows_to_insert[i:i+batch_size])
                print(f"batch size of {batch_size} inserted into table: {self.table_name}")

            # Commit the transaction after all inserts
            connection.commit()

            print(f"Data inserted into SQLite table '{self.table_name}' successfully.")

        except sqlite3.Error as error:
            print(f"Error inserting data into SQLite table: {error}")

        finally:
            # Ensure the connection is closed
            if connection:
                connection.close()
    
    #--------------------Plate Maps----------------------#
    
    def add_plate_map_column(self):
        """
        Adds Well_Number column to SQLite table and updates its values based on row and column numbers.
        Optimized for performance by reducing number of queries and minimizing memory usage.
        """
        print(f"\nUpdating Well coordinates for {self.table_name}.")

        def convert_to_plate_map(row: int, col: int):
            Row_to_letter = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L'}
            
            # Convert row and column to plate map string format (e.g., 'A01', 'B12')
            plate_row = Row_to_letter[row]  # Row is already an integer
            plate_col = f"{col:02}"  # Ensures two-digit column format (01, 02, ...)
            return plate_row + plate_col

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Add the 'Well' column if it doesn't exist
            cursor.execute(f"PRAGMA foreign_keys=off;")
            cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN Well {self.column_data_type};")
            cursor.execute(f"PRAGMA foreign_keys=on;")

            # Set PRAGMA to improve performance during bulk insert
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Iterate over rows in the table and update in bulk
            cursor.execute(f"SELECT Row, Column FROM {self.table_name};")
            rows = cursor.fetchall()

            # Initialize a set to track unique (row_number, column_number) pairs
            seen = set()
            updates = []

            # Build updates list with unique values
            for row in rows:
                row_number = int(row[0])  # Ensure integer row
                column_number = int(row[1])  # Ensure integer column

                # Use a tuple (row_number, column_number) to check if this combination has already been processed
                if (row_number, column_number) not in seen:
                    # If unique, convert to plate map and add to updates
                    plate_map_number = convert_to_plate_map(row_number, column_number)
                    updates.append((plate_map_number, row_number, column_number))
                    seen.add((row_number, column_number))  # Add the pair to the set to track

            # Efficient batch update using executemany
            update_query = f"""
            UPDATE {self.table_name}
            SET Well = ?
            WHERE Row = ? AND Column = ?
            """
            cursor.executemany(update_query, updates)

            # Commit the transaction
            connection.commit()

            print("Plate map numbers updated successfully.")

        except sqlite3.Error as error:
            print(f"Error accessing SQLite database: {error}")

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_well_row_and_col(self, value: str):
        """
        Adds Well_Number column to SQLite table and updates its values based on row and column numbers.
        Optimized using SQL CASE expression for updating values.
        """
        print(f"Updating Well {value} for {self.table_name}.")

        if value not in ('WellRow', 'WellColumn'):
            print("Error: add_well_row_and_col must take either 'WellRow' or 'WellColumn' as an argument.")
            return

        # Select the correct coordinate based on input
        coord = "Row" if value == 'WellRow' else "Column"

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            # Set PRAGMA to improve performance during bulk insert
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Check if the column already exists in the table
            cursor.execute(f"PRAGMA table_info({self.table_name});")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            # Add the new column if it doesn't exist
            if value not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN {value} {self.column_data_type};")
            
            # Build the SQL query with a CASE expression
            update_query = f"""
            UPDATE {self.table_name}
            SET {value} = CASE
                WHEN {coord} < 10 THEN '0' || {coord}  -- For values between 0-9, prepend a '0'
                WHEN {coord} >= 10 THEN {coord}      -- For values 10 or greater, leave as is
                ELSE NULL  -- If invalid value (negative or NULL), set as NULL (can also use 'nan')
            END;
            """

            # Execute the update query
            cursor.execute(update_query)

            # Commit the changes
            connection.commit()

            print(f"{value} values updated successfully.")

        except sqlite3.Error as e:
            print(f"SQLite error in add_well_row_and_col(): {e}")
        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()


    # --------------------- Old Attempts -----------------------------

    def add_well_row_and_col_slow(self, value:str):

        """
        Adds Well_Number column to SQLite table and updates its values based on row and column numbers.
        """
        print(f"Updating Well {value} for {self.table_name}.")
        if value not in ('WellRow', 'WellColumn'):
            print(f"error add_well_row_and_col has to take either WellRow or WellColumn as a argument")
            return

        if value in ('WellRow'):
            coord = "Row"
        else:
            coord = "Column"

        def convert_to_Well_Value(num):
            """
            Either for WellRow or WellColumn
            """
            if 0 < num < 10:
                WellRow = f"0{num}"
                return WellRow
            if num >= 10:
                return num
            if num < 0:
                print(f"There cannot be negitive rows or columns, value in question {num}")
                return error
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Add new column 'Well' if it doesn't exist
            cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN {value} {self.column_data_type};")

            # Execute query to retrieve rows and columns
            cursor.execute(f"SELECT {coord} FROM {self.table_name};")

            # Fetch all rows from the result set
            rows = cursor.fetchall()

            # Iterate over rows, calculate plate map numbers, and update the table
            for row in rows:

                # Convert to int to handle both floats and integers
                number = int(float(row[0]))

                Well_number = convert_to_Well_Value(number)

                # Update each row with the calculated plate map number
                cursor.execute(f"UPDATE {self.table_name} SET {value} = ? WHERE {coord} = ?;", (Well_number, number))

            # Commit changes to the database
            connection.commit()
            print(f"{value} values updated successfully.")

        except sqlite3.Error as error:
            print(f"Error accessing SQLite database: {error}")

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_plate_map_column_slow(self):

        """
        Adds Well_Number column to SQLite table and updates its values based on row and column numbers.
        """
        # TODO takes very long for Hoescht Why?
        # TODO for some reason plateresults has row and column values saved a floats not ints why?
        print(f"\nUpdating Well coordinates for {self.table_name}.")

        def convert_to_plate_map(row, col):
            Row_to_letter = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L'}

            row_int = int(row)
            plate_row = Row_to_letter[row_int]

            # Convert column index to plate map column (01, 02, ...)
            plate_col = f"{int(col):02}"  # Assuming columns are 1-based index

            # Combine row and column into plate map number
            plate_map_number = plate_row + plate_col

            return plate_map_number

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Add new column 'Well' if it doesn't exist
            cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN Well {self.column_data_type};")

            # Execute query to retrieve rows and columns
            cursor.execute(f"SELECT Row, Column FROM {self.table_name};")

            # Fetch all rows from the result set
            rows = cursor.fetchall()

            # Iterate over rows, calculate plate map numbers, and update the table
            for row in rows:
                #row_number, column_number = row

                # Convert to int to handle both floats and integers
                row_number = int(float(row[0]))
                column_number = int(float(row[1]))

                #print("Row is: ", row_number)
                plate_map_number = convert_to_plate_map(row_number, column_number)

                # Update each row with the calculated plate map number
                cursor.execute(f"UPDATE {self.table_name} SET Well = ? WHERE Row = ? AND Column = ?;", (plate_map_number, row_number, column_number))

            # Commit changes to the database
            connection.commit()
            print("Plate map numbers updated successfully.")

        except sqlite3.Error as error:
            print(f"Error accessing SQLite database: {error}")

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def add_plate_map_column_slow(self):
        """
        Adds Well_Number column to SQLite table and updates its values based on row and column numbers.
        Optimized for performance by reducing number of queries and minimizing memory usage.
        """
        print(f"\nUpdating Well coordinates for {self.table_name}.")

        def convert_to_plate_map(row, col):
            Row_to_letter = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L'}

            row_int = int(row)
            plate_row = Row_to_letter[row_int]
            plate_col = f"{int(col):02}"  # Ensure two-digit column format (01, 02, ...)
            
            return plate_row + plate_col

        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Add the 'Well' column if it doesn't exist
            cursor.execute(f"PRAGMA foreign_keys=off;")
            cursor.execute(f"ALTER TABLE {self.table_name} ADD COLUMN Well {self.column_data_type};")
            cursor.execute(f"PRAGMA foreign_keys=on;")
            
            cursor.execute("PRAGMA synchronous = OFF;")
            cursor.execute("PRAGMA journal_mode = MEMORY;")
            
            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Fetch rows and columns in a more memory-efficient manner
            cursor.execute(f"SELECT Row, Column FROM {self.table_name};")
            rows = cursor.fetchall()

            # Prepare an update query that will update multiple rows in one go
            update_query = f"UPDATE {self.table_name} SET Well = CASE "

            # Build the CASE WHEN clause for batch update
            for row in rows:
                row_number = int(float(row[0]))  # Ensure integer row
                column_number = int(float(row[1]))  # Ensure integer column
                plate_map_number = convert_to_plate_map(row_number, column_number)
                update_query += f"WHEN Row = {row_number} AND Column = {column_number} THEN '{plate_map_number}' "

            # Close the CASE WHEN clause
            update_query += "END WHERE Row IN (" + ",".join(str(int(float(row[0]))) for row in rows) + ")"

            # Execute the batch update in a single query
            cursor.execute(update_query)

            # Commit the transaction
            connection.commit()

            print("Plate map numbers updated successfully.")

        except sqlite3.Error as error:
            print(f"Error accessing SQLite database: {error}")

        finally:
            # Close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Rename functions
    def rename_columns_results(self):
        """
        Renames DataFrame columns to adhere to database naming rules.
        """

        try:
            new_columns = self.data_frame.iloc[7].tolist()
            #print("New Columns: ", new_columns[:])
            self.data_frame.columns = new_columns

            # Ignores the header that Harmony csv files have
            self.trimmed_data_frame = self.data_frame.iloc[8:, :]

            # Rename columns to remove spaces and special characters
            self.column_names = []
            for name in self.trimmed_data_frame.columns:
                #new_name = name.replace(" - ", "_").replace(" ", "_").replace("%", "percent").replace("/", "slash").replace("[µm²]", "um").replace("[µm]", "um").replace("[s]", "_s").replace("[s]", "_s").replace("[m]", "m").replace("ï»¿", "")
                
                # TODO refactor into regex.sub(any non word, no sqlite commands like group ext.)
                new_name = name.replace("-", "_").replace("Group", "Group_id").replace(" ", "").replace("%", "percent").replace("/", "_").replace("[", "").replace("]", "").replace("[µm²]", "um").replace("[µm]", "um").replace("[s]", "_s").replace("[m]", "m").replace("ï»¿", "").replace("Â", "")
                self.column_names.append(new_name)
                
            self.data_frame.columns = self.column_names
            print("\nColumns after: \n", self.data_frame.columns[0:])

            self.trimmed_data_frame = self.data_frame

        except Exception as e:
            print(f"Error renaming columns: {str(e)}")
            self.trimmed_data_frame = None
            self.column_names = None

    def rename_columns_Index(self):
        """
        Renames DataFrame columns to adhere to database naming rules.
        """
        try:
            
            correct_col_names = []

            for col_name in self.data_frame.columns:
                correct_name = col_name.replace("-", "_").replace("Group", "Group_id").replace(" ", "").replace("%", "percent").replace("/", "_").replace("[", "").replace("]", "").replace("²", "").replace("µ", "u").replace("[µm²]", "um").replace("[µm]", "um").replace("[s]", "_s").replace("[m]", "m").replace("ï»¿", "").replace("Â", "")
                correct_col_names.append(correct_name)

            #TODO Check that column names are not longer than 64 characters!
            self.column_names = correct_col_names
            self.data_frame.columns = self.column_names
            print("\nColumns after: \n", self.data_frame.columns[0:])

            self.trimmed_data_frame = self.data_frame
            

        except Exception as e:
            print(f"Error renaming columns: {str(e)}")
            self.trimmed_data_frame = None
            self.column_names = None

    # TODO make this a general catchall with regex to rename columns
    # TODO use regex to find the start of the data, ie: first csv index that has 'Row'
    def rename_columns_results_2(self):
        """
        Renames DataFrame columns to adhere to database naming rules.
        
        The new column names are derived from the 8th row of the DataFrame.
        Spaces and special characters are replaced to create valid identifiers
        for a database schema.
        """

        try:
            new_columns = self.data_frame.iloc[7].tolist()
            self.data_frame.columns = new_columns

            # Ignores the header that Harmony CSV files have
            self.trimmed_data_frame = self.data_frame.iloc[8:, :]

            # Function to clean and format column names
            def clean_column_name(name):
                
                if isinstance(name, bytes):
                    name = name.decode('utf-8')  # Convert bytes to string
                name = str(name)  # Ensure it's a string
                # Replace specific patterns using regex
                name = re.sub(r'[ -]', '_', name)  # Replace spaces and hyphens with underscores
                name = re.sub(r'[%\[\]]', '', name)   # Remove %, [, and ]
                name = re.sub(r'Group', 'Group_id', name)  # Specific replacement for 'Group'
                name = name.replace('µm²', 'um').replace('µm', 'um').replace('s', '_s').replace('m', 'm')
                return name.strip()  # Remove any leading/trailing whitespace

            # Rename columns using the cleaning function
            self.column_names = [clean_column_name(name) for name in self.trimmed_data_frame.columns]

        except Exception as e:
            print(f"Error renaming columns: {str(e)}")
            self.trimmed_data_frame = None
            self.column_names = None


    
        
