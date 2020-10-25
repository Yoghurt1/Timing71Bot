from enum import Enum

class FlagEmotes(Enum):
	Yellow = "<:yellowflag:759534303817236550>"
	Green = "<:greenflag:759534303821692988>"
	BlackWhite = "<:blackwhiteflag:759447554047475723>"
	Black = "<:blackflag:759534303595331615>"
	SafetyCar = "<:safetycar:757207851893522472>"
	Fcy = "<:fcy:759432420092805170>"
	Retired = "<:F_:592914927396585472>"
	Red = "<:redflag:759534303842402314>"
	Code60 = "<:code60:759432100558012436>"
	Checkered = "🏁"
	Investigation = "🔍"

def addEvent(msg, currentEvent):
    return ("**" + currentEvent["name"] + " - " + currentEvent["description"] + "**\n" + msg)

def addFlag(msg, flag, currentEvent):
    msgWithFlag = flag + " " + msg + " " + flag
    return addEvent(msgWithFlag, currentEvent)

def formatWithFlags(msg, currentEvent):
    if any(x in msg.lower() for x in ["full course yellow", "virtual", "full course caution"]):
        return addFlag(msg, FlagEmotes.Fcy.value, currentEvent)
    elif "safety car" in msg.lower():
        return addFlag(msg, FlagEmotes.SafetyCar.value, currentEvent)
    elif "green" in msg.lower():
        return addFlag(msg, FlagEmotes.Green.value, currentEvent)
    elif any(x in msg.lower() for x in ["warning", "black / white"]):
        return addFlag(msg, FlagEmotes.BlackWhite.value, currentEvent)
    elif "penalty" in msg.lower():
        return addFlag(msg, FlagEmotes.Black.value, currentEvent)
    elif any(x in msg.lower() for x in ["yellow", "slow zone"]):
        return addFlag(msg, FlagEmotes.Yellow.value, currentEvent)
    elif "retired" in msg.lower():
        return addFlag(msg, FlagEmotes.Retired.value, currentEvent)
    elif "code 60" in msg.lower():
        return addFlag(msg, FlagEmotes.Code60.value, currentEvent)
    elif "chequered flag" in msg.lower():
        return addFlag(msg, FlagEmotes.Checkered.value, currentEvent)
    elif "red" in msg.lower():
        return addFlag(msg, FlagEmotes.Red.value, currentEvent)
    elif "under investigation" in msg.lower():
        return addFlag(msg, FlagEmotes.Investigation.value, currentEvent)
    else:
        return ("**" + currentEvent["name"] + " - " + currentEvent["description"] + "**\n" + msg)
		
