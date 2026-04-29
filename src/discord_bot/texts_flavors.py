import random
import time

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

FULFILLED_WISH_FLAVOR = [
    "{player1} dragged themselves to {location} to retrieve {item} for {player2}. Against better judgment, they complied.",
    "{player1} returned from {location} with {item} for {player2}. Yes, it was as unnecessary as it sounds.",
    "{player1} fetched {item} at {location} for {player2}. A perfect example of wasted potential.",
    "{player1} completed {player2}'s demand for {item} from {location}. Nothing says teamwork like exploitation.",
    "{player1} went to {location}, got {item}, and handed it to {player2}. Truly, a career-defining low point.",
    "{player1} obtained {item} from {location} for {player2}. Hope it was worth the existential damage.",
    "{player1} served {player2} by retrieving {item} at {location}. The hierarchy is now clear.",
    "{player1} brought back {item} from {location} for {player2}. One step closer to realizing they can be sent anywhere.",
    "{player1} fulfilled {player2}'s little wish for {item} from {location}. How quaintly one-sided.",
    "{player1} retrieved {item} at {location} for {player2}. Labor distribution remains a hilarious concept.",
    "{player1} wasted their time at {location} acquiring {item} for {player2}. Hope that felt important.",
    "{player1} obeyed and fetched {item} from {location} for {player2}. No one is surprised.",
    "{player1} completed the ritual of servitude: {item} secured at {location} for {player2}.",
    "{player1} brought {item} from {location} to {player2}. Delegation success. Self-respect failure.",
    "{player1} returned with {item} from {location} for {player2}. Congratulations on enabling this behavior.",
    "{player1} handled {item} acquisition at {location} for {player2}. They will absolutely be asked again.",
    "{player1} fetched {item} from {location} for {player2}. Efficiency was not the goal—obedience was.",
    "{player1} completed the errand for {player2}: {item} from {location}. A thrilling use of talent.",
    "{player1} secured {item} at {location} for {player2}. No reward was mentioned. Of course.",
    "{player1} did the thing again: got {item} from {location} for {player2}. Character development unclear.",
    "{player1} heroically fulfilled {player2}'s totally reasonable request by fetching {item} from {location}. Truly inspiring teamwork.",
    "{player1} went all the way to {location} to get {item} for {player2}. Because apparently, no one else could.",
    "{player1} delivered {item} from {location} to {player2}. Cooperation achieved. Barely.",
    "{player1} picked up {item} at {location} for {player2}. A sacrifice that will not be remembered.",
    "{player1} successfully retrieved {item} from {location} for {player2}. The bar was low, but still.",
    "{player1} got {item} from {location} for {player2}. Let’s all pretend this was a team effort.",
    "{player1} made the bold journey to {location} and returned with {item} for {player2}. Someone had to do it.",
    "{player1} answered {player2}'s call by grabbing {item} at {location}. Reluctantly, probably.",
    "{player1} fulfilled {player2}'s wish for {item} from {location}. A shocking display of competence.",
    "{player1} brought back {item} from {location} for {player2}. Expectations were exceeded. Slightly.",
    "{player1} handled {player2}'s request for {item} at {location}. Truly, a one-person team.",
    "{player1} secured {item} from {location} for {player2}. The rest of the team watched, surely.",
    "{player1} fetched {item} at {location} for {player2}. Because delegating is easier than helping.",
    "{player1} completed the mission: {item} acquired at {location} for {player2}. Applause is optional.",
    "{player1} went to {location}, got {item}, and gave it to {player2}. Efficiency or just resignation?",
    "{player1} made sure {player2} got their precious {item} from {location}. Priorities, clearly.",
    "{player1} retrieved {item} from {location} for {player2}. A task no one else mysteriously volunteered for.",
    "{player1} delivered {item} from {location} to {player2}. The definition of teamwork has been stretched.",
    "{player1} grabbed {item} at {location} for {player2}. Because saying no was apparently not an option.",
    "{player1} fulfilled {player2}'s request for {item} from {location}. Against all odds (and motivation).",
    "{player1} went to {location} and retrieved {item} for {player2}. Reliable as ever.",
    "{player1} returned from {location} with {item} for {player2}. Solid teamwork.",
    "{player1} fetched {item} at {location} for {player2}. Nicely handled.",
    "{player1} completed {player2}'s request for {item} from {location}. Efficient and effective.",
    "{player1} went to {location}, got {item}, and delivered it to {player2}. Smooth execution.",
    "{player1} obtained {item} from {location} for {player2}. Mission accomplished.",
    "{player1} came through with {item} from {location} for {player2}. Dependable as always.",
    "{player1} brought back {item} from {location} for {player2}. That’s how it’s done.",
    "{player1} fulfilled {player2}'s request for {item} from {location}. Clean work.",
    "{player1} retrieved {item} at {location} for {player2}. Nicely played.",
    "{player1} secured {item} at {location} for {player2}. Strong contribution.",
    "{player1} delivered {item} from {location} to {player2}. Teamwork in action.",
    "{player1} handled the {item} pickup at {location} for {player2}. Well executed.",
    "{player1} made the trip to {location} and returned with {item} for {player2}. Worth it.",
    "{player1} completed the task: {item} acquired at {location} for {player2}. Great job.",
    "{player1} grabbed {item} at {location} for {player2}. Quick and efficient.",
    "{player1} answered the call and picked up {item} at {location} for {player2}. Nicely done.",
    "{player1} fulfilled the request for {item} from {location} for {player2}. Strong play.",
    "{player1} brought {item} from {location} to {player2}. That’s real support.",
    "{player1} returned with {item} from {location} for {player2}. Always delivering.",
    "{player1} took care of {item} at {location} for {player2}. Reliable execution.",
    "{player1} secured {item} from {location} for {player2}. Big help to the team.",
    "{player1} fetched {item} at {location} for {player2}. Smooth teamwork.",
    "{player1} completed the errand for {player2}: {item} from {location}. Nicely handled.",
    "{player1} handled {player2}'s request for {item} at {location}. Clean and efficient.",
    "{player1} delivered {item} from {location} to {player2}. Strong coordination.",
    "{player1} picked up {item} at {location} for {player2}. Good call.",
    "{player1} successfully retrieved {item} from {location} for {player2}. Well played.",
    "{player1} made the journey to {location} and came back with {item} for {player2}. Clutch move.",
    "{player1} stepped up and got {item} from {location} for {player2}. Team player.",
    "{player1} fulfilled {player2}'s wish for {item} from {location}. Nicely executed.",
    "{player1} brought back {item} from {location} for {player2}. That made a difference.",
    "{player1} took initiative and secured {item} at {location} for {player2}. Great teamwork.",
    "{player1} retrieved {item} from {location} for {player2}. Efficient as always.",
    "{player1} delivered exactly what was needed: {item} from {location} for {player2}.",
    "{player1} handled the mission: {item} acquired at {location} for {player2}. Success.",
    "{player1} made sure {player2} got {item} from {location}. Nicely supported.",
    "{player1} grabbed {item} at {location} for {player2}. Fast and effective.",
    "{player1} came through again with {item} from {location} for {player2}. Consistent.",
    "{player1} fulfilled the request for {item} from {location} for {player2}. Great execution."
]

