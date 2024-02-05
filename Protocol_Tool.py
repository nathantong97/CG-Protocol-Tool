from datetime import datetime
import fitz  # PyMuPDF
import re


def extract_info_from_pdf(file_path):
    try:
        with fitz.open(file_path) as pdf_document:
            # Extract text from the first page
            first_page_text = pdf_document[0].get_text()

            # Extract text from the second and third pages for Table of Contents
            second_page_text = pdf_document[1].get_text() if len(pdf_document) > 1 else ""
            third_page_text = pdf_document[2].get_text() if len(pdf_document) > 2 else ""

            # Combine second and third page texts
            toc_text = second_page_text + third_page_text

            # Extract publishing standard body
            publishing_body = extract_publishing_standard_body(first_page_text)

            # Extract protocol name
            protocol_name = extract_protocol_name(first_page_text)

            # Extract protocol version
            protocol_version = extract_protocol_version(first_page_text)

            # Extract release date
            release_date = extract_release_date(first_page_text)

            # Extract protocol code
            protocol_code = extract_protocol_code(first_page_text)

            # Extract GHG Emission Type from the Table of Contents
            emission_type = extract_emissions_type(toc_text)

            # Extract additionality requirements (hardcoded for now)
            additionality_reqs = "The project must demonstrate that its activities result in greater GHG reductions or removals than what would naturally occur in a standard scenario, proving that these activities are a direct result of carbon market incentives. Key to this requirement is the concept of 'regulatory surplus,' which requires that the project activities are not required by any existing government policies or laws."

            # Extract monitoring project time (hardcoded for now)
            project_time = "Under the VCS Standard, projects are required to have a minimum project longevity of 40 years."

            return {
                "Publish Standard Body": publishing_body,
                "Protocol Name": protocol_name,
                "Protocol Version": protocol_version,
                "Release Date": release_date,
                "Protocol Code": protocol_code,
                "GHG Emission Type": emission_type,
                "Additionality Requirements": additionality_reqs,
                "Monitoring Project Time, Project Longevity": project_time,
            }

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

'''
def extract_protocol_name(text):
    lines = text.split('\n')
    for line in lines:
        if line.strip().startswith("Methodology"):
            return line.strip()
    return None
'''
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

if __name__ == "__main__":
    verra_pdf_document_path = 'C:/Users/User/OneDrive/Desktop/Local - Green Metric Technologies/Green Analytics/Carbon Guild/Protocol_Tool/Protocols/VM0025-Campus-Clean-Energy-and-Energy-Efficiency-v1.0.pdf'  #Replace with your document's path

    extracted_info = extract_info_from_pdf(verra_pdf_document_path)

    if extracted_info:
        print("Extracted Information:")
        for key, value in extracted_info.items():
            print(f"{key}: {value}")


#testing