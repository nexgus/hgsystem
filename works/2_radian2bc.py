from dbfread import DBF
from pymongo import MongoClient

# [
#   'ID', 
#   'SN', 
#   'RECEIVE_DA', 'GIVE_DATE', 
#   'DEGREE_LEF', 'DEGREE_RIG', 
#   'ASTIGMATIC', 'ASTIGMATI2', 
#   'ANGLE_LEFT', 'ANGLE_RIGH', 
#   'INTEROCULA', 
#   'ADDITION', 
#   'RADIAN_LEF', 'RADIAN_RIG', 
#   'FRAME', 
#   'LENSE', 
#   'CONTACT_LE', 
#   'CPRICE', 'LPRICE', 'FPRICE', 'PRICE', 
#   'MEMO'
# ]

####################################################################################################
def getNameByID(customers, cid):
    if cid == "": return "", None
    try:
        document = customers.find_one({"_id": cid})
    except Exception as ex:
        name = ""
        error = ex
    else:
        if document is None:
            name = ""
            error = None
        else:
            name = document["name"]
            error = None
    return name, error

####################################################################################################
bc_list = ("B1", "B2", "B3", "Q1", "Q2", "Q3", "S", "M", "L", "8.00",  "8.10", "8.30", "8.50", 
           "8.70", "8.90", "9.00")
bc_extra_list = ("綠散L", "藍L", "M綠", "M藍")

dbf = DBF("dbf/gdata.DBF", char_decode_errors="ignore")
total = len(dbf)

mongo = MongoClient("localhost", 27017)
customers = mongo.hgsystem.customers
worksheets = mongo.hgsystem.worksheets

wids = []  # existing wid
for idx, rec in enumerate(dbf):
    print(f"\r{idx+1}/{total}", end="")
    wid = rec["SN"].strip()
    counter = 0
    while wid in wids:
        counter += 1
        wid = f"{rec['SN'].strip()}_{counter}"
    wids.append(wid)

    cid = rec["ID"].strip()
    name, _ = getNameByID(customers, cid)
    if name == "": continue

    bc_r, bc_l = "", ""
    val = rec['RADIAN_LEF'].strip()
    if val in bc_list:
        bc_r = val
    elif val in bc_extra_list:
        if "L" in val: bc_r = "L"
        if "M" in val: bc_r = "M"
    val = rec['RADIAN_RIG'].strip()
    if val in bc_list:
        bc_l = val
    elif val in bc_extra_list:
        if "L" in val: bc_l = "L"
        if "M" in val: bc_l = "M"

    if bc_r == "" and bc_l == "": continue
    worksheets.find_one_and_update(
        {"_id": wid},
        {"$set": {"bc_r": bc_r, "bc_l": bc_l}}
    )
    print(f" {cid}/{name}/{wid}: {bc_r}/{bc_l}")

print()

mongo.close()
