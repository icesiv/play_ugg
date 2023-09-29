RESOURCE_EXCLUSTIONS = ['image', 'stylesheet', 'media', 'font', 'other']

EXCEL_INPUT_FILE_PATH = 'excel_files/input.xlsx'
EXCEL_OUTPUT_FILE_PATH = 'excel_files/results.xlsx'

BASE_URL = "https://uggus.deckersb2b.deckers.com"


def get_url(key):

    if key == "login":
        return BASE_URL + "/#/login"

    elif key == "orderCenter":
        return "https://uggus.deckersb2b.deckers.com/order-center/#/orderCenter/home"

    else:
        return "Key Not Set"
