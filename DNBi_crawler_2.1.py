import requests
import lxml.html
from bs4 import BeautifulSoup
import webbrowser
import pandas
import getpass
from difflib import get_close_matches

s = requests.session()  # Keep this global


"""Login to DNBi"""


def DNBi_login(username, password):
    login = s.get('https://sso.dnbi.com/cas/login')
    login_html = lxml.html.fromstring(login.text)
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
    form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
    form['username'] = username
    form['password'] = password
    response = s.post('https://sso.dnbi.com/cas/login', data=form)
    return(response.url)


def DSC_portfolio():
    homepage = s.get('https://na3.dnbi.com/dnbi/companies/showCompanyHome')  # Must keep this in order to get past Disclaimer page after login

    """Accesses the DSC portfolio companies page and prepares it for BeautifulSoup Parsing. Note: Customize DNBi website to show all companies by defualt"""
    My_Companies_Folder = s.get('https://na3.dnbi.com/dnbi/companies/showFolderEntities?folder_name=MyCompanies&folder_id=4E892B9ED7CB291FE0534A52450AA6A3&folder_type=SYSTEM&isSmart=false')
    My_Companies_Folder_Content_bs = BeautifulSoup(My_Companies_Folder.text, 'lxml')

    table = My_Companies_Folder_Content_bs.find('table', class_='results full_company')

    data = []
    # begining = https://na3.dnbi.com/ # Gonna need to this to navigate to the specific company page.
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            link = 'https://na3.dnbi.com' + (cols[1].find_all('a', {'class': 'navlinktable'})[0]['href'])  # Get Link from Table
            name = cols[2].find("b").text
            cols = [ele.text.strip() for ele in cols]
            cols.insert(0, link)
            cols.insert(1, name)
            cols[3] = cols[3][-11:]
            cols[4] = cols[4][len(name):]
        data.append([ele for ele in cols if ele])  # Get rid of empty values
    return(data[1:])


def company_name_DNBi(table):
    company_name_DNBi_dict = {}
    for row in table:
        company_name_DNBi_dict[row[1]] = row[2]
    return(company_name_DNBi_dict)


comp_name_for_csv = ""


def duns_getter(comp_duns):
    global comp_name_for_csv
    name = input("Enter Company name: ")
    name = name.upper()
    if name in comp_duns:
        comp_name_for_csv = str(get_close_matches(name, comp_duns.keys())[0])
        return(comp_duns[get_close_matches(name, comp_duns.keys())[0]])
    elif len(get_close_matches(name, comp_duns.keys())) > 0:
        yn = (input("Did you mean {} instead? Enter Y/N: ".format(get_close_matches(name, comp_duns.keys())[0]))).lower()
        # print("Did you mean {} instead? Enter Y/N".format(get_close_matches(w, data.keys())[0]))
        if yn == "y":
            comp_name_for_csv = str(get_close_matches(name, comp_duns.keys())[0])
            return(comp_duns[get_close_matches(name, comp_duns.keys())[0]])
        elif yn == "n":
            print("Please double check your spelling")
            duns_getter(comp_duns)
        else:
            print("We didn't understand your entry")
            duns_getter(comp_duns)
    else:
        print("Word cannot be found.")
        duns_getter(comp_duns)


def get_DNBi_profile_href(duns):
    for row in DSC_portfolio():
        if row[2] == duns:
            company_DNBi_profile_href = row[0]
            return(company_DNBi_profile_href)


def DNBi_profile_print_view_prep(company):
    Company_DNBi_Profile = s.get(company)
    # Company_DNBi_Profile_url = Company_DNBi_Profile.url ##Keep for trouble shooting
    Company_DNBi_Profile_bs = BeautifulSoup(Company_DNBi_Profile.text, 'lxml')

    DNBi_link = 'https://na3.dnbi.com/dnbi/companies' + (str(Company_DNBi_Profile_bs.find('li', class_='print_ecf')))[64:-105]
    Print_view = s.get(DNBi_link)
    Print_view_bs = BeautifulSoup(Print_view.text, 'lxml')
    # Print_view_bs_string = (Print_view_bs.text)
    # print(Print_view_bs_string) ##Keep for trouble shooting
    return(Print_view_bs)


