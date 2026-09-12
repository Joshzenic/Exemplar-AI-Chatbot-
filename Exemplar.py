import time
import os
import random
import json
import traceback
import requests

keywords = {
    "greeting": {"hi", "hello", "aloha", "howdy", "gday", "g'day", "lo", "'lo", "yo", "sup"},
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

fallbacks = ["what?", "what are you talking about", "not sure what you mean by that", "i might just be stupid but i dont know what you said"]

response_pts = []
unknown_words = []
misc_words = {}
deleted_words = []
timer = 0
savetimer = 0
disable_userIn = False

LOG_FOLDER = "log"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)


session_name = input("Give current session a name (leave blank for an auto gen): ").strip().replace(" ", "_")
if session_name == "":
    session_name = time.strftime('%Y-%m-%d_%H-%M-%S')
selftrain = input("Self train Exemplar Chatbot? (y/n) ").strip().lower()
if selftrain == "y" or selftrain == "yes":
    disable_userIn = True
print(f"Chat name is now: {session_name}\n")
time.sleep(3)
os.system('cls' if os.name == 'nt' else 'clear')
log_filename = f"{LOG_FOLDER}/chat_{session_name}.txt"
with open(log_filename, "w") as f:
    f.write(f"--- Session started by user at {time.strftime('%H:%M:%S')}---\n")

def self_train():
    headers = {
        "User-Agent": "ExemplarSelfTrain/1.0 (personal project; contact: none)"
    }

    req = requests.get("https://en.wikipedia.org/api/rest_v1/page/random/summary", headers=headers)
    print(f"Status code: {req.status_code}")
    print(f"First 200 chars: {req.text[:200]}")
    if req.status_code == 200:
        data = req.json()
        text = data["extract"]
        print(f"Title: {data['title']}")
        print(f"Text: {text[:100]}...")
    else:
        text = f"{random.choice(list(synonyms['greeting']))} {random.choice(list(synonyms['action']))} {random.choice(list(synonyms['negative']))}"
        print("Request failed.")
        
    content = text.strip().lower().split()
    usr_in = []
    runtimer = 0
    
    while runtimer < 5:
        usr_in.append(random.choice(content))
        runtimer += 1
    
    query = " ".join(usr_in)


    return query

def delete_word(word):
    global deleted_words
    with open(log_filename, "a") as log_file:
        log_file.write(f"[{time.strftime('%H:%M:%S')}] Cleared: {word}\n")
    deleted_words.append(word)
    keywords["misc."].discard(word)
    synonyms["misc."].discard(word)
    if word in misc_words:
        del misc_words[word]
    
def promote_word(word):
    for intent, word_set in keywords.items():
        if word in word_set:
            return
    guessed_intent = None

    if len(word) <= 3 and word not in conjunctions:
        guessed_intent = "identity"
    elif word.endswith("ing") or word.endswith("ed"):
        guessed_intent = "action"
    elif word.endswith("ly") and len(word) > 4:
        guessed_intent = "negative"
    elif len(word) < 6 and any(char in word for char in ["y", "u", "o"]):
        guessed_intent = "affirmation"
        
    if guessed_intent:
        with open(log_filename, "a") as log_file:
            log_file.write(f"[{time.strftime('%H:%M:%S')}] Promoted: {word} -> {guessed_intent}\n")
        keywords[guessed_intent].add(word)
        synonyms[guessed_intent].add(word)
        keywords["misc."].discard(word)
        synonyms["misc."].discard(word)
        misc_words["misc."].discard(word)
    else:
        keywords["misc."].add(word)
        synonyms["misc."].add(word)


def load_data():
    global keywords, synonyms, fallbacks, unknown_words, conjunctions, fillers, misc_words
    with open(f"{LOG_FOLDER}/words.json", "r") as f:
        data = json.load(f)

    keywords = {k: set(v) for k, v in data["keywords"].items()}
    synonyms = {k: set(v) for k, v in data["synonyms"].items()}
    fallbacks = data["fallbacks"]
    misc_words = data.get("misc_words", {})

