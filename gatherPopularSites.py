"""
Uses the tranco list to find popular websites in the corpus 
Prints the list of those filed and their paths to the terminal
J. Chanenson
8/10/2023
"""

from tranco import Tranco
import os, tldextract
from tqdm import tqdm

def findTopSites(numSites, searchType = "exact"):
    """
    Gets the top sites from tranco and then looks for them in a given directory 
    Options for kwarg: "fuzzy", "exact", "exact-TLD:com"
    Parameters:
    - numSites (int): the top N sites 
    
    Returns:
    - file paths for the matching sites
    """
    # Handle kwarg
    VALID_SEARCH_TYPES = ["fuzzy", "exact", "exact-TLD:com"]

    searchType_explanations = {
        "fuzzy": "Fuzzy returns multiple items that are a fuzzy match for the item e.g., 'google' would return 'google', 'google-shop', and 'googlesucks'.",
        "exact": "Exact returns multiple items that are an exact match in the corpus.",
        "exact-TLD:com": "Exact-TLD:com returns a single item that is an exact match in the corpus, prioritizing the TLD '.com' if available."
    }

    if searchType not in VALID_SEARCH_TYPES:
        explanations = "\n".join([f"{key} - {value}" for key, value in searchType_explanations.items()])
        raise ValueError(f"Invalid searchType. Expected one of {VALID_SEARCH_TYPES}, but got '{searchType}'.\n\n{explanations}")

    # Get Tranco rankings 
    t = Tranco(cache=True, cache_dir='.tranco')
    latest_list = t.list()
    
    siteLst = latest_list.top(numSites)
    directory = "../privacy-policy-historical-master"
    
    # print(f"Looking for {siteLst}")
    
    # Search corpus for tranco website matches
    if searchType == "exact":
        fileDict = findMatchingFiles(siteLst, directory, exact=True)
    elif searchType == "fuzzy":
        fileDict = findMatchingFiles(siteLst, directory, exact=False)
    elif searchType == "exact-TLD:com":
        # Recall findExactMatchInDirTLD only handles one file at a time 
        # and only returns one match
        fileDict = {}
        for website in tqdm(siteLst):
            result = findExactMatchInDirTLD(directory, website)
            # Recall the function sometimes returns none, we don't want that
            if result is not None: 
                # Need this to match the keys in findMatchingFiles's output
                extracted_domain = tldextract.extract(website).domain
                fileDict[extracted_domain] = result
    else:
        print(f"You've reached this branch in error")


    return fileDict

