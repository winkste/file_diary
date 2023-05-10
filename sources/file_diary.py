""" This module creates a backup archive of folder content + archive report
    text file.

This program generates a backup of an input path and places this backup
into an output path. Additional it is generating a text file as log file
with all elements stored into the archive. Only elements stored in the
archive shall be listed in the text file and will be moved to trash.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Stephan Wink"
__contact__ = "stephan_wink@web.de"
__copyright__ = "Copyright $2022, $WShield"
__date__ = "2022/11/12"
__deprecated__ = False
__email__ =  "stephan_wink@web.de"
__license__ = "GPLv3"
__maintainer__ = "Stephan Wink"
__status__ = "Development"
__version__ = "0.0.1"

################################################################################
# Imports
import os
import datetime
import logging
from pathlib import Path
import xml.etree.ElementTree as ET
import pprint
from datetime import date
import shutil
#import zipfile


logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s - %(filename)s/%(funcName)s(%(lineno)d) - %(levelname)s - %(message)s")

################################################################################
# Variables

################################################################################
# Functions
def main(input_path_name:str, output_path_name:str):
    """
        This is the main processing function
    """

    # check input parameter
    try:
        input_path, output_path = create_file_pathes(input_path_name, output_path_name)
    except TypeError:
        print("Input parameter error")
        return -1

    # get list of new files in the input directory
    list_of_files = get_list_of_files_in_directory(input_path)
    logging.debug("found %d files in the input folder.", len(list_of_files))

    # create the file dictionary with datetime as keys
    file_dict = get_timestamp_based_file_dictionary(list_of_files)
    logging.debug("files categorized according to date")

    # move the identified files from input to output path sorted by date
    moved_files = move_files_to_diary_path(file_dict, input_path, output_path)
    logging.debug("number of files moved to new folder: %d", moved_files)

    # create a diary file on the complete output folder and store it with date
    store_diary_file(file_dict, output_path)
    logging.debug("diaries generated")

    return 0

def create_file_pathes(input_path_name:str, output_path_name:str) -> Path:
    """This function creates the input and output pathes
    Args:
        input_path_name (str): input path name
        output_path_name (str): output or destination path name
    Raises:
        TypeError: in case of error with pathes
    Returns:
        Path: input and output pathes
    """
    if not isinstance(input_path_name, str) or not isinstance(output_path_name, str):
        raise TypeError("Arguments are not strings")

    input_path = Path(input_path_name)
    output_path = Path(output_path_name)
    logging.debug("Input path %s", os.path.abspath(input_path))
    logging.debug("Output path %s", os.path.abspath(input_path))

    if not input_path.exists() or not output_path.exists():
        raise TypeError("Pathes are not existing")

    if not input_path.is_dir() or not output_path.is_dir():
        raise TypeError("Arguments are not pathes")

    return input_path, output_path

def get_list_of_files_in_directory(directory:Path)->list:
    """Creates a list including all filenames from a given directory
    Args:
        directory (Path): directory to create file list from
    Returns:
        list: list of files, empty list if no files in directory
    """
    # get all files including path in a list
    list_of_files = []
    for (dir_path, _ , files) in os.walk(directory):
        list_of_files += [os.path.join(dir_path, file) for file in files]
    return list_of_files

def get_timestamp_based_file_dictionary(file_list:list)->dict:
    """Generates a date timestamp based dictionary with assosiated file lists
    Args:
        file_list (list): list of files that shall be grouped in dictionary
    Returns:
        dict: a dictionary with datetime as string as key and list of files
    """
    # Create an empty dictionary to store the files and their modification times
    file_dict = {}
    # Loop through each file in the list
    for filename in file_list:
        # Check if the path is a file and not a directory
        if os.path.isfile(filename):
            # Get the modification time of the file
            mod_time = os.path.getmtime(filename)
            # Convert the modification time to a datetime object
            mod_time = datetime.datetime.fromtimestamp(mod_time)
            mod_time = mod_time.strftime("%Y%m%d")
            # Add the file to the dictionary with its modification time as the key
            if mod_time in file_dict:
                file_dict[mod_time].append(filename)
            else:
                file_dict[mod_time] = [filename]
    return file_dict

def move_files_to_diary_path(file_dict:dict, input_path:Path, output_path:Path)->int:
    """Moves the files from dictionary based on datetime to output folder

    Args:
        file_dict (dict): datetime based file dictionary
        input_path (Path): input path
        output_path (Path): output path
    Returns:
        int: the number of files moved to output folder
    """
    moved_files:int = 0
    # create date specific sub folders in output if not exist
    # Loop through each key-value pair in the dictionary
    for key, value in file_dict.items():
        new_path_name = os.path.join(output_path, key)
        for file in value:
            new_file = file.replace(str(input_path), new_path_name)
            # check if new file already exist at destination
            if not os.path.isfile(new_file):
                # Split the file path into directory and file name components
                new_directory_path, _ = os.path.split(new_file)
                # Create the destination directory if it doesn't exist
                if not os.path.exists(new_directory_path):
                    os.makedirs(new_directory_path)
                # move files according to sorting into correct sub folder
                shutil.move(file, new_directory_path)
                moved_files = moved_files + 1
    return moved_files

def store_diary_file(diary_dict:dict, output_path:Path):
    """This function controls the storing of the diary
    Args:
        diary_dict (dict): datetime based dictionary of file lists
        output_path (Path): the target path for the dictionary
    """
    store_diary_file_as_python_code(diary_dict, output_path)
    store_diary_file_as_xml(diary_dict, output_path)

def store_diary_file_as_python_code(diary_dict:dict, output_path:Path):
    """This function stores a diary into a python code file format.
    Args:
        diary_dict (dict): datetime based dictionary of file lists
        output_path (Path): the target path for the dictionary
    """
    # generate the file path and name
    python_file = os.path.join(output_path, generate_diary_file_name() + ".py")

    # open the new file
    with open(python_file, 'w', encoding="utf-8") as file:
        # write the data to the python file using pprint pformat function
        file.write("diary = \n" + pprint.pformat(diary_dict) + '\n')


def store_diary_file_as_xml(diary_dict:dict, output_path:Path):
    """
        This function stores a diary into an xml format
    Args:
        diary_dict (dict): datetime based dictionary of file lists
        output_path (Path): the target path for the dictionary
    """

    # generate the file path and name
    xml_file = os.path.join(output_path, generate_diary_file_name() + ".xml")

    # Create an XML element for the root node
    root = ET.Element('files')

    # Loop through each key-value pair in the dictionary and add it as a child element
    for mod_time, filenames in diary_dict.items():
        # Create an XML element for the key (modification time)
        key = ET.SubElement(root, 'modification_time')
        key.text = mod_time
        # Loop through each filename in the value (list of files)
        for filename in filenames:
            # Create an XML element for the filename and add it as a child element of the key
            file_elem = ET.SubElement(key, 'file')
            file_elem.text = filename

    # Create an XML tree from the root element
    tree = ET.ElementTree(root)

    with open(xml_file, "w", encoding="utf-8") as file:
        tree.write(file, encoding="unicode", method="xml", short_empty_elements=True)

def generate_diary_file_name()->str:
    """Generates the diary file name

    Returns:
        str: file name as string
    """
    # datetime object containing current date and time
    now = datetime.datetime.now()
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%Y%m%d_%H%M%S")
    return dt_string


################################################################################
# Classes

################################################################################
# Scripts
if __name__ == "__main__":
    # execute only if run as a script
    print('--- file_diary script ---')
    main(os.path.join(os.getcwd(), 'test_input_folder'),
         os.path.join(os.getcwd(), 'test_output_folder'))