WISHLIST_FLAVORS = [
    "Here’s the list of items you’re currently hoping others will find for you. No pressure, of course.",
    "Ah yes, the things you’d rather let others deal with. Efficient.",
    "Here’s everything you’ve politely outsourced to your teammates.",
    "Behold: your personal wishlist, generously delegated to others.",
    "Here’s what you’re waiting for others to magically deliver.",
    "A curated list of problems you’ve decided are someone else’s responsibility.",
    "Here’s what you’re relying on your teammates for. Bold strategy.",
    "Ah, the list of items you confidently expect others to handle.",
    "Here’s your 'I’ll let someone else do it' collection.",
    "Behold: the items you are absolutely not going out of your way to find.",
    "Here’s what you’re hoping will just… happen.",
    "A neat summary of things you expect to receive without lifting a finger.",
    "Here’s your contribution to teamwork: expectations.",
    "Ah yes, the famous list of 'someone else will get it'.",
    "Here’s everything you’ve decided is a group problem now.",
    "Behold your requests, carefully crafted and entirely someone else’s problem.",
    "Here’s what you’re waiting on. No rush… for you, at least.",
    "A fine selection of items you’d love to receive someday.",
    "Here’s your dependency list. Good luck to everyone else.",
    "Everything you need, and none of it your responsibility. Impressive.",
    "Here’s your wishlist — a clear sign you know exactly what you need. Nice.",
    "A well-thought-out list of priorities. Your team appreciates the clarity.",
    "Here’s what would help you shine even more. Good call.",
    "A refined selection of items to boost your progress. Smart thinking.",
    "Here’s your roadmap to success, neatly outlined.",
    "You’ve got a clear vision — here’s what will get you there.",
    "A strong wishlist. Your teammates know exactly how to support you.",
    "Here’s a solid list of goals. Efficient and to the point.",
    "A carefully considered set of needs. Nicely done.",
    "Here’s what will take you to the next level. Looking good.",
    "A focused wishlist — you’re setting yourself up for success.",
    "Here’s your game plan. Simple, clear, effective.",
    "You know what you’re doing — here’s the proof.",
    "A clean and purposeful list. Your team can work with that.",
    "Here’s what you need to keep the momentum going.",
    "A smart selection of items. You’re playing this well.",
    "Here’s your priority list. Confident choices.",
    "You’ve made it easy for others to help — that’s good teamwork.",
    "A sharp wishlist. You’re clearly thinking ahead.",
    "Here’s what will make a difference for you. Well identified."
]

