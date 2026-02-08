"""
Keyword definitions for all housing society categories.
Includes English, Hindi/Hinglish keywords, and common typos/misspellings.
"""

# Category definitions with keywords for detection
# Format: category_name -> {offer_keywords, query_keywords, subcategory_keywords, emoji}

CATEGORIES = {
    "property": {
        "emoji": "🏠",
        "offer_keywords": [
            # English
            "selling flat", "flat for sale", "house for sale", "apartment for sale",
            "for rent", "on rent", "available for rent", "flat available",
            "bhk available", "rk available", "pg available",
            "selling my", "want to sell", "selling 1bhk", "selling 2bhk", "selling 3bhk",
            "apartment available", "house available", "room available",
            "property for sale", "flat on sale", "home for sale",
            # Typos
            "seling flat", "sellin flat", "flaat for sale", "appartment",
            "avalable for rent", "availble", "avialable", "availabel",
            # Hindi
            "flat bechna", "ghar bechna", "kiraye par", "rent pe", "bechna hai",
            "flat khali", "kamra khali", "available hai", "bech raha", "bech rahi",
            "makan bechna", "ghar bechna hai", "flat bech raha",
            # Hindi typos
            "flate bechna", "bechana hai", "bechhna", "kiraya par"
        ],
        "query_keywords": [
            # English
            "looking for flat", "need flat", "want to buy", "want flat",
            "looking for house", "need house", "want to rent", "need on rent",
            "anyone selling flat", "any flat available", "looking for bhk",
            "looking for 1bhk", "looking for 2bhk", "looking for 3bhk",
            "need 1bhk", "need 2bhk", "need 3bhk", "want 1bhk", "want 2bhk", "want 3bhk",
            "searching for flat", "require flat", "flat required", "house required",
            "need apartment", "looking for apartment", "want apartment",
            "need room", "looking for room", "want room", "room required",
            "any 1bhk", "any 2bhk", "any 3bhk", "koi bhi flat",
            # Typos
            "lokking for", "loking for", "lookng for", "serching", "searcing",
            "nedd flat", "ned flat", "requried", "requred", "requird",
            # Hindi
            "flat chahiye", "ghar chahiye", "room chahiye", "kamra chahiye",
            "kiraye pe chahiye", "rent pe chahiye", "koi flat", "koi ghar",
            "1bhk chahiye", "2bhk chahiye", "3bhk chahiye",
            "flat lena", "ghar lena", "kamra lena", "makan chahiye",
            # Hindi typos
            "chhaiye", "chaheye", "chahye", "chayie", "cahiye", "chaihye"
        ],
        "subcategory_patterns": [
            r"(\d)\s*bhk", r"(\d)\s*rk", r"studio", r"penthouse", r"duplex",
            r"1\s*bed", r"2\s*bed", r"3\s*bed", r"flat", r"apartment"
        ]
    },
    
    "furniture": {
        "emoji": "🪑",
        "offer_keywords": [
            # English
            "selling sofa", "old sofa", "used sofa", "sofa for sale",
            "selling table", "old table", "used table", "table for sale",
            "selling bed", "old bed", "used bed", "bed for sale",
            "selling fridge", "old fridge", "used fridge", "fridge for sale",
            "selling washing machine", "old washing machine", "used ac",
            "furniture for sale", "selling furniture", "used furniture",
            "selling chair", "old chair", "selling almirah", "selling wardrobe",
            "selling tv", "old tv", "used tv", "tv for sale",
            "selling mattress", "old mattress", "used mattress",
            "selling dining table", "dining set for sale",
            # Typos
            "seling sofa", "sofaa", "tabel", "freidge", "frige", "fridg",
            "furnture", "furnitre", "washng machine", "almira", "almaira",
            # Hindi
            "sofa bechna", "table bechna", "bed bechna", "fridge bechna",
            "purana sofa", "purana table", "purana bed", "furniture bechna",
            "kursi bechna", "gadda bechna", "tv bechna", "almari bechna"
        ],
        "query_keywords": [
            # English
            "need sofa", "looking for sofa", "want sofa", "anyone selling sofa",
            "need table", "looking for table", "want table", "anyone selling table",
            "need bed", "looking for bed", "want bed", "anyone selling bed",
            "need fridge", "looking for fridge", "want fridge",
            "need furniture", "looking for furniture", "used furniture",
            "need chair", "need almirah", "need wardrobe", "need tv",
            "need mattress", "looking for mattress", "need dining table",
            "anyone has sofa", "anyone has table", "anyone has fridge",
            # Typos
            "nedd sofa", "lokking for table", "freidge chahiye",
            # Hindi
            "sofa chahiye", "table chahiye", "bed chahiye", "fridge chahiye",
            "furniture chahiye", "koi sofa", "koi table", "koi bed",
            "kursi chahiye", "gadda chahiye", "tv chahiye", "almari chahiye",
            "purana furniture", "second hand furniture"
        ],
        "subcategory_patterns": [
            r"sofa", r"table", r"bed", r"fridge", r"refrigerator", r"washing machine",
            r"ac", r"air conditioner", r"chair", r"wardrobe", r"almirah", r"cupboard",
            r"tv", r"television", r"mattress", r"gadda", r"dining", r"almari", r"almira"
        ]
    },
    
    "maid": {
        "emoji": "🧹",
        "offer_keywords": [
            # English
            "maid available", "domestic help available", "helper available",
            "cook available", "nanny available", "babysitter available",
            "housekeeper available", "cleaning lady", "bai available",
            "house help available", "helper contact", "maid contact",
            "part time maid", "full time maid", "good maid",
            # Typos
            "maide available", "maid availble", "coook available", "avialable",
            # Hindi
            "maid mil jayegi", "kaam wali available", "bai available",
            "cook mil jayegi", "kaamwali available", "jhaadu pochha",
            "kaam wali milegi", "bai milegi", "aaya available",
            # Hindi typos
            "kaamvali", "kamwali", "bhai available"
        ],
        "query_keywords": [
            # English
            "need maid", "looking for maid", "maid required", "want maid",
            "need cook", "looking for cook", "cook required", "want cook",
            "need nanny", "looking for nanny", "babysitter required",
            "need domestic help", "helper required", "need bai",
            "need house help", "need cleaning lady", "maid wanted",
            "part time maid needed", "full time maid needed",
            "looking for a maid", "looking for a cook", "looking for a nanny",
            "anyone has maid", "any maid available", "maid contact please",
            # Typos
            "nedd maid", "maide required", "coock chahiye", "maid requried",
            "lokking for maid", "miad wanted", "made required",
            # Hindi
            "maid chahiye", "kaam wali chahiye", "bai chahiye", "cook chahiye",
            "nanny chahiye", "kaamwali chahiye", "jhaadu pochha chahiye",
            "koi maid", "koi cook", "koi bai", "maid hai kya", "koi maid hai",
            "kaamwali hai kya", "cook hai kya", "aaya chahiye",
            # Hindi typos
            "chhaiye", "chaheye", "chahye", "kaamvali chahiye", "kamwali chahiye"
        ],
        "subcategory_patterns": [
            r"maid", r"cook", r"nanny", r"babysitter", r"helper", r"bai",
            r"kaamwali", r"kaam wali", r"housekeeper", r"aaya", r"kamwali"
        ]
    },
    
    "plumber": {
        "emoji": "🔧",
        "offer_keywords": [
            # English
            "plumber available", "plumbing service", "plumbing work",
            "plumber contact", "plumber number", "plumber here",
            "i am plumber", "plumbing done", "plumber ka kaam",
            # Typos
            "plumer available", "plumbar", "plomber", "plamber",
            # Hindi
            "plumber milega", "plumber available hai", "plumbing ka kaam",
            "nalwala", "paani wala mistri"
        ],
        "query_keywords": [
            # English
            "need plumber", "plumber required", "looking for plumber",
            "tap leaking", "pipe leaking", "bathroom issue", "toilet issue",
            "water problem", "drainage problem", "plumbing issue",
            "tap issue", "pipe issue", "bathroom leak", "toilet leak",
            "water leak", "drainage issue", "blocked drain", "clogged",
            "tank leaking", "geyser issue", "geyser problem",
            "please share plumber", "any plumber", "plumber contact please",
            # Typos
            "plumer required", "plumbar chahiye", "plomber needed",
            "leking", "leeking", "leakng", "problm", "isue",
            # Hindi
            "plumber chahiye", "plumber bhejo", "nal se paani", "pipe leak",
            "toilet kharab", "bathroom mein problem", "paani ka issue",
            "nalkoop", "boring", "koi plumber", "nal kharab", "paani tapak",
            "tank se paani", "geyser kharab",
            # Hindi typos
            "plumber chaiye", "plumbar chaiye"
        ],
        "subcategory_patterns": [
            r"tap", r"pipe", r"toilet", r"bathroom", r"drainage", r"leak",
            r"geyser", r"tank", r"nal", r"drain", r"clog"
        ]
    },
    
    "electrician": {
        "emoji": "💡",
        "offer_keywords": [
            # English
            "electrician available", "electrical work", "electrical service",
            "electrician contact", "electrician number", "wiring work",
            "i am electrician", "electrical repairs",
            # Typos
            "electritian", "electrican", "electrision", "electician",
            # Hindi
            "electrician milega", "bijli ka kaam", "wiring available",
            "bijli wala", "bijli mistri"
        ],
        "query_keywords": [
            # English
            "need electrician", "electrician required", "looking for electrician",
            "fan not working", "light not working", "switch problem",
            "wiring issue", "electrical problem", "power issue", "mcb tripping",
            "inverter problem", "ups problem", "socket issue", "plug issue",
            "short circuit", "fuse problem", "ac not working electrician",
            "please share electrician", "any electrician", "electrician contact",
            # Typos
            "electritian chahiye", "electician needed", "electrican required",
            "fan not workng", "lite not working", "probem", "isssue",
            # Hindi
            "electrician chahiye", "bijli ka kaam", "fan kharab",
            "light kharab", "switch kharab", "wiring problem",
            "bijli nahi", "current nahi", "koi electrician",
            "inverter kharab", "mcb trip", "socket kharab", "plug kharab",
            # Hindi typos
            "electrician chaiye", "bijlee", "bigli"
        ],
        "subcategory_patterns": [
            r"fan", r"light", r"switch", r"wiring", r"mcb", r"inverter",
            r"socket", r"plug", r"fuse", r"ac", r"ups"
        ]
    },
    
    "carpenter": {
        "emoji": "🪚",
        "offer_keywords": [
            # English
            "carpenter available", "carpentry work", "furniture repair",
            "wood work", "carpenter contact", "woodwork done",
            "i am carpenter", "carpentry service",
            # Typos
            "carpanter", "carpentar", "carpnter", "carpeter",
            # Hindi
            "carpenter milega", "mistri available", "lakdi ka kaam",
            "badhai available", "badhai milega"
        ],
        "query_keywords": [
            # English
            "need carpenter", "carpenter required", "looking for carpenter",
            "furniture repair", "door repair", "wood work needed",
            "cabinet repair", "wardrobe repair", "fixing furniture",
            "door problem", "drawer broken", "cupboard repair",
            "any carpenter", "carpenter contact please",
            # Typos
            "carpanter needed", "carpnter chahiye", "furnitur repair",
            # Hindi
            "carpenter chahiye", "mistri chahiye", "lakdi ka kaam",
            "furniture repair", "door kharab", "koi carpenter", "koi mistri",
            "badhai chahiye", "darwaza kharab", "almari repair",
            # Hindi typos
            "mistree", "mistari"
        ],
        "subcategory_patterns": [
            r"door", r"cabinet", r"wardrobe", r"furniture", r"wood",
            r"drawer", r"cupboard", r"almari", r"darwaza"
        ]
    },
    
    "driver": {
        "emoji": "🚗",
        "offer_keywords": [
            # English
            "driver available", "can drive", "driving service",
            "driver for hire", "driver contact", "i can drive",
            "experienced driver", "part time driver available",
            # Typos
            "diver available", "drivar", "drivr",
            # Hindi
            "driver milega", "driver available hai", "gaadi chala sakta",
            "driver hun", "gaadi chalata hun"
        ],
        "query_keywords": [
            # English
            "need driver", "driver required", "looking for driver",
            "driver wanted", "part time driver", "full time driver",
            "any driver", "driver contact please", "personal driver needed",
            # Typos
            "diver needed", "drivar chahiye", "drivr required",
            # Hindi
            "driver chahiye", "gaadi chalane wala", "koi driver",
            "driver bhejo", "driver ka number", "driver mile kya",
            # Hindi typos
            "drivar chaiye"
        ],
        "subcategory_patterns": [
            r"driver", r"full time", r"part time", r"personal"
        ]
    },
    
    "ac_repair": {
        "emoji": "❄️",
        "offer_keywords": [
            # English
            "ac repair", "ac service", "ac installation",
            "fridge repair", "washing machine repair", "appliance repair",
            "ac technician", "ac mechanic", "ac gas filling available",
            "i repair ac", "fridge technician",
            # Typos
            "ac repiar", "ac servise", "ac servic", "friddge repair",
            # Hindi
            "ac repair available", "ac ka kaam", "fridge repair available",
            "ac wala", "fridge wala"
        ],
        "query_keywords": [
            # English
            "ac not working", "ac repair needed", "need ac service",
            "fridge not working", "fridge repair", "washing machine repair",
            "ac not cooling", "ac gas filling", "ac installation",
            "ac leaking", "ac noise", "fridge not cooling",
            "washing machine not working", "microwave repair", "geyser repair",
            "any ac technician", "ac mechanic needed",
            # Typos
            "ac not workng", "ac not coolig", "ac repiar needed",
            "fridg repair", "washng machine", "geaser repair",
            # Hindi
            "ac kharab", "ac repair chahiye", "ac thanda nahi",
            "fridge kharab", "washing machine kharab", "koi ac wala",
            "ac se paani", "fridge thanda nahi", "geyser kharab",
            # Hindi typos
            "ac chaiye", "ac chahye"
        ],
        "subcategory_patterns": [
            r"ac", r"air conditioner", r"fridge", r"refrigerator", 
            r"washing machine", r"microwave", r"geyser", r"cooler"
        ]
    },
    
    "tutor": {
        "emoji": "📚",
        "offer_keywords": [
            # English
            "tutor available", "home tuition", "teaching available",
            "can teach", "tuition classes", "coaching available",
            "i teach", "private tutor", "tutoring available",
            "online tuition", "home teaching",
            # Typos
            "tuter available", "tution classes", "tutor availble",
            # Hindi
            "tuition available", "padha sakta", "teacher available",
            "padhata hun", "padhati hun"
        ],
        "query_keywords": [
            # English
            "need tutor", "tutor required", "looking for tutor",
            "home tuition", "tuition for class", "need teacher",
            "maths tutor", "science tutor", "english tutor",
            "physics tutor", "chemistry tutor", "hindi tutor",
            "tutor for class", "any tutor", "tutor contact",
            "coaching needed", "private tutor needed",
            # Typos
            "tuter required", "tution chahiye", "tuter needed",
            "maths tuter", "scince tutor", "chemisty tutor",
            "looking for tuter", "tuter for class", "need tuter",
            # Hindi
            "tutor chahiye", "teacher chahiye", "tuition chahiye",
            "padhane wala", "koi tutor", "koi teacher",
            "coaching chahiye", "sir chahiye", "madam chahiye",
            # Hindi typos
            "tushan chahiye", "tution chaiye"
        ],
        "subcategory_patterns": [
            r"class\s*\d+", r"maths", r"math", r"science", r"english", r"hindi",
            r"physics", r"chemistry", r"cbse", r"icse", r"ssc", r"hsc"
        ]
    },
    
    "packers_movers": {
        "emoji": "📦",
        "offer_keywords": [
            # English
            "packers available", "movers available", "shifting service",
            "relocation service", "transport available",
            "packing service", "moving service", "we do shifting",
            # Typos
            "packers avalable", "movers availble", "shifting servise",
            # Hindi
            "packers movers available", "shifting ka kaam", "saman le jayenge",
            "shifting karwate hain"
        ],
        "query_keywords": [
            # English
            "need packers", "packers required", "looking for movers",
            "shifting help", "house shifting", "relocation help",
            "need transport", "goods transport", "moving help",
            "any packers", "packers contact", "movers contact",
            "local shifting", "outstation shifting",
            # Typos
            "packers requried", "shipting help", "relocaton help",
            # Hindi
            "packers chahiye", "movers chahiye", "shifting chahiye",
            "saman shift karna", "ghar badalna", "koi packers",
            "shifting karna hai", "ghar shift", "saman le jana",
            # Hindi typos
            "shipting chahiye", "packar chahiye"
        ],
        "subcategory_patterns": [
            r"local", r"outstation", r"interstate", r"city", r"shifting"
        ]
    },
    
    "vehicle": {
        "emoji": "🚙",
        "offer_keywords": [
            # English
            "selling car", "car for sale", "bike for sale", "selling bike",
            "scooter for sale", "vehicle for sale", "used car", "used bike",
            "selling activa", "selling scooty", "activa for sale", "scooty for sale",
            "want sell", "want to sell my", "two wheeler", "selling two wheeler",
            "selling my car", "selling my bike", "car available",
            "bike available", "second hand car", "second hand bike",
            # Typos
            "seling car", "sellin bike", "car for sel", "bik for sale",
            "actva for sale", "scooti", "scoty",
            # Hindi
            "car bechna", "bike bechna", "gaadi bechna", "scooty bechna",
            "activa bechna", "bechna hai car", "bechna hai bike",
            "gaadi bech raha", "bike bech rahi"
        ],
        "query_keywords": [
            # English
            "looking for car", "need car", "want to buy car",
            "looking for bike", "need bike", "want to buy bike",
            "used car", "second hand car", "used bike",
            "looking for activa", "looking for scooty", "need activa", "need scooty",
            "want activa", "want scooty", "looking for two wheeler",
            "any car available", "any bike available", "car contact",
            "second hand vehicle", "old car", "old bike",
            # Typos
            "lokking for car", "nedd bike", "secnd hand", "old bik",
            # Hindi
            "car chahiye", "bike chahiye", "gaadi chahiye",
            "koi car", "koi bike", "purani car", "purani bike",
            "activa chahiye", "scooty chahiye", "gaadi leni hai",
            "bike leni hai", "second hand gaadi",
            # Hindi typos
            "car chaiye", "gaadhi chahiye"
        ],
        "subcategory_patterns": [
            r"car", r"bike", r"scooter", r"scooty", r"activa", r"two wheeler",
            r"bullet", r"splendor", r"pulsar", r"honda", r"suzuki", r"maruti",
            r"hyundai", r"tata", r"alto", r"swift", r"i10", r"i20"
        ]
    },
    
    "pest_control": {
        "emoji": "🪳",
        "offer_keywords": [
            # English
            "pest control available", "pest control service",
            "termite treatment", "cockroach control",
            # Hindi
            "pest control milega", "pest control ka kaam"
        ],
        "query_keywords": [
            # English
            "need pest control", "pest control required", "looking for pest control",
            "cockroach problem", "termite problem", "ant problem", "bed bugs",
            "mosquito problem", "rat problem", "pest issue",
            # Typos
            "pest contol", "cockroch", "termit problem",
            # Hindi
            "pest control chahiye", "cockroach problem hai", "kide makode",
            "chuhe ki problem", "machhar problem"
        ],
        "subcategory_patterns": [
            r"cockroach", r"termite", r"ant", r"bed bug", r"mosquito", r"rat"
        ]
    },
    
    "painter": {
        "emoji": "🎨",
        "offer_keywords": [
            # English
            "painter available", "painting service", "painting work",
            "i am painter", "home painting", "wall painting",
            # Typos
            "paintar available", "paiter",
            # Hindi
            "painter milega", "painting ka kaam", "rang wala"
        ],
        "query_keywords": [
            # English
            "need painter", "painter required", "looking for painter",
            "painting needed", "wall paint", "house painting",
            "any painter", "painter contact",
            # Typos
            "paintar chahiye", "paiter needed", "paintng needed",
            # Hindi
            "painter chahiye", "painting ka kaam", "rang karna hai",
            "koi painter", "rang wala chahiye", "ghar paint karna"
        ],
        "subcategory_patterns": [
            r"paint", r"wall", r"room", r"house", r"interior", r"exterior"
        ]
    },
    
    "security_guard": {
        "emoji": "👮",
        "offer_keywords": [
            # English
            "security guard available", "watchman available",
            "guard available", "security service",
            # Hindi
            "guard milega", "chowkidar milega", "watchman milega"
        ],
        "query_keywords": [
            # English
            "need security guard", "guard required", "looking for watchman",
            "security needed", "night guard", "day guard",
            # Typos
            "gaurd required", "secrity guard", "watchmn needed",
            # Hindi
            "guard chahiye", "watchman chahiye", "chowkidar chahiye",
            "security chahiye", "raat ka guard", "din ka guard"
        ],
        "subcategory_patterns": [
            r"guard", r"watchman", r"chowkidar", r"security", r"night", r"day"
        ]
    }
}

