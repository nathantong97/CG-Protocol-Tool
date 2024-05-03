from datetime import datetime
import fitz  # PyMuPDF
import re
import requests
from dotenv import load_dotenv
import os

# Specify the correct path to your .env file if it's not in the root - Load API Key
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

#Extract specific details
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
            #toc_text = "".join([pdf_document[i].get_text() for i in range(1, min(3, len(pdf_document)))]) #Pages 2 and 3 - depreciated
            first_six_pages_text = "".join([pdf_document[i].get_text() for i in range(min(6, len(pdf_document)))])

            # Extract Standards body for use in identifying additionality reqs, crediting period & longevity
            extracted_data["Publish Standard Body"] = extract_publishing_standard_body(first_six_pages_text)
            standard_body = extract_publishing_standard_body(first_six_pages_text)
            extracted_data["Publish Standard Body"] = standard_body

            #Extract Specific details - Python
            extracted_data["Protocol Name"] = extract_protocol_name(first_page_text)
            extracted_data["Protocol Version"] = extract_protocol_version(first_page_text)
            extracted_data["Release Date"] = extract_release_date(first_page_text)
            extracted_data["Protocol Code"] = extract_protocol_code(first_page_text)
            extracted_data["GHG Emission Type"] = extract_emissions_type(first_six_pages_text)

            # Hardcoded values (consider extracting dynamically if format standardizes) #Will likely be passed off to the LLM
            extracted_data["Additionality Requirements"] = extract_additionality_reqs(standard_body)
            extracted_data["Crediting Period"] = extract_crediting_period(standard_body)
            extracted_data["Project Longevity"] = extract_project_time(standard_body)

            return extracted_data

    except Exception as e:
        print(f"Error extracting information: {e}")
        return None

def extract_publishing_standard_body(text):
    text_lower = text.lower()
    if "vcs" in text_lower or "verified carbon standard" in text_lower:
        return "Verified Carbon Standard"
    elif "acrcarbon.org" in text_lower or "american carbon registry" in text_lower:
        return "American Carbon Registry"
    elif "climate action reserve" in text_lower or "climateactionreserve" in text_lower or "car" in text_lower:
        return "Climate Action Reserve"
    else:
        return "Unknown"

def extract_protocol_name(text):
    protocol_name = "Unknown"  # Default if no name is found

    # Trying to capture the first significant line or title before "Version" or other keywords
    match = re.search(r"^(.*?)(?:Version|Protocol|\d{1,2} [A-Za-z]+ \d{4})", text, re.MULTILINE | re.DOTALL)
    if match:
        # Extract the matched group and strip any excess whitespace
        protocol_name = match.group(1).strip()
        # Replace newlines and multiple spaces to ensure it's on one line
        protocol_name = re.sub(r'\s+', ' ', protocol_name.replace('\n', ' ')).strip()
    return protocol_name
    
def extract_protocol_version(text):
    # Regular expression to find the pattern "Version X.X"
    match = re.search(r'Version\s+\d+\.\d+', text)
    if match:
        return match.group()
    return "Unknown"

def extract_release_date(text):
    # Regular expression to find the date patterns "12 February 2014" and "March 19, 2024"
    # This regex accommodates both by making the day part optional for the second format
    match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})|(\w+\s+\d{1,2},\s+\d{4})', text)
    if match:
        # Extract the matched date string
        date_str = match.group(0)

        # Define possible date formats
        date_formats = ['%d %B %Y', '%B %d, %Y']

        # Try parsing the date with each format
        for date_format in date_formats:
            try:
                date_object = datetime.strptime(date_str, date_format)
                return date_object.strftime('%Y-%m-%d')
            except ValueError:
                continue  # If parsing fails, try the next format

    return "Unknown"  # Return "Unknown" if no valid date is found or parsing fails

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

