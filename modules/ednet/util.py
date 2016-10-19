class Util:
    def __init__(self):
        pass

    @staticmethod
    def GetModList(attr_list, mod_op=None):
        modlist = []
        for attrtype in attr_list.keys():
            attrvaluelist = filter(lambda x:x!=None, attr_list[attrtype])
            if attrvaluelist:
                if (mod_op != None):
                    modlist.append((mod_op, attrtype, attr_list[attrtype]))
                else:
                    modlist.append((attrtype, attr_list[attrtype]))
        return modlist

    @staticmethod
    def GetCellValue(sheet, row, col, default_val=""):
        ret = default_val
        try:
            val = str(sheet.cell(row, col).value)
            # Strips off the .0 at the end of numbers
            if (val.endswith(".0")):
                val = val[:-2]
            ret = val
        except:
            #ret = "ERROR!!!"
            pass
        return ret

    @staticmethod
    def GetJSONFromCellRange(sheet, row, col_start, col_end):
        from gluon.serializers import json
        # Loop through the cols and add them do an array
        items = dict()
        for col in range(col_start, col_end):
            items["col_"+str(col)] = Util.GetCellValue(sheet, row, col)

        json_cols = json(items)
        return json_cols

    @staticmethod
    def ParseName(full_name):
        # Split name into parts
        pos = full_name.find(",")
        if (pos != -1):
            # Found comma, should be last name first
            parts = full_name.split(',', 2)
            parts = (parts[1].strip(), parts[0].strip())
            return parts

        # Assume first <space> last format
        parts = full_name.split(None, 2)
        if (len(parts) > 1):
            parts = (parts[0].strip(), parts[1].strip())
        elif (len(parts) == 1):
            parts = (parts[0].strip())
        return parts
