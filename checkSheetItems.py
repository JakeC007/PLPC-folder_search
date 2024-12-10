"""
Takes in a CSV file of websites. Then checks to see if those websites are in the Princeton corpus
Writes out a new CSV with a column next to each column with "None" if the website doesn't exist or the path to the website's policy
if the website does exist 
J. Chanenson
8/11/23
"""

import os, csv
import tldextract
from tqdm import tqdm

def findExactMatchInDir(path, website):
    """
    Searches for files in a directory (and its subdirectories) 
    that exactly match the provided domain, prioritizing .com domains.

    Parameters:
    - path (str): The current directory path.
    - website (str): The website URL or name to use for matching.

    Returns:
    - str or None: Returns the file path if a match is found, or None otherwise.
    """
    # Take in website URL or name
    if "." in website:
        domain = tldextract.extract(website).domain
    else:
        domain = website

    domain = domain.lower()  # Convert the domain to lowercase for case-insensitive match
    foundComPath = None  # Store path if .com TLD is found
    foundOtherPath = None  # Store path if any other TLD is found

    for entry in os.scandir(path):
        if entry.is_dir():
            # Recurse into the directory
            foundPath = findExactMatchInDir(entry.path, website)
            
            # If a match was found in the subdirectory
            if foundPath:
                 # Extract the filename and TLD
                fName = os.path.splitext(os.path.basename(foundPath))[0]
                _, _, ext = tldextract.extract(fName)
                
                # Check if the TLD is "com"
                if ext == "com":
                    return foundPath
                # If it's not a .com, but the domain is the same and no other match was found before
                elif not foundOtherPath:
                    foundOtherPath = foundPath
        
        # If the entry is not a directory, then it's a file
        else:
            # # Extract the filename and URL parts
            baseName, _ = os.path.splitext(entry.name)
            extractedResult = tldextract.extract(baseName)  # Extract domain and TLD
            
            # Check if the extracted domain matches our target domain
            if extractedResult.domain == domain:
                if extractedResult.suffix == "com":
                    return entry.path  
                # If it's not a .com and this is the first domain match
                elif not foundOtherPath:
                    foundOtherPath = entry.path
    
    # Return the .com match
    # If a .com match wasn't found, return the first non-.com match if it exists
    return foundComPath or foundOtherPath

# Read the CSV
def readCSV(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        return [row for row in reader]

# Write to a new CSV
def writeCSV(data, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def processCSV(inputFile, outputFile, directoryPath):
    data = readCSV(inputFile)
    newData = []
    headers = data[0]  # Assuming the first row is headers
    newHeaders = []
    for header in headers:
        newHeaders.append(header)
        newHeaders.append(header + " Exists")
    newData.append(newHeaders)

    # Check existence and append results
    for row in tqdm(data[1:]):  # skipping the header row
        newRow = []
        for item in row:
            # print(f"{item} | ", end="")
            newRow.append(item)
            if item:  # Check if the cell (item) is not empty
                
                result = findExactMatchInDir(directoryPath, item)  # Returns file path or None
                if result:
                    # print(result)
                    newRow.append(result)  # Add the file path to the new row
                else:
                    # print("None")
                    newRow.append("None")  # Add "None" if no match was found
            else:
                # print("Skipped")
                newRow.append('')
        newData.append(newRow)

    # Write to the new CSV file
    writeCSV(newData, outputFile)

if __name__ == '__main__':
    # Execute the function
    directory = "../privacy-policy-historical-master"
    output = "process_application_data\Corpus_Subset_Selection_Checked.csv"
    processCSV('process_application_data\Corpus_Subset_Selection.csv', output, directory)
    print(f"Wrote out checked CSV file to {output}")