# General query indicators (to differentiate queries from offers)
QUERY_INDICATORS = [
    # English
    "need", "require", "required", "looking for", "want", "wanted",
    "anyone", "any one", "anybody", "any body", "who has", "who have",
    "please share", "pls share", "can someone", "can anyone",
    "help needed", "urgent", "urgently", "asap", "immediately",
    "searching", "searching for", "find", "finding",
    "recommend", "recommendation", "suggest", "suggestion",
    "any good", "koi acha", "koi accha",
    # Typos
    "nedd", "ned", "requried", "requred", "lokking", "loking",
    # Hindi
    "chahiye", "chaiye", "chiye", "mangta", "mangti", "dedo", "de do",
    "bhejo", "batao", "bata do", "koi hai", "koi he", "zarurat",
    "jarurat", "urgent", "jaldi", "turant", "abhi", "foran"
]

# General offer indicators
OFFER_INDICATORS = [
    # English
    "available", "for sale", "selling", "on sale", "contact",
    "call me", "reach me", "dm me", "message me", "whatsapp",
    "my number", "contact me", "ping me", "text me",
    "i have", "i am", "we have", "we are",
    "want to sell", "want sell", "wanna sell", "selling my",
    # Typos
    "availble", "avalable", "avialable", "availabel", "seling",
    # Hindi
    "milega", "milegi", "mil jayega", "mil jayegi", "available hai",
    "bechna hai", "bech raha", "bech rahi", "contact karo", "call karo",
    "mere paas", "hamare paas", "hum hai", "main hun", "bechna chahta"
]

# Messages to ignore (greetings, general chat)
IGNORE_PATTERNS = [
    r"^good\s*(morning|evening|night|afternoon)",
    r"^gm\b", r"^ge\b", r"^gn\b",
    r"^(hi|hello|hey|hii|helloo)\b",
    r"^(thanks|thank you|thanku|thnx|ty|thx|thanx)",
    r"^(ok|okay|k|done|noted|oka|okk)",
    r"^(yes|no|ya|nahi|haan|han|nope|yep|yup)",
    r"^(happy|wish|wishing).*(birthday|anniversary|diwali|holi|eid|christmas)",
    r"^(congratulations|congrats|congos)",
    r"^\+\d",  # Just phone numbers
    r"^https?://",  # Just links
    r"^@\w+$",  # Just mentions
    r"^(lol|haha|hehe|😂|🤣|👍|🙏)+$",  # Just reactions
    r"^(ji|jee|hmm|hmmm|accha|achha|sahi|theek|thik)\b",
]
