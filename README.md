# Harmony to CellProfiler Analyst (CPA) Database Converter

## Background

- This is a guide for running the Harmony to CellProfiler Analyst (CPA) database converter application.
- It can take outputted Harmony data and convert it into a database that can be read by CPA.
- It works for single plates and can be run multiple times to convert multiple plates.
- As of now, it doesn't work for 3D images.

## Instructions

The following instructions are the same if you choose to run the exe, or from the source files located in the src folder

### Step 1: Export Harmony Data

- First, export your Harmony data (plate results, object results, and images).
- Place these into a new experiment folder in the `input` directory where you found this app.  
  **Make sure that there are no other overlapping experiment data in the same folder.**


It should look like this:
DatabaseConverter.exe
```
├── output
├── input
│   ├── Experiment1
│   │   ├── OPOtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 1
│   │   │   ├── Index.txt  **<-- Index_file is important!**
│   │   │   └── Evaluation 6
│   │   │       ├── Objects_Population - 1
│   │   │       ├── Objects_Population - 2
│   │   │       └── PlateResults
│   ├── Experiment2
│   ├── Experiment3
│   └── ...
```
### Step 2: Create Output Folder

- Create a unique folder for each experiment in the `output` folder as well.
- If you are running this converter multiple times for multiple plates and output
- to the same experiment output folder it will overwrite existing properties files. 
- So make seperate folders according to plate 

- It should look something like this:
```
DatabaseConverter.exe
├── output
├── input
│   ├── Experiment1
|   ├── Experiment2
|   | .....
```

### Step 3: Place Image Folders

- Place your image folders from each plate into their own folder as well. 
- It should look like this when you're done:
```
DatabaseConverter.exe
├── Images
│   ├── OPOtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 1
│   ├── OPOtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 2
│   └── ...
├── input
│   ├── Experiment1
│   │   ├── OPOtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 1
│   │   │   ├── Index.txt
│   │   │   └── Evaluation 6
│   │   │       ├── Objects_Population - 1
│   │   │       ├── Objects_Population - 2
│   │   │       └── PlateResults
│   ├── Experiment2
│   ├── Experiment3
│   └── ...
├── output
│   ├── Experiment1
│   ├── Experiment2
│   └── ...
```

Now, you're all set up to run the program.


### Step 4: Run the Converter

1. Locate the `DatabaseConverter` application and click on it.
2. It will bring up a terminal window, and eventually, a prompt window will be displayed. Follow the instructions shown in the top left corner of the window.
3. You will be asked to:
   - Select **Yes**.
   - Locate your plate's **input** folder.
   - Locate the plate's **image** folder.
   - Locate the plate's **output** folder.

Wait for the database to be created...

4. Another window will pop up asking you to link the corresponding channels to their object tables.  
   For example:
   - Hoechst → Hoechst 33342
   - O4 Final → Alexa 647
   - ...

5. Link each of the tables, and when you are sure they are correct, click **Done**.
6. Wait for the program to display **ALL DONE** and create the properties files.

At this point, the window will close, and you can now open your properties file in CPA!

Good luck!

---

## Notes

- Sometimes, CPA needs some tables to be linked for certain features to work. The most straightforward way to accomplish this is to open each properties file in CPA.  
  This will modify the database and add a couple of tables with link information.
  
- The filter method in CPA doesn't like `NULL` values in the table. I tried running some tests, but it seems the filter breaks when non-numerical columns are present in the object tables.

---

## Features to Add

- Convert the **BoundingBox** to a usable measurement (could be a source of error for filtering in CPA).
- Enable the ability to read multiple plates at once and add them all to the same database, instead of converting each plate individually.
- Support for different plate types other than 96-well (e.g., 384-well).
- Support for 3D data (e.g., `cell_z_location`).
- Support for Mac and Linux.
- MySQL implementation of DB creation.
- Calculation of **median per well** and **std per well**.

---

## Notes for Developers

- If you edit the source code and need to remake the application/exe, run this command in the project folder:

```
pyinstaller --onefile --add-data "PropertiesFileTemplate.ini;." main.py
```
