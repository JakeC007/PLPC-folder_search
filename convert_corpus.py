"""
Takes in a list of privacy corpus files and chunks the corpus documents into a size
that would be good for a context window AND adds the BOS and EOS tokens.
These files are then written to their own CSV and added to a subdir with today's date
This is then saved to a CSV
J. Chanenson
8/8/23
"""
import csv, os, tiktoken, re
from nltk.tokenize import sent_tokenize, word_tokenize 
from datetime import date
import gatherPopularSites

# Uncomment below if you need to download punkt
# import nltk
# nltk.download('punkt')

# Tokenizer, make it global so it only loads in once
print("Loading in Tokenizer from tiktoken...")
encoding = tiktoken.get_encoding("cl100k_base")

def countTokens(text):
    """
    Count the number of tokens using tiktoken's encoder.

    Parameters:
    - text (str): The input string for which the number of tokens needs to be counted.

    Returns:
    - int: The number of tokens present in the given text after encoding.
    """
    return len(encoding.encode(text))  

def main():
    # Get list of files in corpus 
    fileList = dataInput()

    newSubdir = createNewSubdir()

    for inputPath in fileList:
        fileContent = readFile(inputPath)
        
        # Strip out md and the block quote at begining
        plainText = stripMarkdown(fileContent)

        # Splitting the text from the file into chunks
        chunks = splitIntoChunks(plainText, 1000)

        # Annotating chunks with BOS and EOS tokens and param tags
        annotatedChunks = addAnnotations(chunks)
        
        ## Diagonistics
        # Printing the token count for each annotated chunk
        for i, chunk in enumerate(annotatedChunks):
            print(f"Chunk {i+1}: {countTokens(chunk)} tokens")

        # Write the chunks to a file
        baseName = os.path.splitext(os.path.basename(inputPath))[0] 
        csvFilePath = os.path.join(newSubdir, f"{baseName.replace('.', '_')}.csv")

        with open(csvFilePath, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for chunk in annotatedChunks:
                writer.writerow([chunk])

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
    Input function to define how we ingest the data for chunking
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

def createNewSubdir():
    """
    Creates and returns a path to a new subdirectory named after today's date (formatted as YYYY-MM-DD).
    If the directory already exists, it simply returns the path without creating a new one.

    Parameters:
    None

    Returns:
    - str: Path to the new (or existing) subdirectory named after today's date.

    Example:
    path = createNewSubdir()
    print(path)  # Outputs: /CI-Annotation-GPT/production_csvs/2023-08-13 (or whichever today's date is)

    Note:
    The subdirectory is created in the 'production_csvs' directory which is one directory up from the script's directory.
    """
    
    # Get today's date and format it as YYYY-MM-DD
    todayDate = date.today().strftime('%Y-%m-%d')
    
    # Get the directory of the current script
    currentDir = os.path.dirname(os.path.abspath(__file__))

    # Go one directory up and then to 'production_csvs'
    parentDir = os.path.dirname(currentDir)
    productionCsvsDir = os.path.join(parentDir, "production_csvs")

    # Join the productionCsvsDir with today's date
    newSubdir = os.path.join(productionCsvsDir, todayDate)
    
    # Create new subdir if it doesn't exist
    if not os.path.exists(newSubdir):
        os.makedirs(newSubdir)

    return newSubdir

def handleLongSentence(sentence, maxTokens):
    """"
    Handle sentences that exceed the maxTokens limit by splitting them into 
    smaller chunks using LLM-friendly tokenization.
    
    Args:
    - sentence (str): The sentence to be handled.
    - maxTokens (int): Maximum number of tokens for each chunk.

    Returns:
    - List[str]: List of chunks derived from the long sentence.
    """
    words = word_tokenize(sentence)
    chunks = []
    
    # This list will temporarily hold words for the current chunk.
    currentChunk = []
    
    # Index to keep track of our position in the words list.
    wordIndex = 0

    # Continue until all words from the sentence have been processed.
    while wordIndex < len(words):
        # Calculate the space left in the current chunk.
        spaceLeft = maxTokens - countTokens(''.join(currentChunk))
        
        # Get a segment of words that can fit into the space left in the current chunk.
        segment = words[wordIndex:wordIndex + spaceLeft]
        
        for word in segment:
            # Check if the word is a punctuation or if the current chunk is empty.
            # If so, append the word without adding a space before it.
            if word in ["!", ",", ".", "?", ";", ":", "(", ")", "{", "}", "[", "]", "'", "\"", "—", "-", "..."] or not currentChunk:
                currentChunk.append(word)
            # Otherwise, add a space before appending the word.
            else:
                currentChunk.append(' ' + word)

        # Move the word index forward by the number of words we've just processed.
        wordIndex += spaceLeft
        
        # If the current chunk reaches the max token limit or we've processed all words, finalize the chunk.
        if countTokens(''.join(currentChunk)) >= maxTokens or wordIndex >= len(words):
            # Add the current chunk to the chunks list after removing any leading or trailing spaces.
            chunks.append(''.join(currentChunk).strip())
            
            # Reset the current chunk for further processing.
            currentChunk = []

    return chunks

def splitIntoChunks(text, maxTokens=1000):
    paragraphs = text.split('\n')
    chunks = []
    currentChunk = []

    for paragraph in paragraphs:
        sentences = sent_tokenize(paragraph)
        for sentence in sentences:
            sentenceTokens = countTokens(sentence)

            if sentenceTokens > maxTokens:
                if len(currentChunk) > 0:
                    chunks.append(' '.join(currentChunk))
                    currentChunk = []

                chunks.extend(handleLongSentence(sentence, maxTokens))

            # Add the sentence to current chunk if adding the sentence to the current chunk doesn't exceed the maximum tokens
            elif countTokens(' '.join(currentChunk) + ' ' + sentence) <= maxTokens:
                currentChunk.append(sentence)
            
            # If the sentence causes the current chunk to exceed the maximum tokens
            # Add the current chunk to the chunks list and start a new chunk with the current sentence.
            else:
                chunks.append(' '.join(currentChunk))
                currentChunk = [sentence]

        # Add a separator for paragraphs.
        if len(currentChunk) > 0:
            currentChunk.append("\n")

    # After processing all paragraphs, add the remaining chunk.
    if len(currentChunk) > 0:
        chunks.append(' '.join(currentChunk).strip())

    return chunks

def addAnnotations(chunkList):
    """
    Append "Annotate:" to the beginning and "--->" to the end of each item in the chunk list.
    Does this 9 times for the 9 CI-GKC parameters: 'Sender', 'Subject', 'Consequence', 'Modality', 'Recipient', 
              'Transmission-Principle', 'Condition', 'Aim', 'Attribute'

    Args:
    - chunkList (List[str]): List of text chunks.

    Returns:
    - List[str]: List of annotated text chunks.
    """
    # List of parameters
    params = ['Sender', 'Subject', 'Consequence', 'Modality', 'Recipient', 
              'Transmission-Principle', 'Condition', 'Aim', 'Attribute']
    
    # List to hold the annotated chunks
    annotatedList = []

    # For every chunk in the chunkList
    for chunk in chunkList:
        # For every parameter in params
        for param in params:
            # Create the desired format and append it to the annotatedList
            annotatedList.append("Annotate:" + chunk + " " + param + "--->")
    
    return annotatedList

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

if __name__ == "__main__":
    main()

