Distance Vector Routing

# 04/23/2017
# Ganapathy Hari Narayan: ganapathy.hari.narayan@gatech.edu- Section A
# Vishal Gupta: vishal9gupta@gatech.edu - Section B


# Files Submitted:
### distance_vector_routing.py
#### the main file to run which contains a Node object, a Graph object, a function for each of the algorithms and functions to process the input. Finally its go the main script at the very bottom of the file which connects all these components together
### sample.txt
#### the sample output file contains a sample output from running a basic protocol. the contents of the events.txt and the routes3.txt is provided at the bottom of the sample.txt

# Running the program
## python3 distance_vector_routing.py routes3.txt events.txt 1 1
## Where the first parameter is the file name to run, the second parameter is the txt file with initial topology, the second parameter is text file with the topological events that can take place, the 3rd parameter is whether the output should be detailed or not (1 for detailed 0 for not) and the last paramter is the algorithm to run (0 - running all of them, 1 - running basic, 2 - running poison reverse, 3 - running split horizon)

# Bugs
## No known bugs