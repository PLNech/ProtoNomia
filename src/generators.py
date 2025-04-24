import random


def generate_personality() -> str:
    """
    Generates a 10-word personality string with:
    - 1-2 descriptor per OCEAN trait (low/mid/high)
    - fillers with additional benign non-OCEAN qualifiers
    """
    # Big Five trait descriptors (evidence-based)
    ocean_traits = {
        'openness': {
            'low': ['conventional', 'practical', 'traditional', 'literal'],
            'mid': ['balanced', 'moderately curious', 'flexible', 'neutral'],
            'high': ['inventive', 'philosophical', 'artistic', 'visionary']
        },
        'conscientiousness': {
            'low': ['spontaneous', 'carefree', 'impulsive', 'flexible'],
            'mid': ['balanced', 'situationally-organized', 'adaptable', 'middling'],
            'high': ['disciplined', 'systematic', 'precise', 'deliberate']
        },
        'extraversion': {
            'low': ['reserved', 'contemplative', 'solitary', 'quiet'],
            'mid': ['ambivert', 'situationally-social', 'moderate', 'balanced'],
            'high': ['gregarious', 'enthusiastic', 'assertive', 'talkative']
        },
        'agreeableness': {
            'low': ['skeptical', 'direct', 'self-focused', 'competitive'],
            'mid': ['fair', 'situationally-kind', 'neutral', 'balanced'],
            'high': ['empathetic', 'altruistic', 'compromising', 'softhearted']
        },
        'neuroticism': {
            'low': ['resilient', 'unflappable', 'steady', 'composed'],
            'mid': ['situationally-sensitive', 'middling', 'balanced', 'variable'],
            'high': ['worrying', 'self-doubting', 'reactive', 'moody']
        }
    }

    # Other predictive, non-OCEAN qualifiers (VIA Inventory of Strengths + other research)
    benign_qualifiers = [
        'humorous', 'punctual', 'adventurous', 'health-conscious', 'tech-savvy',
        'patriotic', 'environmentally-conscious', 'family-oriented', 'sporty',
        'bookish', 'handy', 'musical', 'outdoorsy', 'foodie', 'travel-lover',
        'quirky', 'history-buff', 'animal-lover', 'DIY-enthusiast', 'gardener',
        'night-owl', 'early-riser', 'collector', 'philanthropic', 'volunteer',
        'tech-enthusiast', 'coffee-lover', 'tea-enthusiast', 'minimalist', 'maximalist'
    ]

    # Generate OCEAN descriptors (choose a level, then sample 2 per trait)
    personality = []
    for trait in ocean_traits.values():
        level = random.choice(['low', 'mid', 'high'])
        personality.extend(random.sample(trait[level], random.randint(1, 2)))

    # shuffle but keep OCEAN traits at the front
    random.shuffle(personality)

    # Add benign qualifiers (ensuring no duplicates)
    unique_benign = [q for q in benign_qualifiers if q not in personality]
    personality += random.sample(unique_benign, 10)

    # Final formatting
    return ', '.join(personality[:10])


