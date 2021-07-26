from engines import searchobject
import requests

# Asks the Google API for an image, returns a GSO if found (None if not)
def searchimages(term, config): 
    if config['api']['api_key'] == "":
        print("The Google API key is not set.")
        return message("The Google API key is not set.")

    try:
        search_url = "https://www.googleapis.com/customsearch/v1?key={}&cx=016079215605992494498:z4taegakbcc&searchType=image&q={}".format(config['api']['api_key'],term.replace('-','+'))
        search_data = requests.get(search_url).json()
        if 'error' in search_data:
            raise KeyError("error!")
    except KeyError:
        print("Your API key has reached it's quota")
        return None
    
    search_error = 0
    while True:
        if search_error == 3:
            break

        try:
            search_result = search_data['items'][0 + int(search_error)]
        except KeyError:
            print("No image found!")
            return None

        try:
            search_url = search_result['link']
            break
        except:
            search_error += 1
            continue

    if search_error == 3:
        print("Search failed")
        return None
    else:
        gso = searchobject.genGSO(term, search_result['title'], search_result['image']['contextLink'], search_url)
        print('Google image result for ' + gso['term'].replace('-',' ') + ' found!')
        return gso