DEATHLINK_FLAVOR = [
    "{dead_player} has fallen.",
    "{dead_player} has met their end.",
    "{dead_player} didn't make it.",
    "{dead_player} has perished.",
    "{dead_player} is no more.",
    "{dead_player} has been defeated.",
    "{dead_player} has died. Stay sharp, everyone.",
    "{dead_player} has fallen in battle.",
    "{dead_player} couldn't survive this one.",
    "{dead_player} has been eliminated.",
    "{dead_player} has fallen... and you're all coming with them.",
    "{dead_player} is gone. That’s unfortunate for everyone.",
    "{dead_player} has died. Hope you were ready.",
    "{dead_player} bit the dust. Brace yourselves.",
    "{dead_player} is out. This won’t end well for the rest of you.",
    "{dead_player} has fallen. Consequences incoming.",
    "{dead_player} has died. That’s going to hurt.",
    "{dead_player} died. Impressive, really.",
    "{dead_player} has perished. Truly a masterclass performance.",
    "{dead_player} is dead. Didn’t see that coming. (We did.)",
    "{dead_player} managed to die. Congratulations.",
    "{dead_player} has fallen. Flawless execution.",
    "{dead_player} is no more. Outstanding move.",
    "{dead_player} died. That was definitely intentional.",
    "{dead_player} has perished. Skill issue?",
    "{dead_player} is gone. Bold strategy.",
    "{dead_player} died. Truly one of the plays of all time.",
    "{dead_player} has died. Maybe try not doing that next time?",
    "{dead_player} is dead. That seemed avoidable.",
    "{dead_player} has fallen. You had one job.",
    "{dead_player} died. We're all very impressed.",
    "{dead_player} has perished. Stunning lack of survival instinct.",
    "{dead_player} is no more. A predictable outcome.",
    "{dead_player} died. Could have gone better.",
    "{dead_player} has fallen. At least you tried. Sort of.",
]

def get_clear_todolist_flavor() -> str :
    return random.choice(CLEAR_TODOLIST_FLAVOR)

def get_todolist_flavor() -> str :
    return random.choice(TODOLIST_FLAVOR)

def get_empty_todolist_flavor() -> str :
    return random.choice(EMPTY_TODOLIST_FLAVOR)

def get_fulfilled_wish_flavor(player_sending: str, player_recieving: str, item: str, location: str) -> str :
    flavor = random.choice(FULFILLED_WISH_FLAVOR)
    return flavor.format(player1=player_sending, player2=player_recieving, item=item, location=location)

def get_wishlist_flavor() -> str :
    return random.choice(WISHLIST_FLAVORS)

def get_deathlink_flavor(dead_player: str, death_time: float) -> str :
    flavor = random.choice(DEATHLINK_FLAVOR)
    flavor = flavor.format(dead_player=dead_player)
    time_struct = time.localtime(death_time)
    time_str = time.strftime("%m-%d %H:%M:%S", time_struct)
    return f"```ansi\n💀 \u001b[0;31m[{time_str}]\u001b[0m {flavor}\n```"