from datetime import datetime
import fitz  # PyMuPDF
import re
import requests
from dotenv import load_dotenv
import os

# Specify the correct path to your .env file if it's not in the root
load_dotenv()

api_key = os.getenv('API_KEY')
if not api_key:
    print("API key not loaded. Check your .env file and path.")
else:
    print("API key loaded successfully.")

file_path = r'C:\Users\User\OneDrive\Desktop\Local - Green Metric Technologies\Green Analytics\Carbon Guild\CG-Protocol-Tool\Protocols\VM0025-Campus-Clean-Energy-and-Energy-Efficiency-v1.0.pdf'

#full text extraction for Summarization & Project
def extract_text_from_pdf(file_path):
    try:
        document = fitz.open(file_path)
        text = "".join([page.get_text() for page in document])
        document.close()
        return text
    except Exception as e:
        print(f"Error opening/reading the PDF file: {e}")
        return None

def extract_info_from_pdf(file_path):
    try:
        # Improved structure by using a context manager for handling the document
        with fitz.open(file_path) as pdf_document:
            # Initializing a dictionary to hold all the extracted data
            extracted_data = {}
            
            # Check if the PDF has enough pages to avoid IndexError
            if len(pdf_document) < 3:
                print("PDF does not have enough pages to extract all data.")
                return None

            # Extract text from the first three pages (assuming they contain relevant info)
            first_page_text = pdf_document[0].get_text()
            toc_text = "".join([pdf_document[i].get_text() for i in range(1, min(3, len(pdf_document)))])

            # Extract specific details
            extracted_data["Publish Standard Body"] = extract_publishing_standard_body(first_page_text)
            extracted_data["Protocol Name"] = extract_protocol_name(first_page_text)
            extracted_data["Protocol Version"] = extract_protocol_version(first_page_text)
            extracted_data["Release Date"] = extract_release_date(first_page_text)
            extracted_data["Protocol Code"] = extract_protocol_code(first_page_text)
            extracted_data["GHG Emission Type"] = extract_emissions_type(toc_text)

            # Hardcoded values (consider extracting dynamically if format standardizes)
            extracted_data["Additionality Requirements"] = "The project must demonstrate that its activities result in greater GHG reductions or removals than what would naturally occur in a standard scenario, proving that these activities are a direct result of carbon market incentives. Key to this requirement is the concept of 'regulatory surplus,' which requires that the project activities are not required by any existing government policies or laws."
            extracted_data["Monitoring Project Time, Project Longevity"] = "Under the VCS Standard, projects are required to have a minimum project longevity of 40 years."

            return extracted_data

    except Exception as e:
        print(f"Error extracting information: {e}")
        return None

def extract_publishing_standard_body(text):
    if "VCS" in text or "Verified Carbon Standard" in text:
        return "Verified Carbon Standard"
    elif "Another Standard" in text:
        return "Another Standard"
    else:
        return "Unknown"

def extract_protocol_name(text):
    match = re.search(r'VM\d{4}', text)
    if match:
        return match.group()
    return "Unknown"
    
def extract_protocol_version(text):
    # Regular expression to find the pattern "Version X.X"
    match = re.search(r'Version\s+\d+\.\d+', text)
    if match:
        return match.group()
    return "Unknown"

def extract_release_date(text):
    # Regular expression to find the date pattern (e.g., "12 February 2014")
    match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', text)
    if match:
        # Parse the matched date
        try:
            date_object = datetime.strptime(match.group(), '%d %B %Y')
            # Format the date in the desired format (e.g., "2023-02-12")
            return date_object.strftime('%Y-%m-%d')
        except ValueError:
            return "Unknown"  # Return "Unknown" in case of parsing error
    return "Unknown"

def extract_protocol_code(text):
    pattern = r'(VM\d{4}|ACM\d{4})'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_emissions_type(text):
    # Regular expression to find both singular and plural forms
    pattern = r'Reduction(?:s)?|Removal(?:s)?'
    matches = re.findall(pattern, text)

    # Initialize variables to track the presence of each term
    has_removal = 'Removal' in matches or 'Removals' in matches
    has_reduction = 'Reduction' in matches or 'Reductions' in matches

    # Concatenate the terms in the desired order
    if has_removal and has_reduction:
        return 'Removal and Reduction'
    elif has_removal:
        return 'Removal'
    elif has_reduction:
        return 'Reduction'
    else:
        return "Unknown"

def extract_additionality_reqs(text):
    return "The project must demonstrate that its activities result in greater GHG reductions or removals than what would naturally occur in a standard scenario, proving that these activities are a direct result of carbon market incentives. Key to this requirement is the concept of ""regulatory surplus,"" which requires that the project activities are not required by any existing government policies or laws."

def extract_project_time(text):
    if "VCS" in text or "Verified Carbon Standard" in text:
        return "Under the VCS Standard, projects are required to have a minimum project longevity of 40 years."

def summarize_text(text, api_key):
    url = "https://api.openai.com/v1/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model":"gpt-3.5-turbo", #specify model
        "prompt": f"Summarize the following text: \n\n{text}",
        "max_tokens": 150,  # Adjust based on how detailed you want the summary
        "temperature": 0.5 #adjust creativity / variability of the summary
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    if 'choices' not in response_data or not response_data['choices']:
        print("Failed to retrieve summary:")
        print(response_data)  # This will show what the API actually returned
        return None
    return response_data['choices'][0]['text']

def main(file_path):
    text = extract_text_from_pdf(file_path)
    if text is not None:
        summary_response = summarize_text(text, api_key)
        if summary_response:
            print("Summary of the Document:")
            print(summary_response)
        else:
            print("No summary available.")

        extracted_info = extract_info_from_pdf(file_path)
        if extracted_info:
            print("Extracted Information:")
            for key, value in extracted_info.items():
                print(f"{key}: {value}")
    else:
        print("Failed to extract text from the PDF.")

# Usage
main(file_path)

#Detemine execution context
if __name__ == "__main__":
    file_path = r'C:\Users\User\OneDrive\Desktop\Local - Green Metric Technologies\Green Analytics\Carbon Guild\CG-Protocol-Tool\Protocols\VM0025-Campus-Clean-Energy-and-Energy-Efficiency-v1.0.pdf'
    main(file_path)
