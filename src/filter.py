import logging
from datetime import datetime

def find_sig(s: str) -> list:
    rtn = []
    for x in range(len(s)):
        if s[x] == '$' and (x == 0 or not s[x-1] == "\\"):
            rtn.append(x)
            break
    if len(rtn) == 0:
        return rtn
    count = 0
    for x in range(rtn[0]+2, len(s)):
        if s[x] == '\\':
            count += 1
        elif s[x] == "}" and count % 2 == 0:
            rtn.append(x)
            break
        else:
            count = 0
    return rtn

def filter(desc: str, pattern:str ,logger:logging.Logger) -> bool:
    if pattern == "":
        return True
    
    expr = pattern.replace(" ", "")
    while 1:
        rtn = find_sig(expr)
        if len(rtn) == 0:
            break
        elif len(rtn) == 2:
            expr = expr[:rtn[0]] + "\"" + expr[rtn[0] + 2 : rtn[1]] + "\" in desc" + expr[rtn[1]+1:]
        else:
            logger.error(f"Filter pattern error: {pattern} :")
            return True
    
    expr = expr.replace("\\}", "}")
    expr = expr.replace("\\{", "{")
    expr = expr.replace("\\$", "$")
    expr = expr.replace("not", "not ")
    expr = expr.replace("or", " or ")
    expr = expr.replace("and", " and ")
    
    try:
        return eval(expr, {"desc": desc})
    except Exception as e:
        logger.error(f"Filter pattern error: {pattern} : {e}")
        return True
    
def time_tran(time: str, logger:logging.Logger) -> int:
    if time:
        if not ':' in time:
            time = time.replace(" ", "")
            time += " 00:00:00"
        try:
            dt = datetime.strptime(time, r"%Y.%m.%d %H:%M:%S").timestamp()
        except ValueError as e:
            logger.error(f"Date limitation format error: {e}")
            return -1
        else:
            return int(dt)
    else:
        return -1

def time_limit(time: int, limit: str, logger:logging.Logger) -> bool:
    partition = limit.find('-')
    if  not partition == -1:
        d1 = limit[:partition]
        d2 = limit[partition:]
        d2 = d2.replace("-", "")
        date1 = time_tran(d1, logger)
        date2 = time_tran(d2, logger)
        if ((not date1 == -1) and (date1 > time)) or ((not date2 == -1) and (date2 < time)):
            return False
        else:
            return True
    else:
        return True

if __name__ == "__main__":
    log = logging.getLogger("test")
    print(filter(str(input("\ndesc:")), str(input("\npattern:")), log))