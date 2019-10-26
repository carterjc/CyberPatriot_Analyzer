import json
data = " = [['Time', 'Server2016_cpxii_r1_hsms', 'Ubuntu14_cpxii_r1_hs', 'Windows10_cpxii_r1_hsms'],['10/25 13:05', 0, 0, 0]" \
       ",['10/25 13:10', 18, 39, 0],['10/25 13:15', 43, 68, 13],['10/25 13:20', 54, 88, 38],['10/25 13:25', 54, 88, 43]," \
       "['10/25 13:30', 78, 88, 48],['10/25 13:35', 89, 88, 48],['10/25 13:40', 89, 88, 53],['10/25 13:45', 89, 89, 53]," \
       "['10/25 13:50', 89, 100, 53],['10/25 13:55', 89, 100, 53],['10/25 14:00', 89, null, 53],['10/25 14:05', 89, null" \
       ", 53],['10/25 14:10', 89, null, 59],['10/25 14:15', 89, null, 59],['10/25 14:20', 89, null, 65],['10/25 14:25', " \
       "100, null, 65],['10/25 14:30', 100, null, 65],['10/25 14:35', null, null, 65],['10/25 14:40', null, null, 65]," \
       "['10/25 14:45', null, null, 71], ['10/25 14:50', null, null, 77],['10/25 14:55', null, null, 77]," \
       "['10/25 15:00', null, null, 89], ['10/25 15:05', null, null, 100],['10/25 15:10', null, null, 100]]"


j_info = data.partition("=")[2].replace("'", '"')
print(j_info)
json1 = json.loads(j_info)
print(json1[0][1])