def DNBi_profile_scrapper(DNBi_profile_print_view_bs):
    DNBi_profile_dict = {}
    DNBi_profile_dict["company_name"] = DNBi_profile_print_view_bs.find_all("td", {"class": "adminContent"})[0].text.strip()
    DNBi_profile_dict["company_trade_names"] = DNBi_profile_print_view_bs.find_all("td", {"class": "adminContent"})[1].text.strip()
    DNBi_profile_dict["company_address"] = DNBi_profile_print_view_bs.find("div", {"class": "DnBAddressAcc"}).find_all("td", {"valign": "top"})[1].text.strip()
    DNBi_profile_dict["paydex"] = DNBi_profile_print_view_bs.find("div", {"class": "barScorePos10"}).text.strip()
    DNBi_profile_dict["credit_limit"] = DNBi_profile_print_view_bs.find("p", {"style": "font-size:14px;font-weight:bold;width:auto;text-align:center;color:#006;margin:0;"}).text.strip()
    DNBi_profile_dict["CEO"] = DNBi_profile_print_view_bs.find_all("td", {"class": "adminContent"})[4].text.strip()
    DNBi_profile_dict["registration"] = DNBi_profile_print_view_bs.find_all("td", {"class": "adminContent"})[9].text.strip() + ', ' + Print_view_bs.find_all("td", {"class": "adminContent"})[10].text.strip()
    DNBi_profile_dict["Bankruptcy"] = DNBi_profile_print_view_bs.find_all("div", {"class": "widget_full"})[11].find_all("td", {"class": "rightAlign"})[0].text.strip()
    DNBi_profile_dict["Judgements"] = DNBi_profile_print_view_bs.find_all("div", {"class": "widget_full"})[11].find_all("td", {"class": "rightAlign"})[2].text.strip()
    DNBi_profile_dict["Liens"] = DNBi_profile_print_view_bs.find_all("div", {"class": "widget_full"})[11].find_all("td", {"class": "rightAlign"})[4].text.strip()
    DNBi_profile_dict["Suits"] = DNBi_profile_print_view_bs.find_all("div", {"class": "widget_full"})[11].find_all("td", {"class": "rightAlign"})[6].text.strip()
    DNBi_profile_dict["UCCs"] = DNBi_profile_print_view_bs.find_all("div", {"class": "widget_full"})[11].find_all("td", {"class": "rightAlign"})[8].text.strip()
    return(DNBi_profile_dict)


def csv_maker(DNBi_profile_dict):
    df = pandas.DataFrame(DNBi_profile_dict, index=[0])
    df.to_csv("{}_DNBi_profile.csv".format(comp_name_for_csv))


### HEAD ###
while True:
    username = input("DNBi username: ")
    password = getpass.getpass("DNBi password: ")
    DNBi_login(username, password)
    if DNBi_login(username, password)[-2:] == "20":
        print("Logging into DNBi website")
        break
    else:
        print("Incorrect username or password")


DSC_portfolio_dict = DSC_portfolio()

print("Creating portfolio of saved DNBi profiles...")

DSC_portfolio_comp_duns = company_name_DNBi(DSC_portfolio_dict)

company_duns = duns_getter(DSC_portfolio_comp_duns)

company_href = get_DNBi_profile_href(company_duns)

Print_view_bs = DNBi_profile_print_view_prep(company_href)

DNBi_profile_dict = DNBi_profile_scrapper(Print_view_bs)


csv_maker(DNBi_profile_dict)

print("Constructing csv file for {} DNBi profile...".format(comp_name_for_csv))

print("csv file saved.")


# while True:
#     csv_maker(DNBi_profile_dict)
#     print("Constructing csv file for {} DNBi profile...".format(comp_name_for_csv))
#     print("csv file saved.")
#     yn = input("Thank you sir may I have another? y/n").lower().strip()
#     if yn == "y":
#         continue
#     else:
#         break
