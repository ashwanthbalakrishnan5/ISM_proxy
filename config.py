import fuzzywuzzy

config = {
    "HOST_NAME": "localhost",
    "BIND_PORT": 8001,
    "MAX_REQUEST_LEN": 4096,
    "BLACKLIST_DOMAINS": ["google.com", "httpforever.com"],
    "HOST_ALLOWED": ["*"],
    "ALLOWED_METHODS": ["GET", "POST", "CONNECT", "HEAD", "PUT", "DELETE", "OPTIONS"],
    "COLORED_LOGGING": True,
    "BLACKLIST_WORDS": [
        "movies",
        "games",
    ],
    "FUZZY_SCORER": fuzzywuzzy.fuzz.ratio,
    "FUZZY_THRESHOLD": 80,
}

"""
HTTP Sites
    
* http://www.china.com.cn/
* http://httpforever.com/
* https://info.cern.ch/
* http://neverssl.com/

"""