#Likely will need to use the LLM to extract this information.    
def extract_geographical_applicability(text):
    # Define keywords or phrases for regions
    regions = {
        'Europe': {'europe', 'eu', 'european union'},
        'USA': {'usa', 'united states', 'us', 'america'},
        'Canada': {'canada', 'canadian'},
        'Global': {'global', 'international', 'worldwide'},
        'Asia': {'asia', 'asean', 'asian region'},
        # Add more regions and keywords as needed
    }

    # Prepare a dictionary to store detected regions
    detected_regions = []

    # Check for each region in the text
    for region, keywords in regions.items():
        if any(keyword in text for keyword in keywords):
            detected_regions.append(region)

    # Special logic for combined regions
    if 'USA' in detected_regions and 'Canada' in detected_regions:
        return 'North America'
    elif detected_regions:
        return ', '.join(detected_regions)  # Join all found regions with comma

    return "Global"  # Default return if no regions are matched

def extract_additionality_reqs(text):
    if "VCS" in text or "Verified Carbon Standard" in text:
        return "The project must demonstrate that its activities result in greater GHG reductions or removals than what would naturally occur in a standard scenario, proving that these activities are a direct result of carbon market incentives. Key to this requirement is the concept of ""regulatory surplus,"" which requires that the project activities are not required by any existing government policies or laws."
    if "CAR" in text or "Climate Action Reserve" in text:
        return "CAR uses a standardized approach to determine ""additionality"" for offset programs. This method involves specific performance standards and criteria that exclude non-additional or ""business as usual"" projects. Projects mandated by law or regulation are not considered additional. This approach provides clarity on project eligibility and aims to minimize errors​​."
    
def extract_crediting_period(text):
    if "VCS" in text or "Verified Carbon Standard" in text:
        return "The initial crediting period must be at least 20 years but can be up to a maximum of 100 years. This period can be renewed up to four times, with the total project crediting period not exceeding 100 years."
    if "CAR" in text or "Climate Action Reserve" in text:
        return "Up to 100 years"

def extract_project_time(text):
    if "VCS" in text or "Verified Carbon Standard" in text:
        return "Under the VCS Standard, projects are required to have a minimum project longevity of 40 years."
    if "CAR" in text or "Climate Action Reserve" in text:
        return "100 years"

#LLM Extracted data - Send to OpenAI API
def summarize_and_extract_details(text, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Expanded prompt to ask for more specific details
    prompt_text = (
    "Provide the following details for this protocol, each separated by '###':\n"
    "- Project Summary: A brief overview of the protocol in less than 100 words.\n"
    "- Project Activities: Describe what actions are required by this protocol.\n"
    "- Geographical Applicability: Firstly state where the methodology is applied 'Global', 'U.S', 'U.S and Canada', 'Europe' or 'Asia'. Then provide extra details if necessary.\n"
    "- Additionality Requirements: Explain the criteria for additionality.\n"
    "- Crediting Period: Define the crediting period, if specified.\n"
    "- Project Longevity: Describe the expected duration of project activities.\n"
    "- Baseline Methodology: First state whether the methodology is 'Historical', 'Dynamic', or 'Both'. Then, provide a detailed explanation of how it works.\n"
    "- Protocol Type (Taxonomy): First state the taxonomy category based on the Oxford Protocols.\n\n"
    "### Project Summary\n"
    "### Project Activities\n"
    "### Geographical Applicability\n"
    "### Additionality Requirements\n"
    "### Crediting Period\n"
    "### Project Longevity\n"
    "### Baseline Methodology\n"
    "### Protocol Type (Taxonomy)\n\n"
    f"{text}"
)

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt_text}
        ],
        "max_tokens": 800,  # Increased token limit to accommodate more detailed queries
        "temperature": 0  # Adjusted for a balance between creativity and relevance
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    if 'error' in response_data:
        print("Failed to retrieve summary due to API error:", response_data['error']['message'])
        return None
    if 'choices' not in response_data or not response_data['choices']:
        print("No response available.")
        return None

    # Extract and return detailed responses from the model's output
    return response_data['choices'][0]['message']['content']


