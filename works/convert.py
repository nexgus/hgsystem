import datetime
import string
import sys

from datetime import date
from datetime import datetime
from dbfread import DBF
from pymongo import MongoClient

####################################################################################################
def pure_ascii(s):
    for c in s:
        if c not in string.printable:
            return False
    return True

####################################################################################################
def getCustomerName(record):
    name = record['NAME'].strip()
    if not pure_ascii(name):
        name = name.replace(" ", "").replace("\\", "")
    return name

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
def getCustomerPhoneNumber(record):
    all_tel = []
    for col in ("TEL1", "TEL2"):
        tel = record[col].strip().replace("\\", "").replace(".", "").replace(";", "").replace("-", "")
        all_tel += tel.split()  # tel is seperated by a space
    return ";".join(all_tel)

####################################################################################################
def getLens(record):
    lens = record["LENSE"].strip().replace("\\", "")
    contactLens = record["CONTACT_LE"].strip().replace("\\", "")
    if len(lens) > 0:
        return lens, ''
    elif len(contactLens):
        return contactLens, ''
    else:
        return '', ''

####################################################################################################
def importCustomers():
    dbf = DBF("dbf/gname.DBF", char_decode_errors="ignore")
    total = len(dbf)

    mongo = MongoClient("localhost", 27017)
    collection = mongo.hgsystem.customers

    for idx, record in enumerate(dbf):
        print(f"{idx+1}/{total} {' '*27}", end="")
        print("\x08"*27, end="")

        name = getCustomerName(record)
        print(f"name={name}", end="")
        if name == "":
            print()
            continue

        sys.stdout.flush()
        document = {"name": name}

        _id = record["ID"].strip()
        if len(_id) > 0:
            document["_id"] = _id

        document["title"] = record["APPELLATIO"].strip()
        document["addr"] = record["ADDR"].strip().replace("\\", "")
        document["phones"] = getCustomerPhoneNumber(record)

        birthdate = record["BIRTHDAY"]
        if isinstance(birthdate, date): birthdate = datetime.combine(birthdate, datetime.min.time())
        document["birthdate"] = birthdate

        document["broker"] = record["INTRODUCE"].strip().replace("\\", "")

        collection.insert_one(document)
        print("\r", end="")

    mongo.close()
    print()

####################################################################################################
def importWorksheets():
    dbf = DBF("dbf/gdata.DBF", char_decode_errors="ignore")
    total = len(dbf)
    
    mongo = MongoClient("localhost", 27017)
    customers = mongo.hgsystem.customers
    worksheets = mongo.hgsystem.worksheets
    
    wids = []  # existing wid
    errors = 0
    for idx, record in enumerate(dbf):
        print(f"{idx+1}/{total} {' '*24}", end="")
        print("\x08"*24, end="")

        cid = record["ID"].strip()
        name, err = getNameByID(customers, cid)

        # To prevent wid duplicates
        wid = record["SN"].strip()
        counter = 0
        while wid in wids:
            counter += 1
            wid = f"{record['SN'].strip()}_{counter}"
        wids.append(wid)

        if name == "":
            errors += 1
            print(f' wid="{wid}", cid="{cid}", ', end="")
            if err:
                print(f'err="{err}"')
            else:
                print(f'name="{name}"')
            continue
        print(f" -> {name}", end="\r", flush=True)

        document = {"_id": wid, "cid": cid}

        # 訂單時間
        order_time = record["RECEIVE_DA"]
        if isinstance(order_time, date): order_time = datetime.combine(order_time, datetime.min.time())
        document["order_time"] = order_time

        # 交貨時間
        deliver_time = record["GIVE_DATE"]
        if isinstance(deliver_time, date): deliver_time = datetime.combine(deliver_time, datetime.min.time())
        document["deliver_time"] = deliver_time

        # 度數, Spherical correction (SPH), 球面度數
        document["sph_r"] = record["DEGREE_RIG"].strip().replace("\\", "")
        document["sph_l"] = record["DEGREE_LEF"].strip().replace("\\", "")

        # 散光, Cylinder correction (CYL), 柱狀度數
        document["cyl_r"] = record["ASTIGMATI2"].strip().replace("\\", "")
        document["cyl_l"] = record["ASTIGMATIC"].strip().replace("\\", "")

        # 軸度, Axis, 散光軸度
        document["axis_r"] = record["ANGLE_RIGH"].strip().replace("\\", "")
        document["axis_l"] = record["ANGLE_LEFT"].strip().replace("\\", "")

        # base, bc.v, bc.h
        document["base_r"] = ""
        document["base_l"] = ""
        document["bcv_r"] = ""
        document["bcv_l"] = ""
        document["bch_r"] = ""
        document["bch_l"] = ""

        # 老花加入度, ADD
        document["add_r"] = record["ADDITION"].strip().replace("\\", "")
        document["add_l"] = ""

        # 瞳孔距離, PD (Pupillary Distance)
        document["pd"] = record["INTEROCULA"].strip().replace("\\", "")

        # source, sight_see_r, sight_see_l 視力
        document["source"] = ""
        document["sight_see_r"] = ""
        document["sight_see_l"] = ""

        # 鏡片度數 (含隱型眼鏡)
        document["lens_r"], document["lens_l"] = getLens(record)

        # 鏡架
        document["frame"] = record["FRAME"].strip().replace("\\", "")

        # 備註
        document["memo"] = record["MEMO"].strip().replace("\\", "")

        # 鏡片價格
        try:
            document["lens_price"] = int(record['LPRICE'])
        except Exception:
            try:
                document["lens_price"] = int(record['CPRICE'])
            except Exception:
                document["lens_price"] = 0

        # 鏡架價格
        try:
            document["frame_price"] = int(record['FPRICE'])
        except Exception:
            document["frame_price"] = 0

        worksheets.insert_one(document)
        print("\r", end="")

    print()
    print(f"Error Count: {errors}")
    mongo.close()

####################################################################################################
if __name__ == "__main__":
    importCustomers()
    importWorksheets()