if os.path.exists(f"{LOG_FOLDER}/words.json"):
    load_data()

def get_response(ipt):
    global response_pts, timer, deleted_words
    parts = ipt.replace(".", "").replace("?", "").replace("!", "").replace("!", "").split(",")
    matched = False
    det_intent = None
    
    try:
        for part in parts:
            words = part.strip().split()
            for i in words:
                matched = False
                for intent, i_set in keywords.items():
                    if i in i_set:
                        syn_list = list(synonyms.get(intent, {i}))
                        response_pts.append(random.choice(syn_list))
                        det_intent = intent
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
                else:
                    if i in misc_words:
                        misc_words[i]["uses"] += 1
                    else:
                        misc_words[i] = {"uses": 1}
                        
            response = " ".join(response_pts)
            if not response.endswith(("!", "?")):
                if det_intent == "question" or det_intent == "negative" or det_intent == "action":
                    response += "?"
                elif len(parts) > 1 and part != parts[1]:
                    response += "."
                    
        if timer > 5 and len(synonyms["misc."]) > 10:
            timer = 0
            for word in list(synonyms["misc."]):
                if word in misc_words and "uses" in misc_words[word]:
                    if misc_words[word]["uses"] < 3:
                        delete_word(word)
                    elif misc_words[word]["uses"] >= 5:
                        promote_word(word)
                else:
                    delete_word(word)
        else:
            timer += 1
                
                
        if not response.endswith(("!", "?", ".", ",")):
            response += "."

        if not response_pts or response.strip() == "" or response.strip() in [".", "?", "!"] or response.strip() in unknown_words:
            response = random.choice(fallbacks)
        
        internal = [
            {"current intent": det_intent},
            {"notes": f"{response} {det_intent}"},
            {"new words": unknown_words},
            {"time to next wipe": timer},
            {"forgotten words": deleted_words},
            {"word usage track": misc_words},
        ]

        with open(f"{LOG_FOLDER}/status.json", "w") as f:
            json.dump(internal, f, indent=4)

    except Exception as e:
        print(f"Exemplar ran into a problem while formatting response.\nDebug: {e}")
        geterror = input("See extra (y/n) ").strip().lower()
        if geterror == "y" or geterror == "yes":
            print(f"Line: {traceback.format_exc()}")
        print("")
        response = random.choice(fallbacks)
    
    return response

print(f"Chat name:\n{session_name}")
        
while True:
    response_pts = []
    if disable_userIn:
        time.sleep(3)
        query = self_train()
        savetimer += 1
        if savetimer > 20:
            query = "qs"
    else:
        query = input("Ask anything (or 'q' to quit): ").strip().lower()
    if query == "q" or query == "qs":
        with open(log_filename, "a") as log_file:
            log_file.write(f"\n--- Session ended by user at {time.strftime('%H:%M:%S')} ---\n")
            
        if "misc." not in synonyms:
            synonyms["misc."] = set()
        elif not isinstance(synonyms["misc."], set):
            synonyms["misc."] = set(synonyms["misc."])
        if "misc." not in keywords:
            keywords["misc."] = set()
        elif not isinstance(keywords["misc."], set):
            keywords["misc."] = set(keywords["misc."])

        synonyms["misc."].update(unknown_words)
        keywords["misc."].update(unknown_words)
        save_data = {
            "keywords": {k: list(v) for k, v in keywords.items()},
            "synonyms": {k: list(v) for k, v in synonyms.items()},
            "fallbacks": fallbacks,
            "misc_words": misc_words,
        }

        with open(f"{LOG_FOLDER}/words.json", "w") as f:
            json.dump(save_data, f, indent=4)
        if query == "qs":
            query = ""
            savetimer = 0
        else:
            quit()
    else:
        print("")
        bot_response = get_response(query)
        print(f"Exemplar: {bot_response}")
        print("")
        with open(log_filename, "a") as log_file:
            log_file.write(f"[{time.strftime('%H:%M:%S')}] User: {query}\n")
            log_file.write(f"[{time.strftime('%H:%M:%S')}] Exemplar: {bot_response}\n\n")
