import random
import os
import sys
import easygui as g

class testgenerator():

    def __init__(self, number_of_files) -> None:
        self.output_folder = None
        self.number_of_files = number_of_files

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

    def generate_random_data(self, num_files: int, number_of_objects: int):
        # Ensure the output directory exists
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Template for data file
        header1 = [
            "Database Name\tOpera",
            "Database Link\thttp://",
            "Evaluation Signature\t" + str("c23e0046-16p3-asdd-b6f1-fbaba1d2bda6"),
            "Plate Name\tOPtoxicityIF_OPC",
            "Measurement\tMeasurement 1",
            "Evaluation\tEvaluation6",
            "Population\tPopulation - O4 Final",
            "",
            "[Data]"
        ]

        # Function to generate random row data for a well in the plate
        def generate_random_row(row, col, field, object_no):
            row = [
                str(row),  # Row
                str(col),  # Column
                str(random.randint(1, 1)),  # Plane
                str(random.randint(1, 1)),  # Timepoint
                str(field),  # Field
                str(object_no),  # Object No
                str(random.randint(10, 800)),  # X
                str(random.randint(11, 800)),  # Y
                f"[{random.randint(1, 800)},{random.randint(1, 800)},{random.randint(1, 800)},{random.randint(100, 800)}]",  # Bounding Box
                str(round(random.uniform(-500, 500), 2)),  # Position X [µm]
                str(round(random.uniform(-500, 500), 2)),  # Position Y [µm]
                "", "", "",  # Blank columns
                str(round(random.uniform(50, 200), 3)),  # O4 Final - O4 Area [µm²]
                str(round(random.uniform(1000, 5000), 2)),  # O4 Final - Intensity O4 Alexa 647 Mean
                str(random.randint(100000, 1000000)),  # O4 Final - Intensity O4 Alexa 647 Sum
                str(object_no)  # O4 Final - Object No in O4
            ]
            return "\t".join(row)

        # Create specified number of files
        for file_num in range(1, num_files + 1):
            obj_name = f'object_{file_num}'
            filename = os.path.join(self.output_folder, f"{obj_name}.txt")
            with open(filename, 'w') as file:
                # Define the header with the column names
                header = [
                    "Row", "Column", "Plane", "Timepoint", "Field", "Object No", "X", "Y",
                    "Bounding Box", "Position X [µm]", "Position Y [µm]", "", "", "",
                    f"{obj_name} - Area [µm²]", f"{obj_name} - Intensity Alexa 647 Mean",
                    f"{obj_name} - Intensity Alexa 647 Sum", f"{obj_name} - Object No in Ch"
                ]
                # Write header
                file.write("\t".join(header) + "\n")
                # Keep track of the object number and field number across the entire 96-well plate
                object_no = 1  # Start object number from 1
                field_no = 1  # Start field number from 1
                
                # Write random data rows for a 96-well plate (8 rows * 12 columns = 96 wells)
                for row in range(1, 9):  # 8 rows
                    for col in range(1, 13):  # 12 columns
                        # Write row with the current field and object number
                        
                        for i in range(1, number_of_objects):
                                file.write(generate_random_row(row, col, field_no, object_no) + "\n")
                                object_no = i  # Increment object number for each new object
                        
                        # Increment field number after each row of 12 columns (or after each well's data)
                        if col == 12:  # After the last column, increment field number
                            field_no += 1

            print(f"Generated file: {filename}")

# Set the number of generated files you want
number_of_files = 3

# This is the object count per field. Higher object counts => larger files
# 100 is not alot, 1000 is alot.
number_of_objects = 800

testgenerator_inst = testgenerator(number_of_files)

# specify your output folder
testgenerator_inst.set_output_folder()

# Generate 3 files for demonstration
testgenerator_inst.generate_random_data(testgenerator_inst.number_of_files, number_of_objects)

    
