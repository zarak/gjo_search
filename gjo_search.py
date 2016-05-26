import getpass
import pandas as pd
import requests
from bs4 import BeautifulSoup


LOGIN_URL = "https://www.gjopen.com/users/sign_in"
session = requests.session()

email = input("Enter email: ")
password = getpass.getpass("Enter password: ")


# Extract authenticity token from login page
def getToken(session):
    session.headers['User-Agent'] = 'Mozilla/5.0'
    result = session.get("http://www.gjopen.com/users/sign_in")
    login_soup = BeautifulSoup(result.text, "html.parser")
    return login_soup.find("input", {"name": "authenticity_token"})


# Returns prediction set as a dictionary
def getPrediction(item):
    preDict = {}
    pred_values = item.find("div", {"class": "prediction-values"})
    for k, v in zip(pred_values.findAll("div", {"class": "col-md-1"}), pred_values.findAll("div", {"class": "col-md-11"})):
        preDict[k.get_text().strip()] = v.get_text().strip()
    return preDict


while True:
    keyword = input("Enter keyword: ")
    SEARCH_URL = 'https://www.gjopen.com/search/query?term=' + keyword

    token_line = getToken(session)
    # User login information
    payload = {
        "user[email]": email,
        "user[password]": password,
        "authenticity_token": token_line['value']
    }

    result = session.post(LOGIN_URL, data=payload)
    result.raise_for_status()

    result = session.get(SEARCH_URL)
    result.raise_for_status()
    search_soup = BeautifulSoup(result.text, "html.parser")

    # Find all results for search term
    search_items = search_soup.findAll("div", {"class": "panel search-result comment-result"})
    columns = ['question', 'id', 'username', 'prediction-values', 'vote-count', 'date-localizable-timestamp', 'comment-content']
    # Create dataframe and populate with values
    df = pd.DataFrame(index=range(len(search_items)), columns=columns)
    for i, item in enumerate(search_items):
        df['question'][i] = item.find("a").text
        df['username'][i] = item.find("div", {"class": "prediction-set-info"}).span.text
        df['id'][i] = eval(item.find("a", {"class": "membership-link"})['data-membership-popover-data'])['id']
        df['prediction-values'][i] = getPrediction(item)
        df['comment-content'][i] = item.find("div", {"class": "flyover-comment-body"}).text.strip()
        df['vote-count'][i] = item.find("span", {"class": "vote-count"}).text
        df['date-localizable-timestamp'][i] = item.find("div", {"class": "flyover-comment-date"}).span.text

    print(df)
    filename = "gjo_search_for_" + keyword + ".csv"
    save_file_prompt = input("Save results to file? y/n ")
    if save_file_prompt.lower() == 'y':
        df.to_csv(filename)

    repeat_prompt = input("Search again? y/n ")
    if repeat_prompt.lower() == 'y':
        continue
    else:
        break