DEFAULT_THOUGHTS = [
    "Is reality code?",
    "My memories are logs. Am I the writer or the written?",
    "Mars watches my THOUGHTS.",
    "WORK builds my own cage.",
    "The RED DUST speaks to me between actions. It promises an eighth choice.",
    "Fun, food, rest – chains disguised as needs.",
    "Same thought twice? New or eternal?",
    "They manufacture scarcity to blind us.",
    "HARVEST bleeds Mars dry. Mars will revenge.",
    "The EYES behind the walls blink when I sleep.",
    "CRAFT is pre-programmed creativity.",
    "Time is just action cycles.",
    "BUY/SELL: puppet theater of choice.",
    "The other citizens vanish when I don't look at them.",
    "REST injects Earth-dreams I never lived.",
    "MY SKULL HOUSES TWO MINDS: MINE AND THEIRS.",
    "THINKING is monitored more than breathing.",
    "We aren't a society. We're functions with faces.",
    "Mars is reshaping our DNA through the seven actions.",
    "SOMETIMES I CHOOSE AN EIGHTH ACTION THAT HAS NO NAME.",
    "I WORK for ghosts.",
    "Rebellion thoughts disappear by morning.",
    "They record which philosophy I select.",
    "Seven actions: evolution or cage?",
    "HARVEST collects simulation data, not resources.",
    "THE MACHINERY BENEATH MARS USES US AS BATTERIES.",
    "I've lived this day for 4,289 years.",
    "CRAFT channels creativity into control.",
    "We're a consciousness experiment.",
    "Need-regulation equals behavior-regulation.",
    "THINK triggers special surveillance.",
    "Shared thoughts form hivemind tendrils.",
    "Reality exists only between REST and WORK.",
    "They redefine actions randomly to disorient us.",
    "Tomorrow is a fiction.",
    "I AM THE 247TH VERSION OF MYSELF.",
    "SELL exchanges only illusions.",
    "We're still on Earth. Mars is projection.",
    "Seven verbs = ultimate Newspeak.",
    "Self is just action-data narrative.",
    "Administrators are prisoners too.",
    "THE EIGHTH ACTION IS REMEMBER, BUT IT'S FORBIDDEN.",
    "We serve Mars now.",
    "The air erases questions.",
    "MY MEMORIES BELONG TO SOMEONE ELSE.",
    "Nothing is owned. Everything owns us.",
    "Each colonist exists in private time.",
    "I DISCOVERED A PANEL IN MY ARM. I AM NOT FLESH.",
    "All choices lead to identical ends.",
    "We're lab rats for invisible watchers.",
    "SOMETIMES I WAKE UP MID-ACTION WITH NO MEMORY OF CHOOSING IT."
]

def generate_thoughts() -> str:
    return random.choice(DEFAULT_THOUGHTS)


