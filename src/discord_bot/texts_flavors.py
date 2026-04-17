import random

CLEAR_TODOLIST_FLAVOR = [
    "Your todo list has been cleared. Clearly, the needs of your teammates were… optional.",
    "Todo list cleared. It’s almost like your teammates didn’t need those items after all.",
    "Your todo list is now empty. Maybe your teammates will find a way to get those items themselves? Who knows.",
    "Todo list cleared. It’s almost as if your teammates were just asking for the sake of asking, without any real need for those items.",
    "Your todo list has been cleared. It’s almost like your teammates were just trying to make you feel useful, without any real intention of actually needing those items.",
    "Your todo list has been cleared. Your teammates' requests have been respectfully ignored.",
    "Your todo list has been cleared. Your teammates will surely appreciate how little you care.",
    "Your todo list has been cleared. A bold statement that other players' needs are, indeed, none of your concern.",
    "Your todo list has been cleared. Who needs to cooperate anyway?"
]

TODOLIST_FLAVOR = [
    "Here's the list of items your teammates desperately needed. Don't worry, it's not like they actually needed them or anything.",
    "Behold, the highly negotiated list of items your teammates absolutely needed. It's almost as if they were just asking for the sake of asking, without any real need for those items.",
    "Here lies the completely reasonable list of things your team expects you to grab",
    "Behold: a small and absolutely not overwhelming list of urgent necessities",
    "Here’s what your team casually decided you should handle",
    "Ah yes, the list of items that somehow became your responsibility",
    "Behold: the result of intense negotiations you were not invited to",
    "Here’s the short list of things your teammates gently insist you pick up",
    "Presenting: the entirely optional (but actually not) list of items",
    "Behold: the collective wish list your teammates have entrusted to you",
    "Here’s what your team believes is a perfectly reasonable workload",
    "Ah, the famous list of 'quick stops' your teammates mentioned",
    "Your teammates left you a little list. How nice of them",
    "Guess who’s picking these up?",
    "You’re gonna love this list",
    "This has your name all over it, apparently",
    "Not sure how, but this is on you now"
]

EMPTY_TODOLIST_FLAVOR = [
    "Congratulations! Your todo list is empty.",
    "All clear! No items on your todo list.",
    "Your todo list is currently empty. Enjoy the calm before the storm!",
    "Nothing to see here! Your todo list is empty.",
    "Your todo list is as empty as your teammates' promises to help.",
    "No tasks. Did your teammates forget about you?",
    "You have no assigned tasks. This feels wrong.",
    "No items. Did they lose faith in you?",
    "No tasks. Try not to get used to it.",
    "A rare moment of peace. Cherish it.",
    "For once, the list is empty. A miracle.",
    "You stand unburdened. For now.",
    "A truly impressive list of zero items."
]

def get_clear_todolist_flavor() -> str :
    return random.choice(CLEAR_TODOLIST_FLAVOR)

def get_todolist_flavor() -> str :
    return random.choice(TODOLIST_FLAVOR)

def get_empty_todolist_flavor() -> str :
    return random.choice(EMPTY_TODOLIST_FLAVOR)