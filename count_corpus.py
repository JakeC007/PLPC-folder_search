"""
Counts the number of tokens in the corpus 
There are three modes of input 
    - manually typing the paths into a python list; you edit function inputFromList
    - Getting the intersection between the Tranco top N and the corpus 
    - Reading in from a CSV that has the full file paths
J. Chanenson
8/10
"""

import csv, os, tiktoken, re

import gatherPopularSites


# Uncomment below if you need to download punkt
# import nltk
# nltk.download('punkt')

## Globals
# Tokenizer, make it global so it only loads in once
encoding = tiktoken.get_encoding("cl100k_base")


def inputFromList():
    """
    Returns a predefined list that the user can edit directly in this script.
    
    Returns:
        list: The user-edited list from the Python file.
    """
    # Input what files you want to read in 
    
    fileList = [
        '..\privacy-policy-historical-master\g\ge\gea\geappliances.com.md',
        #'path_to_file2.md',
        # Add paths to more files here...
    ]

    return fileList

def inputFromTranco(numSites):
    """
    Grabs the top N sites from the current tranco lists and finds the 
    intersection of those sites with what is in the corpus.

    Args:
        numSites (int): Number of sites to retrieve from Tranco.
    
    Returns:
        list: full file path for corpus documents
    """
    # Pull in data from Tranco and the matching documents in corpus
    fileList = []
    numDocs = 0 # How many matching domains are there in the corpus

    print(f"Gathering top {numSites} tranco sites from corpus...")
    results = gatherPopularSites.findTopSites(numSites, searchType="exact-TLD:com")
    print("Got the list of files!")
    
    for domain, paths in results.items():
        if paths:
            numDocs += 1

            if isinstance(paths, str):
                fileList.append(paths) # grab the only pathh
            else:
                fileList.append(paths[0]) # just grab one of the items 
    
    print(f"There are {numDocs} matching domains in the corpus")
    
    return fileList

def inputFromCSV(fileName):
    """
    Reads a given CSV file and returns all cells with `.md` at the end.
    Assumes that this CSV file has been run through `checkSheetItems.py`
    as that is the quickest way to generate full paths for the privacy
    policy documents
    
    Args:
        fileName (str): Path to the CSV file.
    
    Returns:
        list: full file path for corpus documents.
    """
    mdFiles = []
    with open(fileName, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        
        # Iterate through rows in the CSV file
        for row in csvreader:
            for cell in row:
                if cell and cell.endswith('.md'):
                    mdFiles.append(cell)
    return mdFiles

def dataInput():
    """
    Input function to define how we ingest the data for counting
    """
    print("Select an option:")
    print("1. Input from User List")
    print("2. Input from Tranco")
    print("3. Input from CSV")
    
    choice = int(input("Choice: "))

    if choice == 1:
       fileList = inputFromList()
    elif choice == 2:
        numSites = int(input("Enter the number of top sites you'd like to retrieve from Tranco: "))
        fileList = inputFromTranco(numSites)
    elif choice == 3:
        # fileName = input("Enter the CSV filename (with extension): ")
        fileName = "process_application_data\Corpus_Subset_Selection_Checked.csv"
        fileList = inputFromCSV(fileName)
    else:
        print("Invalid choice!")
    
    return fileList


def main():
    # Set up output CSV file
    # Set the outputPath to the same directory as the script
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    outputPath = os.path.join(scriptDir, 'corpusTokenCount.csv')
    checkCSVFile(outputPath)
    
    # Get data from one of three sources w/terminal input
    fileList = dataInput()

    print(f"\nRead in {len(fileList):,} documents. Counting tokens...")
    
    totalTokensForAllFiles = 0

    for inputPath in fileList:
        fileContent = readFile(inputPath)
        
        plainText = stripMarkdown(fileContent)
        
        tokenCount = countTokens(plainText)

        writeToCSV(outputPath, os.path.basename(inputPath), tokenCount)
        
        totalTokensForAllFiles += tokenCount

        # print(f"Token count for {os.path.basename(inputPath)} saved to {outputPath}.")

    print(f"Total tokens for all processed files: {totalTokensForAllFiles:,}")
    print(f"Total cost for all processed files: ${(totalTokensForAllFiles/1000)*.12:.2f}")


def checkCSVFile(outputPath):
    """
    Checks to see if the CSV file exists.
    If not, write the header.

    Parameters:
    - outputPath (str): Path to the csv file
    
    Returns:
    - None
    """
    if not os.path.exists(outputPath):
        with open(outputPath, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["File Name", "Token Count"])
    
    return None

def readFile(filePath):
    """
    Reads the content of a file.
    
    Parameters:
    - filePath (str): Path to the file to be read.

    Returns:
    - str: Content of the file.
    """
    with open(filePath, 'r', encoding='utf-8') as file:
        return file.read()

def stripMarkdown(markdownContent):
    """
    Strips common Markdown elements from a given string containing Markdown content.

    Parameters:
    - markdownContent (str): The content string with Markdown formatting.

    Returns:
    - str: The content with Markdown elements removed.
    """
    
    content = markdownContent

    ### REMOVE THE BLOCK QUOTE AT THE TOP OF THE FILE ##
    # This will match everything starting from the first block quote to the newline just before the first top-level heading.
    pattern = r'^(?:>.*\n)+\n(?=# )'

    # Replace the matched block quote with an empty string
    content = re.sub(pattern, '', content, flags=re.MULTILINE)

    # Links: ![alt_text](url) or [link_text](url)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # Images
    content = re.sub(r'\[.*?\]\(.*?\)', '', content)   # Links

    # Headers: # or ## or ### etc.
    content = re.sub(r'#+', '', content)

    # Emphasis: *italic* or **bold** or ***bolditalic***
    content = re.sub(r'\*+', '', content)

    ## Jake: leaving this in because we finetuned on lists
    # Lists: - item or * item or + item
    # content = re.sub(r'^[-\*+]\s+', '', content, flags=re.M)

    # Inline Code: `code`
    content = re.sub(r'`', '', content)

    # Blockquotes: > quote
    content = re.sub(r'^>\s+', '', content, flags=re.M)

    # Horizontal lines: --- or *** or - - -
    content = re.sub(r'^[\-_*]\s*[\-_*]\s*[\-_*]\s*$', '', content, flags=re.M)

    # Code blocks: ```code```
    content = re.sub(r'```.*?```', '', content, flags=re.S)

    return content

def countTokens(plainText):
    """
    Counts the tokens in a given plaintext string. 
    Using the GPT-3 token counter because its fast. 

    Parameters:
    - plainText (str): Plaintext content.

    Returns:
    - int: Number of tokens in the content.
    """
    return len(encoding.encode(plainText)) 

def writeToCSV(outputPath, fileName, tokenCount):
    """
    Writes the file name and token count to a CSV file, and keeps track of the total tokens.

    Parameters:
    - outputPath (str): Path to the output CSV file.
    - fileName (str): Name of the processed file.
    - tokenCount (int): Token count for the processed file.
    """

    with open(outputPath, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([fileName, tokenCount])

if __name__ == '__main__':
    main()