def findExactMatchInDirTLD(path, website):
    """
    Searches for files in a directory (and its subdirectories) 
    that exactly match the provided domain, *prioritizing .com domains*.

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
            foundPath = findExactMatchInDirTLD(entry.path, website)
            
            # If a match was found in the subdirectory
            if foundPath:
                 # Extract the filename and TLD
                fName = os.path.splitext(os.path.basename(foundPath))[0]
                subDomain, _, ext = tldextract.extract(fName)
                
                # Check if the TLD is "com"
                if ext == "com" and subDomain == '':
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

def findMatchingFilesSlow(websites, directory):
    """
    Sinsible, os.walk implementation -- just slower than recurisve

    Searches for files in a given directory (and its subdirectories) that have a filename
    containing a base name from the provided list of websites.
    
    Parameters:
    - websites (list): A list of website URLs to use for matching.
    - directory (str): The path to the directory in which to start the search.
    
    Returns:
    - list: A list of file paths that match the criteria.
    """
    
    matches = []  # List to store matching file paths

    # Traverse through each file in the directory and its subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            for site in websites:
                # Extract the part of the website before the first dot (e.g., 'google' from 'google.com')
                baseName = site.split('.')[0]
                
                # Check if the base name is present in the filename
                if baseName in file:
                    # If a match is found, add the full path to the matches list
                    matches.append(os.path.join(root, file))
                    break  # Break out of the inner loop once a match is found

    return matches

def findExactMatchInDir(path, websites, matches, thresholds):
    """
    Searches for files in a directory (and its subdirectories) 
    that exactly match the provided domains, up to a certain threshold.

    Parameters:
    - path (str): The current directory path.
    - websites (list): A list of website URLs to use for matching.
    - matches (dict): A dictionary to store matching file paths for each domain.
    - thresholds (dict): Keeps track of match counts for each domain.
    """
    domains = [tldextract.extract(site).domain for site in websites]

    for entry in os.scandir(path):
        if entry.is_dir():
            # Recurse into the directory
            findExactMatchInDir(entry.path, websites, matches, thresholds)
        else:
            # Removing the actual file extension for comparison
            base_name, file_ext = os.path.splitext(entry.name)
            extracted_domain = tldextract.extract(base_name).domain  # Extract the domain from the filename
            
            if extracted_domain in domains and thresholds[extracted_domain] < 5:
                matches[extracted_domain].append(entry.path)
                thresholds[extracted_domain] += 1

def scanDir(path, websites, matches, thresholds):
    """
    Recursively scans a directory and its subdirectories for files matching given websites.

    Parameters:
    - path (str): The current directory path.
    - websites (list): A list of website URLs to search for.
    - matches (dict): A dictionary to store matching file paths for each domain.
    - thresholds (dict): Keeps track of match counts for each domain.

    Note:
    For each directory it encounters, it calls itself.
    """
    for entry in os.scandir(path):
        # If the current entry is a directory, we recursively scan its contents.
        if entry.is_dir():
            scanDir(entry.path, websites, matches, thresholds)
        else:
            # Remove the actual file extension (like .md) before processing
            base_name = os.path.splitext(entry.name)[0]

            for site in websites:
                domain = tldextract.extract(site).domain  # Extracts the primary domain name, ignoring subdomains
                
                # Check if we haven't reached the match limit for this domain
                if thresholds[domain] < 5: 
                    # If the domain is found in the file name (base_name), record the match
                    if domain in base_name:
                        matches[domain].append(entry.path)
                        thresholds[domain] += 1  # Update the match count  # Update the match count

def findMatchingFiles(websites, directory, exact=False):
    """
    Search for files in a directory and its subdirectories with names matching the given websites.

    Parameters:
    - websites (list): A list of website URLs to use for matching.
    - directory (str): Starting directory path for the search.
    - exact (bool): When true we only look for exact matches.

    Returns:
    - dict: Dictionary with domains as keys and lists of matching file paths as values.
    """
    # Prepare dictionaries to store matches and thresholds
    domains = [tldextract.extract(site).domain for site in websites]
    matches = {domain: [] for domain in domains}
    thresholds = {domain: 0 for domain in domains}

    if exact:
        # function for exact matches
        findExactMatchInDir(directory, websites, matches, thresholds)
    else:
        # recursive scan, non exact matches
        scanDir(directory, websites, matches, thresholds)

    return matches

def findFilesByTLDs(path, gtlds):
    """
    Searches for files in a directory (and its subdirectories) 
    that contain specified gTLDs in their filenames.

    Parameters:
    - path (str): The current directory path.
    - gtlds (list): List of gTLDs (like ['.com', '.org', ...]) to search for.

    Returns:
    - dict: A dictionary with gTLDs as keys and lists of matching file paths as values.
    """
    matches = {gtld: [] for gtld in gtlds}

    for entry in os.scandir(path):
        if entry.is_dir():
            # Merge dictionaries from recursive search
            sub_matches = findFilesByTLDs(entry.path, gtlds)
            for key in sub_matches:
                matches[key].extend(sub_matches[key])
        else:
            # Removing the actual file extension for tldextract to work correctly
            base_name, file_ext = os.path.splitext(entry.name)
            extracted = tldextract.extract(base_name)
            tld = '.' + extracted.suffix  # Getting the gTLD
            if tld in gtlds:
                matches[tld].append(entry.path)

    return matches

def justURL(path):
    """
    Takes in a full path and spits out just the URL

    Parameters:
    - path (str): The full path to a file

    Returns:
    - str: just the URL  
    """
    return os.path.splitext(os.path.basename(path))[0]

def fuzzyMatchIndex(myList, query):
    """
    Search for a query string within elements of a list and return the index of the first match.
    
    Parameters:
    - myList (list): The list of strings in which to search.
    - query (str): The substring to search for within the list elements.

    Returns:
    - int: The index of the first list element containing the query, or -1 if not found.
    """
    for index, element in enumerate(myList):
        extracted_domain = tldextract.extract(element).domain
        if query == extracted_domain:
            return index
    return -1  # Return -1 if no match is found

if __name__ == '__main__':
    ## Use the following to look for specfic TLDS e.g., .gov, .com, etc.
    # directory = "../privacy-policy-historical-master"
    # desired_gtlds = [ '.gov']
    # results = findFilesByTLDs(directory, desired_gtlds)

    # for gtld, paths in results.items():
    #     if paths:
    #         print(f"Files containing '{gtld}':")
    #         for path in paths:
    #             print(justURL(path)) 
    #         print("-" * 40)


    # t = Tranco(cache=True, cache_dir='.tranco')
    # latest_list = t.list()
    # print(latest_list.top(100))

    # # Sample list of websites to search for
    # websites = ["google.com", "wikipedia.com"]
    
    # # Path to the directory where the search should start
    # directory = "../privacy-policy-historical-master"
    
    # # Get the results
    # results = findMatchingFiles(websites, directory, exact=True)
    
    ## Print out the Tranco top N domains with ranking
    numSite = 200
    results = findTopSites(numSite, searchType="exact-TLD:com")
    t = Tranco(cache=True, cache_dir='.tranco')
    trancoRank = t.list().top(numSite)
    # Print out the matching files for each domain
    domainCount = 0
    for domain, paths in results.items():
        if paths:
            domainCount += 1
            print(f"Matching files for Rank {fuzzyMatchIndex(trancoRank, domain) + 1}: {domain}:")
            print(os.path.splitext(os.path.basename(paths))[0])
            # justURL(paths)
            # for path in paths:
            #     print(justURL(path))
            print("-" * 40)
    print(f"From the Tranco top {numSite}, there are {domainCount} domains in the corpus")
