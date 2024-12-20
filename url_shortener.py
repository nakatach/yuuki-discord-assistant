import requests

def shorten_link(full_link):
    API_KEY = "86f454ac7109d94835f8c38493dc97c2cb7db"
    BASE_URL = "https://cutt.ly/api/api.php"

    payload = {"key": API_KEY, "short": full_link}
    request = requests.get(BASE_URL, params=payload)
    data = request.json()

    try:
        title = data["url"]["title"]
        short_link = data["url"]["shortLink"]
        return f"Title: {title}\nLink: {short_link}"
    except:
        status = data["url"]["status"]
        return f"Error Status: {status}"