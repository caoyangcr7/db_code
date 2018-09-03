# -*- coding:utf8 -*-

def get_memberNames_Of_leader(name_of_leader,func_select):

    memberNames_data=[]
    leader_ID_sql = "select ID from group_leader where name_of_memberOrleader='%s'"%(name_of_leader)
    leader_ID = int(func_select(leader_ID_sql)[0][0])
    members_sql = "select name_of_memberOrleader from group_leader where parent_id=%s"%(leader_ID)
    members = func_select(members_sql)
    for member in members:
        memberNames_data.append(member[0])
    return memberNames_data

def get_member_trainItems(name_of_member,start_time,stop_time,func_select):
    sql = "select training_item " \
    "from training_record where name_of_therapists = '%s' " \
    "and (training_time > '%s' and training_time < '%s')" \
    % (name_of_member,start_time, stop_time)
    print sql
    train_item_sql_result = func_select(sql)
    num_of_record = len(train_item_sql_result)
    print num_of_record
    data_of_train_record = [i for j in train_item_sql_result for i in str(j[0]).split('、')]
    print data_of_train_record
    # data_of_train_record is like ['1','2','3','4'] the number means the train_item
    res = {}
    for train_item in data_of_train_record:
        res[train_item]=data_of_train_record.count(train_item)
    return res,num_of_record

    