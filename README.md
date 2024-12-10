# Tools to Process the Privacy Corpus GitHub Repo

This repository provides a set of tools designed to manage and analyze the [Princeton-Leuven Longitudinal Corpus of Privacy Policies](https://github.com/citp/privacy-policy-historical) GitHub repo. These tools are located in the `process_application_data/` folder and assume you have a local copy of the corpus stored at `../privacy-policy-historical-master/` (in the same directory as the root of this repository).

## Prerequisites

Before using the tools, ensure that:
1. You have cloned or downloaded the Princeton Privacy Corpus into the specified location.
2. You have installed any necessary Python dependencies for running the scripts. Use `requirements.txt` if available, or install packages as needed.

## Overview of Tools

Below is a breakdown of the available scripts and their primary functionalities:

### 1. `convert_corpus.py`
**Purpose:** Prepares corpus documents for processing by a language model.

- **Functionality:**
  - Reformats documents by removing markdown elements and Princeton block quotes.
  - Adds beginning-of-sequence (BOS) and end-of-sequence (EOS) tokens.
  - Saves the processed document into individual CSV files under `production_csvs/` with a subfolder named by the current date.
  
- **Usage:** Run the script and ensure the source and destination paths are properly configured.

---

### 2. `checkSheetItems.py`
**Purpose:** Verifies whether websites listed in a CSV file are included in the Princeton corpus.

- **Functionality:**
  - Accepts a CSV file containing a list of website URLs (update the file path in the script).
  - Outputs a new CSV file (edit the destination path in the script) with:
    - The original list of websites in one column.
    - A second column indicating:
      - `"None"` if the website is not in the corpus.
      - The path to the website’s policy if it is included.

- **Usage:** Adjust input and output file paths within the script before execution.

---

### 3. `convert_corpus.py`
**Purpose:** Calculates the total number of tokens in a document or a list of documents.

- **Functionality:**
  - Processes one or multiple documents to count tokens, assisting in assessing text size and preparing for downstream tasks.

- **Usage:** Run the script and configure the input document paths as needed.

---

### 4. `gatherPopularSites.py`
**Purpose:** Identifies overlap between popular websites and the Princeton corpus.

- **Functionality:**
  - Pulls the top N most visited websites based on the [Tranco list](https://tranco-list.eu/).
  - Finds the intersection of these websites with the Princeton corpus to determine which popular sites are covered.

- **Usage:** Adjust the value of `N` and ensure access to the Tranco list data.

---

## Folder Structure

```bash
root/
├── process_application_data/
│   ├── convert_corpus.py
│   ├── checkSheetItems.py
│   ├── convert_corpus.py
│   ├── gatherPopularSites.py
├── privacy-policy-historical-master/  # Clone of the Princeton corpus
├── production_csvs/                   # Output folder for processed data
```

## Notes
- Update script paths and variables as needed for your local environment.