def parse_response_details(response_text):
    details = {}
    sections = response_text.split("###")

    # Define a dictionary to map headers to their processing labels
    header_to_label = {
        'Project Summary': 'Project Summary',
        'Project Activities': 'Project Activities',
        'Geographical Applicability': 'Geographical Applicability',
        'Additionality Requirements': 'Additionality Requirements',
        'Crediting Period': 'Crediting Period',
        'Project Longevity': 'Project Longevity',
        'Baseline Methodology': 'Baseline Methodology',
        'Protocol Type (Taxonomy)': 'Protocol Type (Taxonomy)'
    }

    # Process each section
    for section in sections:
        for header, label in header_to_label.items():
            if header in section:
                # Remove the header from the section and strip unwanted characters
                content = section.replace(header, '').strip()
                # Remove leading hyphens and extra spaces
                content = content.lstrip('- ').strip()
                details[label] = content
                break

    return details


#Combine specific details & LLM extracted data
def main(file_path, api_key):
    text = extract_text_from_pdf(file_path)
    if text is not None:
        # Execute detailed text info / datapoints - Python
        extracted_info = extract_info_from_pdf(file_path)
        if extracted_info:
            print("Extracted Information:")
            for key, value in extracted_info.items():
                print(f"{key}: {value}")

        #LLM Data
        response = summarize_and_extract_details(text, api_key)
        if response:
            parsed_details = parse_response_details(response)
            for key, value in parsed_details.items():
                print(f"{key}: {value}")
    else:
        print("Failed to extract text from the PDF.")

#Detemine execution context
if __name__ == "__main__":
    main(file_path,api_key)



"""
Test pdfs:
CAR-US-and-Canada-Biochar-Protocol-V1.0.pdf
VM0025-Campus-Clean-Energy-and-Energy-Efficiency-v1.0.pdf
ACR-ACoF-Methodology-v1.0.pdf
VM0047_ARR_v1.0-1.pdf
"""



"""
def summarize_and_extract_details_with_claude(text, claude_api_key):
    # Assuming the base URL and endpoint for Claude's API
    url = "https://api.anthropic.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Expanded prompt to ask for more specific details, similarly structured
    prompt_text = (
        "Provide the following details for this protocol, each separated by '###':\n"
        "- Project Summary: A brief overview of the protocol in less than 100 words.\n"
        "- Project Activities: Describe what actions are required by this protocol.\n"
        "- Geographical Applicability: Firstly state where the methodology is applied 'Global', 'U.S', 'U.S and Canada', 'Europe' or 'Asia'. Then provide extra details if necessary.\n"
        "- Additionality Requirements: Explain the criteria for additionality.\n"
        "- Crediting Period: Define the crediting period, if specified.\n"
        "- Project Longevity: Describe the expected duration of project activities.\n"
        "- Baseline Methodology: First state whether the methodology is 'Historical', 'Dynamic', or 'Both'. Then, provide a detailed explanation of how it works.\n"
        "- Protocol Type (Taxonomy): First state the taxonomy category based on the Oxford Protocols.\n\n"
        "### Project Summary\n"
        "### Project Activities\n"
        "### Geographical Applicability\n"
        "### Additionality Requirements\n"
        "### Crediting Period\n"
        "### Project Longevity\n"
        "### Baseline Methodology\n"
        "### Protocol Type (Taxonomy)\n\n"
        f"{text}"
    )

    data = {
        "model": "claude-instant",  # Assuming Claude has a model identifier, adjust accordingly
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt_text}
        ],
        "max_tokens": 800,  # Assuming similar parameter exists
        "temperature": 0.5  # Adjusted for a balance between creativity and relevance
    }

    response = requests.post(url, json=data, headers=headers)
    response_data = response.json()
    if 'error' in response_data:
        print("Failed to retrieve summary due to API error:", response_data['error']['message'])
        return None
    if 'choices' not in response_data or not response_data['choices']:
        print("No response available.")
        return None

    # Extract and return detailed responses from the model's output
    return response_data['choices'][0]['message']['content']

"""