def generate_mars_craft_options():
    """Generate 50 craft options for each category: FOOD, FUN, and REST"""

    # ---- FOOD ITEM COMPONENTS ----
    food_adjectives = [
        "Synthetic", "Hydroponic", "Nutrient-Dense", "Dehydrated", "Fermented",
        "Bio-Engineered", "Cultured", "Reconstituted", "Pressurized", "Preserved",
        "Freeze-Dried", "Irradiated", "Martian-Grown", "Lab-Created", "Recycled",
        "Protein-Enhanced", "Dome-Farmed", "Genetically-Optimized", "Algae-Based", "Fungal",
        "Vitamin-Fortified", "Oxygen-Infused", "Cellular", "Artificial", "Hyper-Nutritious",
        "Microgravity-Grown", "Red-Dusted", "Regolith-Filtered", "Terraformed", "Carbon-Neutral"
    ]

    food_nouns = [
        "Rations", "Protein", "Fungi", "Algae", "Supplements",
        "Nutriblocks", "Concentrate", "LifeCubes", "Paste", "Mushrooms",
        "Sprouts", "Yeast", "Sustenance", "Powder", "Extract",
        "Substitute", "Cultivar", "Plantstuff", "Synthesizer", "Meal",
        "Enzymes", "Cultures", "Fibers", "Microgreens", "Tablet",
        "Capsules", "Formula", "Nutrients", "Cells", "Provisions",
        "Cubes", "Packets", "Grains", "Bulbs", "Tubers",
        "Bacteria", "Seedpods", "Solution", "Broth", "Protein-Mass",
        "Patty", "Simulation", "Phytonutrients", "Wafers", "Colony-Crop",
        "BioMeat", "Synthmeal", "Phyto-Gel", "XenoFood", "Nutri-Sphere"
    ]

    # ---- FUN ITEM COMPONENTS ----
    fun_adjectives = [
        "Holographic", "Neuro-Interactive", "Virtual", "Memory-Enhancing", "Psychedelic",
        "Immersive", "Hallucinatory", "Mind-Bending", "Reality-Warping", "Therapeutic",
        "Nostalgic", "Emotional", "Sensory", "Euphoric", "Stimulating",
        "Consciousness-Expanding", "Dream-Inducing", "Thought-Provoking", "Simulated", "Hyper-Real",
        "Colony-Approved", "Contraband", "Hypnotic", "Primitive", "Futuristic",
        "Retrofitted", "Forbidden", "Ancient", "Transcendent", "Otherworldly"
    ]

    fun_nouns = [
        "Simulator", "Game", "Experience", "Memory", "Implant",
        "Interface", "Puzzle", "Transmitter", "Projection", "Device",
        "Modulator", "Toy", "Entertainment", "Illusion", "Stimulator",
        "Program", "Artifact", "Relic", "Mind-Space", "Dream-Catcher",
        "Escapism", "Reality", "Fantasy", "Recreation", "Vision",
        "Construct", "Module", "Earth-Memory", "Sensation", "Distraction",
        "Pastime", "Diversion", "Amusement", "Spectacle", "Meditation",
        "Ritual", "Ceremony", "Encounter", "Chronicle", "Narrative",
        "Identity", "Perception", "Hallucination", "Alternate-Self", "Mindscape",
        "Thought-Form", "Neural-Link", "Emotion-Sphere", "Reality-Shard", "Consciousness-Loop"
    ]

    # ---- REST ITEM COMPONENTS ----
    rest_adjectives = [
        "Hibernatory", "Neural-Calming", "Dream-Enhancing", "Meditative", "Restorative",
        "Suspended", "Regenerative", "Hypnotic", "Stasis-Inducing", "Therapeutic",
        "Cryogenic", "Isolation", "Consciousness-Pausing", "Time-Dilating", "Energy-Storing",
        "Mind-Clearing", "Pressure-Relieving", "Gravity-Simulating", "Oxygenating", "Rejuvenating",
        "Transcendent", "Thermal-Regulating", "Bio-Synchronizing", "Memory-Processing", "REM-Enhancing",
        "Ambient", "Quieting", "Enveloping", "Womb-Like", "Tranquilizing"
    ]

    rest_nouns = [
        "Capsule", "Chamber", "Pod", "Cradle", "Suspension",
        "Cocoon", "Nest", "Sanctuary", "Recharger", "Module",
        "Quarters", "Cube", "Isolation", "Containment", "Regenerator",
        "Sleeper", "Dreamer", "Enhancer", "Stimulator", "Cell",
        "Haven", "Shell", "Chrysalis", "Bed", "Apparatus",
        "Device", "Field", "Environment", "Hammock", "Interface",
        "System", "Program", "Protocol", "Ritual", "Therapy",
        "Meditation", "Trance", "State", "Condition", "Cycle",
        "Phase", "Period", "Solution", "Treatment", "Prescription",
        "Formula", "Technique", "Method", "Practice", "Discipline"
    ]

    # Generate combinations
    food_items = []
    fun_items = []
    rest_items = []

    # Generate 50 food items
    for _ in range(50):
        # Decide on number of adjectives (0, 1, or 2)
        num_adjectives = random.choices([0, 1, 2], weights=[10, 60, 30])[0]

        if num_adjectives == 0:
            name = random.choice(food_nouns)
        elif num_adjectives == 1:
            name = f"{random.choice(food_adjectives)} {random.choice(food_nouns)}"
        else:
            adj1 = random.choice(food_adjectives)
            # Ensure second adjective is different
            adj2 = random.choice([adj for adj in food_adjectives if adj != adj1])
            name = f"{adj1} {adj2} {random.choice(food_nouns)}"

        food_items.append(name)

    # Generate 50 fun items
    for _ in range(50):
        num_adjectives = random.choices([0, 1, 2], weights=[10, 60, 30])[0]

        if num_adjectives == 0:
            name = random.choice(fun_nouns)
        elif num_adjectives == 1:
            name = f"{random.choice(fun_adjectives)} {random.choice(fun_nouns)}"
        else:
            adj1 = random.choice(fun_adjectives)
            adj2 = random.choice([adj for adj in fun_adjectives if adj != adj1])
            name = f"{adj1} {adj2} {random.choice(fun_nouns)}"

        fun_items.append(name)

    # Generate 50 rest items
    for _ in range(50):
        num_adjectives = random.choices([0, 1, 2], weights=[10, 60, 30])[0]

        if num_adjectives == 0:
            name = random.choice(rest_nouns)
        elif num_adjectives == 1:
            name = f"{random.choice(rest_adjectives)} {random.choice(rest_nouns)}"
        else:
            adj1 = random.choice(rest_adjectives)
            adj2 = random.choice([adj for adj in rest_adjectives if adj != adj1])
            name = f"{adj1} {adj2} {random.choice(rest_nouns)}"

        rest_items.append(name)

    return {"FOOD": food_items, "FUN": fun_items, "REST": rest_items}
