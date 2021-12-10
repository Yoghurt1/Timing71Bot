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
    Meatball = "<:meatball:759447536376873000>"
    Blue = "<:blueflag:759534303788400670>"
    Checkered = "🏁"
    Investigation = "🔍"
    PB = "🟩"
    SB = "🟪"
    DriverChange = "🔄"


def addFlag(msg, flag, event):
    msgWithFlag = flag + " " + msg + " " + flag
    return addEvent(msgWithFlag, event)

def addEvent(msg, event):
    return "{name} - {description}\n{msg}".format(name=event["name"], description=event["description"], msg=msg)

def formatWithFlags(msg, event):
    if any(
        x in msg.lower()
        for x in ["full course yellow", "virtual", "full course caution"]
    ):
        return addFlag(msg, FlagEmotes.Fcy.value, event)
    elif "safety car" in msg.lower():
        return addFlag(msg, FlagEmotes.SafetyCar.value, event)
    elif any(
        x in msg.lower()
        for x in [
            "green flag",
            "track clear",
            "slow removed",
            "slow zone removed",
            "yellow removed",
        ]
    ):
        return addFlag(msg, FlagEmotes.Green.value, event)
    elif any(x in msg.lower() for x in ["warning", "black / white", "black and white"]):
        return addFlag(msg, FlagEmotes.BlackWhite.value, event)
    elif any(x in msg.lower() for x in ["penalty", "black flag"]):
        return addFlag(msg, FlagEmotes.Black.value, event)
    elif "upgraded to code 60" in msg.lower():
        return addFlag(msg, FlagEmotes.Code60.value, event)
    elif any(
        x in msg.lower()
        for x in [
            "yellow",
            "slow zone",
            "downgraded to slow",
            "slow at mp",
            "slow at zone",
            "slow procedure",
        ]
    ):
        return addFlag(msg, FlagEmotes.Yellow.value, event)
    elif "retired" in msg.lower():
        return addFlag(msg, FlagEmotes.Retired.value, event)
    elif "code 60" in msg.lower():
        return addFlag(msg, FlagEmotes.Code60.value, event)
    elif any(x in msg.lower() for x in ["chequered flag", "checkered flag"]):
        return addFlag(msg, FlagEmotes.Checkered.value, event)
    elif "red flag" in msg.lower():
        return addFlag(msg, FlagEmotes.Red.value, event)
    elif "under investigation" in msg.lower():
        return addFlag(msg, FlagEmotes.Investigation.value, event)
    elif "track limits" in msg.lower():
        return addFlag(msg, FlagEmotes.OffTrack.value, event)
    elif any(
        x in msg.lower() for x in ["black / orange", "black and orange", "meatball"]
    ):
        return addFlag(msg, FlagEmotes.Meatball.value, event)
    elif "blue flag" in msg.lower():
        return addFlag(msg, FlagEmotes.Blue.value, event)
    elif "personal best" in msg.lower():
        return addFlag(msg, FlagEmotes.PB.value, event)
    elif "overall best" in msg.lower():
        return addFlag(msg, FlagEmotes.SB.value, event)
    elif "driver change" in msg.lower():
        return addFlag(msg, FlagEmotes.DriverChange.value, event)
    else:
        return addEvent(msg, event)


def cleanCarInfoValue(spec, value):
    if isinstance(value, list):
        if "time" in spec.lower():
            time = datetime.datetime.utcfromtimestamp(float(value[0]))
            return datetime.datetime.strftime(time, "%M:%S.%f")[:-3]
        elif "speed" in spec.lower():
            return "{0}mph".format(value[0] if value[0] != "" else 0)
        else:
            return value[0] if value[0] != "" else 0
    elif "speed" in spec.lower():
        return "{0}mph".format(value)
    elif value == "":
        return "N/A"
    else:
        return value


def formatCarInfo(carDict, spec):
    if isinstance(carDict, str):
        return carDict

    res = ""
    if spec is not None:
        for key, value in carDict.items():
            if spec.lower() == key.lower():
                res = res + "{0}: {1}\n".format(key, cleanCarInfoValue(key, value))
            elif spec.lower() in key.lower():
                res = res + "{0}: {1}\n".format(key, cleanCarInfoValue(key, value))
    else:
        for key, value in carDict.items():
            if any(x in key.lower() for x in ["sector"]):
                continue
            res = res + "{0}: {1}\n".format(key, cleanCarInfoValue(key, value))

    return res


def formatTrackInfo(trackInfo):
    res = ""
    for key, value in trackInfo.items():
        res = res + "{0}: {1}\n".format(key, value)

    return res


def formatEventMessage(index, event):
    return "{idx}. {name} - {description}".format(
        idx=(index + 1), name=event["name"], description=event["description"]
    )
