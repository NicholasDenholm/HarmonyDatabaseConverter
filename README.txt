Backround
- This is a guide for running the Harmony to Cellprofilier Analyst (CPA) database converter application
- It can take outputted Harmony data and convert it into a database that can be read by CPA. 
- It works for single plates, and can be run multiple times to convert multiple plates.
- As of now it doesnt work for 3d images.

Instructions

__________________________
Step 1

- First export your Harmony data (plate results, object results, and images) 
- Place these into an new experiment folder in the input directory where you found this app. 
**Make sure that there are no other overlapping experiment data in the same folder.**

It should look like this:

|DatabaseConverter.exe
|output
|input
     |--Experiment1
         |--OPtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 1
	    |Index.txt                                           <-- Index_file is important! 
            |--Evaluation 6
               |Objects_Population - 1
               |Objects_Population - 2
               |PlateResults
     |--Experiment2
     |--Experiment3
     ....

__________________________
Step 2

- Create a unique folder for your experiment in the output folder as well
- It should look something like this:

|DatabaseConverter.exe
|output
     |--Experiment1
     |--Experiment2
     ....


If you are running this converter multiple times for multiple plates and output
to the same experiment output folder it will overwrite existing properties files. 
So make seperate folders according to plate 
ex: Experiment1, Experiment2, ...

__________________________
Step 3

Place your Image folders from each plate into their own folder as well.
it'll look like this when you are done.

|DatabaseConverter.exe
|Images
    |--OPtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 1
    |--OPtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 2
    | ....

|input
     |--Experiment1
         |--OPtoxicityIF_OPC__2024-07-31T14_12_17-Measurement 1
	    |Index.txt
            |--Evaluation 6
               |Objects_Population - 1
               |Objects_Population - 2
               |PlateResults
     |--Experiment2
     |--Experiment3
     ....

|output
     |--Experiment1
     |--Experiment2
     ....


Now you are all set up to run the program.

__________________________
Step 4

Locate the DatabaseConverter application, and click on it.

It will bring up a terminal window, and eventually a prompt window will be displayed.
Follow the instructions, each window displays on the top left corner what it needs...
 
-Select yes 
-locate your plates input folder
-locate the plates image folder
-locate the plates output folder

Wait for the database to be created...

There will be another window that pops up and link the corresponding channels to their object tables. 

For example:
Hoechst --> Hoescht 33342
O4 Final --> Alexa 647 
...

Link each of the tables, then when you are sure they are correct, click done.

Wait for the program to display ALL DONE and create the properties files.

__________________________

At this point the window will close and you can now open your properties file in CPA!

Good luck!

__________________________
Notes

Sometimes CPA needs some tables to be linked for some features to work, so the most straight forward way for this to happen is open each properties file in CPA.
--> This will change the database so that it will have a couple more tables with link info

-The filter method in CPA, doesn't like Null values in the table, I tried to run some tests
But it seems that it breaks the filter method..
I think it doesn't like non numerical columns in the object tables


__________________

Features to add

- Convert the BoundingBox to a useable measurement 
(could be source of error for filter in CPA)

-Being able to read multiple plates at once and add them all to the same database, 
instead of converting each plate individually.

-Support for different plate types then 96 well, ie: 384 ...

-Support for 3D, ie: cell_z_loction

-support for Mac, Linux

-MySLQ implementation of db creation

-Calculation of median per_well, std_per_well

_________________

Notes

If you edit the source code and need to remake the application run this command whilst in
the project folder

pyinstaller --onefile --add-data "PropertiesFileTemplate.ini;." main.py