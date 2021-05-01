from enum import Enum
import datetime
import logging

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
	OffTrack = "<:offtrack:769633560327880706>"
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
    elif "green flag" in msg.lower():
        return addFlag(msg, FlagEmotes.Green.value, currentEvent)
    elif any(x in msg.lower() for x in ["warning", "black / white", "black and white"]):
        return addFlag(msg, FlagEmotes.BlackWhite.value, currentEvent)
    elif "penalty" in msg.lower():
        return addFlag(msg, FlagEmotes.Black.value, currentEvent)
    elif any(x in msg.lower() for x in ["yellow", "slow zone"]):
        return addFlag(msg, FlagEmotes.Yellow.value, currentEvent)
    elif "retired" in msg.lower():
        return addFlag(msg, FlagEmotes.Retired.value, currentEvent)
    elif "code 60" in msg.lower():
        return addFlag(msg, FlagEmotes.Code60.value, currentEvent)
    elif any(x in msg.lower() for x in ["chequered flag", "checkered flag"]):
        return addFlag(msg, FlagEmotes.Checkered.value, currentEvent)
    elif "red flag" in msg.lower():
        return addFlag(msg, FlagEmotes.Red.value, currentEvent)
    elif "under investigation" in msg.lower():
        return addFlag(msg, FlagEmotes.Investigation.value, currentEvent)
    elif "track limits" in msg.lower():
        return addFlag(msg, FlagEmotes.OffTrack.value, currentEvent)
    else:
        return ("**" + currentEvent["name"] + " - " + currentEvent["description"] + "**\n" + msg)

def cleanCarInfoValue(value):
    if isinstance(value, list):
        try:
            time = datetime.datetime.utcfromtimestamp(float(value[0]))
            return datetime.datetime.strftime(time, "%M:%S.%f")[:-3]
        except ValueError:
            return value[0]
    elif value == "":
        return "N/A"
    else:
        return value

def formatCarInfo(carDict, spec, currentEvent):
    if isinstance(carDict, str):
		return addEvent(carDict, currentEvent)
	
    res = ""
    if spec is not None:
        for key, value in carDict.items():
            if spec.lower() == key.lower():
                res = res + "{0}: {1}\n".format(key, cleanCarInfoValue(value))
            elif spec.lower() in key.lower():
                res = res + "{0}: {1}\n".format(key, cleanCarInfoValue(value))
    else:
        for key, value in carDict.items():
            if any(x in key.lower() for x in ["sector"]):
                continue
            res = res + "{0}: {1}\n".format(key, cleanCarInfoValue(value))
    
    return addEvent(res, currentEvent)
		
def formatTrackInfo(trackInfo, currentEvent):
    res = ""
    for key, value in trackInfo.items():
        res = res + "{0}: {1}\n".format(key, value)

    return addEvent(res, currentEvent)
