from pymongo import MongoClient

mongo = MongoClient("localhost", 27017)
worksheets = mongo.hgsystem.worksheets
counter = 0
for worksheet in worksheets.find():
    print(f"\r{worksheet['_id']}", end="")
    worksheet['bc_r'] = ""
    worksheet['bc_l'] = ""
    worksheet['eyesight_r'] = worksheet['sight_see_r']
    worksheet['eyesight_l'] = worksheet['sight_see_l']
    worksheet.pop('sight_see_r')
    worksheet.pop('sight_see_l')
    worksheets.find_one_and_replace({"_id": worksheet['_id']}, worksheet)
    counter += 1
mongo.close()
print(f"Total {counter}-worksheet updated.")