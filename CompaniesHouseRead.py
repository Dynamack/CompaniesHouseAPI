"""
This application allows us to fetch company names from Companies House API by inputting company numbers.
Requires a company house API key in 'comp_house_api_key.py'.
"""

from CompaniesHouseService import CompaniesHouseService
from comp_house_api_key import api_key
import pandas as pd
import tkinter as tk
from tkinter import filedialog

# Flags for fetching supplemental data
getOfficers = False
getCharges = False
getInsolvency = True


print("Hello! \nThis program allows you to input a CSV/Excel file with Companies House company numbers and returns a file with the corresponding company names.\
\nSelect a file once with file explorer window opens. Please ensure the file has a column titled 'Company Number'.")
 
root = tk.Tk()
root.withdraw()
companyIDs = filedialog.askopenfilename()  

print("\nFile selected: " + companyIDs)                                         

# condition for when input file is .csv
if companyIDs[(len(companyIDs) - 4) : (len(companyIDs))] == ".csv": 
    df = pd.read_csv(companyIDs, skiprows = 0, dtype = {'Company Number': str, 'Company Name': str})

# condition for when input file is .xlsx
elif companyIDs[(len(companyIDs) - 5) : (len(companyIDs))] == ".xlsx": 
    df = pd.read_excel(companyIDs, skiprows = 0, dtype = {'Company Number': str, 'Company Name': str})

df.index.name = 'Index'

companyHouseAPI = CompaniesHouseService(api_key)

print('\nFetching company information...')


# get company name from CH API
for index, row in df.iterrows():
    # for tracking progress
    percentage_complete = int(((index+1) * 100)/len(df.index))

    company_number = str(row["Company Number"])

    if company_number == "nan":
        print("\n" + str(index+1) + "/" + str(len(df.index)) + " (" + str(percentage_complete) + "%): [No Result]")
        continue

    company_profile = companyHouseAPI.get_company_profile(company_number)

    if company_profile == {}:
        df.at[index, "Company Name"] = "[No Result]"
        df.at[index, "Jurisdiction"] = "[No Result]"
        df.at[index, "Type"] = "[No Result]"
        df.at[index, "Registered Office Address"] = "[No Result]"
        print("\n" + str(index+1) + "/" + str(len(df.index)) + " (" + str(percentage_complete) + "%): " + company_number + " | [No Result]")
        continue

    else:
        df.at[index, "Company Name"] = str(company_profile['company_name'])
        df.at[index, "Jurisdiction"] = str(company_profile['jurisdiction']).title()
        df.at[index, "Type"] = str(company_profile['type']).upper()

        # The below chunk of code fetches address
        df.at[index, "Registered Office Address"] = ""
        
        if 'address_line_1' in company_profile['registered_office_address']:
            df.at[index, "Registered Office Address"] += str(company_profile['registered_office_address']['address_line_1'])
        if 'address_line_2' in company_profile['registered_office_address']:
           df.at[index, "Registered Office Address"] += ", " + str(company_profile['registered_office_address']['address_line_2'])
        if 'locality' in company_profile['registered_office_address']:
           df.at[index, "Registered Office Address"] += ", " + str(company_profile['registered_office_address']['locality'])
        if 'region' in company_profile['registered_office_address']:
           df.at[index, "Registered Office Address"] += ", " + str(company_profile['registered_office_address']['region'])
        if 'postal_code' in company_profile['registered_office_address']:
           df.at[index, "Registered Office Address"] += ", " + str(company_profile['registered_office_address']['postal_code'])
        if 'country' in company_profile['registered_office_address']:
           df.at[index, "Registered Office Address"] += ", " + str(company_profile['registered_office_address']['country'])


    # get officer information
    if getOfficers == True:
        if ('officers' not in company_profile['links']):
            df.at[index, "Directors"] = "[No Directors]"
            print("\n" + str(index+1) + "/" + str(len(df.index)) + " (" + str(percentage_complete) + "%): " + company_number + " | " + str(company_profile['company_name']))
            continue

        else:
            officers_path = str(company_profile['links']['officers'])
    
            directors = companyHouseAPI.get_company_directors(officers_path)

            director_index = 0
            directors_string = ""

            # Create a long string full of the directors names
            while director_index < len(directors):
                directors_string += directors[director_index] + " | "
                director_index = director_index + 1

            df.at[index, "Directors"] = directors_string

            print("Company Number: " + df.at[index, 'Company Number'] + " | Company Name: " + df.at[index, 'Company Name'])


    # get charge information
    if getCharges == True:
        if ('charges' not in company_profile['links']):
            df.at[index, "Charges"] = "[No Charges]"
            print("\n" + str(index+1) + "/" + str(len(df.index)) + " (" + str(percentage_complete) + "%): " + company_number + " | " + str(company_profile['company_name']))
            continue

        else:
            charges_path = str(company_profile['links']['charges'])

            charges = companyHouseAPI.get_company_charges(charges_path)

            # empty string which we will append all charges to
            charges_string = "" 

            chargeIndex = 1
            fieldIndex = 0

            # the below chunk of code iterates over each field in each charge and appends to string
            while (chargeIndex < len(charges) + 1):
                charges_string += str(chargeIndex) + ":\n"
                while (fieldIndex < len(charges[0])):
                    charges_string += str(charges[chargeIndex-1][fieldIndex]) + "\n"
                    fieldIndex += 1
                
                chargeIndex += 1
                fieldIndex = 0
                charges_string += "\n"
        
            charges_string = charges_string.strip()

            df.at[index, "Charges"] = charges_string


    if getInsolvency == True:
        if ('involvency' not in company_profile['links']):
            df.at[index, "Insolvency"] = "[No Insolvency Data]"
            print("\n" + str(index+1) + "/" + str(len(df.index)) + " (" + str(percentage_complete) + "%): " + company_number + " | " + str(company_profile['company_name']))
            continue 

        else:
            hasInsolvencyHistory = company_profile['has_insolvency_history']
            print("has insolvency history: " + hasInsolvencyHistory)
            

    print("\n" + str(index+1) + "/" + str(len(df.index)) + " (" + str(percentage_complete) + "%): " + company_number + " | " + str(company_profile['company_name']))


# Select save location for output file
print("\nSelect location to save output file.\
\nPlease take note that when opening .csv files, excel will truncate leading zeros from 'Company Number', \
hence .xlsx is the optimal file format. \nHowever if you still desire to save as .csv, applications like Notepad, Notepad++ etc. can still view the data with no issue.")


saveLocation = filedialog.asksaveasfilename()

# condition for saving as .csv
if saveLocation[(len(saveLocation) - 4) : (len(saveLocation))] == ".csv":             
    df.to_csv(saveLocation)

# condition for saving as .xlsx
elif saveLocation[(len(saveLocation) - 5) : (len(saveLocation))] == ".xlsx":
    df.to_excel(saveLocation)                                                   