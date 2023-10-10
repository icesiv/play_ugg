# RESOURCE_EXCLUSTIONS = ['image', 'stylesheet', 'media', 'font', 'other']
RESOURCE_EXCLUSTIONS = ['image', 'media', 'font']

EXCEL_INPUT_FILE_PATH = 'excel_files/input.xlsx'
EXCEL_OUTPUT_FILE_PATH = 'excel_files/logs/'

BASE_URL = "https://uggus.deckersb2b.deckers.com"

CONFIG_PATH = '../config.json'


def get_url(key):

    if key == "login":
        return BASE_URL + "/#/login"

    elif key == "search":
        return BASE_URL + "/order-center/#/orderCenter/productList?method=SEARCH&search="

    elif key == "cart":
        return BASE_URL + "/order-center/#/orderCenter/shoppingCar"
    else:
        return "Key Not Set"
