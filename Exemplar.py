import time
import os
import random
import json

keywords = {
    "greeting": {"hi", "hello", "aloha", "howdy", "g'day", "'lo", "yo", "sup"},
    "negative": {"no", "not", "nothing", "nada", "sad", "angry", "upset", "frustrated"},
    "question": {"who", "what", "when", "where", "why", "how", "is", "are", "do", "does", "will", "can", "could", "would", "huh"},
    "nature": {"bear", "climb", "hiking", "outdoors", "fishing", "walking"},
    "affirmation": {"yes", "yeah", "yep", "sure", "okay", "alright", "fine", "agreed", "definitely", "good"},
    "gratitude": {"thanks", "thank", "appreciate", "grateful", "thankful", "cheers"},
    "identity": {"i", "me", "my", "mine", "you", "your", "yours", "we", "us", "they", "them"},
    "action": {"go", "going", "went", "walk", "run", "do", "doing", "did", "make", "making", "made", "build", "create"},
    "misc.": {},
}

conjunctions = ["for", "and", "nor", "but", "or", "yet","so"]

fillers = ["uhm", "uh", "uhmh", "um", "uhuh", "uhh", "umm", "umh"]

synonyms = {
    "greeting": {"good day", "g'day", "hello", "hi", "salutations"},
    "negative": {"sorry", "sorry you're feeling that way?", "tell me what happened?", "im sorry", "are you okay", "upset", "why are you frustrated"},
    "question": {"maybe?", "perhaps", "not sure", "okay"},
    "nature": {"cool", "nature is nice", "have fun!", "okay!", "nice"},
    "affirmation": {"yes okay", "okay", "sure!", "alrighty"},
    "gratitude": {"youre welcome", "no problem", "no biggie", "thats okay", "youre very welcome!"},
    "identity": {"you?", "me?", "you", "i", "you possibly"},
    "action": {"going where?", "went where?", "have fun!", "alright go ahead!"},
    "misc.": {},
    }
def load_data():
    global keywords, synonyms, fallbacks, unknown_words, conjunctions, fillers
    with open("words.json", "r") as f:
        data = json.load(f)

    keywords = {k: set(v) for k, v in data["keywords"].items()}
    synonyms = {k: set(v) for k, v in data["synonyms"].items()}
    fallbacks = data["fallbacks"]

if os.path.exists("words.json"):
    load_data()
    

fallbacks = ["what?", "what are you talking about", "not sure what you mean by that", "i might just be stupid but i dont know what you said"]

response_pts = []
unknown_words = []

def get_response(ipt):
    words = ipt.replace(".", "").replace("?", "").replace("!", "").replace("!", "").split()
    matched = False
    
    for i in words:
        matched = False
        for intent, i_set in keywords.items():
            if i in i_set:
                syn_list = list(synonyms.get(intent, {i}))
                response_pts.append(random.choice(syn_list))
                matched = True
                break
        if not matched:
            if not i in unknown_words:
                unknown_words.append(i)
                break
            if words in fillers or i in conjunctions:
                continue
            else:
                response_pts.append(i)
                
    response = " ".join(response_pts)
    if not response.endswith(("!", "?")):
        response += "."

    if not response_pts or response.strip() == "" or response.strip() in [".", "?", "!"] or response.strip() in unknown_words:
        response = random.choice(fallbacks)
        
    internal = [
        {"current intent": intent},
        {"notes": f"{response} {intent}"},
        {"new words": unknown_words},
    ]

    with open("status.json", "w") as f:
        json.dump(internal, f, indent=4)
    
    return response

while True:
    response_pts = []
    query = input("Ask anything (or enter 'q' to quit): ").strip().lower()
    if query == "q":
        if "misc." not in synonyms:
            synonyms["misc."] = set()
        if "misc." not in keywords:
            keywords["misc."] = set()

        synonyms["misc."].update(unknown_words)
        keywords["misc."].update(unknown_words)
        save_data = {
            "keywords": {k: list(v) for k, v in keywords.items()},
            "synonyms": {k: list(v) for k, v in synonyms.items()},
            "fallbacks": fallbacks,
        }

        with open("words.json", "w") as f:
            json.dump(save_data, f, indent=4)
        quit()
    else:
        print(get_response(query))
