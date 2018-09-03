# -*-coding:utf8 -*-

from flask import Flask,request
from database_api import MessageToSql,Connect_db
from DBUtils.PooledDB import PooledDB
from MemberAndLeader import get_member_trainItems,get_memberNames_Of_leader
from gevent import monkey
from gevent.pywsgi import WSGIServer
from datetime2json import CJsonEncoder
import json
import MySQLdb
from database_choice import configParse
import pdb


# db_config1 and db_config2, db_config3 are for 3 diffrent databases
db_config1 = configParse('DaZhu')
db_config2 = configParse('exo')
db_config3 = configParse('rds')

server = Flask(__name__)
# create the connection pool of Mysql,then everytime when we need to coonect mysql
# just get the instance using conn = Connect_db() 
pool1= PooledDB(MySQLdb,mincached=2,maxcached=6,**db_config1)
pool2 = PooledDB(MySQLdb,mincached=2,maxcached=6,**db_config2)
pool3 = PooledDB(MySQLdb,mincached=2,maxcached=6,**db_config3)

mts = MessageToSql()


def run_select(the_sql,pool=pool1):
    # execute the sql of select ,return the result (the data of select sql)
    conn = Connect_db(pool)
    try:
         sql_result = conn.run(the_sql)
    except Exception as e:
        raise e
    print sql_result
    return sql_result


def run_not_select(the_sql,pool=pool1):
    # execute the sql of non-select,return the flag tio show whther the sql was
    # executed successfully
    flag=1
    conn = Connect_db(pool)
    try:
        sql_result = conn.run(the_sql)
        print sql_result
        flag = 0
    except Exception as e:
        print e
        raise e
    return flag

# this part is for web

'''WebServer: push data to Web'''
@server.route('/web/<func>', methods=['post', 'get'])
def web(func):
    # function_list = ['information_of_patients_0', 'information_of_patients_1',]
    
    func_new = str(func[0:23])
    if func_new == 'information_of_patients':
        flag_value = str(func).split('_')[3]
        table_name = func_new
        if flag_value=='0':
            sql = mts.get_s_sql(['id_of_admission','name_of_patients','gender','age'],{},
                isdistinct=1,table=table_name)
        else:
            column_name_list = ['gender','age','time_of_visit','time_of_prescribe','name_of_therapists',
            'id_of_admission','id_of_bed','diagnosis','advice_advice']
            sql = mts.get_s_sql(column_name_list,{'id_of_admission':flag_value},table=table_name)
    else:
        table_name = 'None'
        sql = 'None'
    try:
        data = run_select(sql)
    except Exception as e:
        if table_name == 'None':
            data = "Please input correct url"
        else:
            data = "There's something wrong with the server"
            print e
    message = {func:data}
    return json.dumps(message, cls=CJsonEncoder, ensure_ascii=False)

'''WebServer: push v3.6&rehab data to web'''
@server.route('/web_exo/<exo_version>', methods=['post', 'get'])
def exo_data_for_web(exo_version):
    if exo_version == 'steps_of_v3.6':
        table_name = 'v3_6_information'
        try:
            sql = mts.get_s_sql(['total_work_steps'],{},table=table_name)
            sql_result = run_select(sql,pool2)
            sql_result = [ item[0] for item in sql_result ]
            total_steps = int(sum(sql_result))
            temp_step = 0
            with open('./config/v3_data_processing.json') as fp:
                devices_dict = json.load(fp)
                for device in devices_dict['device_id_list']: 
                    temp_step += int(devices_dict['exo_v3_data_' + device]['this_work_steps_temp'])
            steps = total_steps + temp_step 
        except Exception as e:
            print e ,'V3.6计步异常'
            steps = 'None'
    # 测试通过
    elif exo_version == 'motion_times_of_rehab' : 
        table_name = 'rehab_information_new'
        try:
            sql = mts.get_s_sql(['*'],{},table=table_name)
            sql_result = run_select(sql,pool2)
            sql_result = [ item[2:] for item in sql_result]
            total_steps = int(sum(map(lambda x : sum(x),sql_result)))
            
            temp_step = 0
            with open('./config/rehab_count_motion_times.json') as fp:
                devices_dict = json.load(fp)
                for device in devices_dict['device_id_list']: 
                    temp_step += int(devices_dict['exo_rehab_data_' + device]['motion_times_temp'])
            steps = total_steps + temp_step
        except Exception as e:
            print 'rehab统计异常', e
            steps = 'None'
    # 测试通过
    else:
        steps = 'error'
        pass
    message = {exo_version: steps}
    print message
    return json.dumps(message, ensure_ascii=False)
    # 测试通过

'''WebServer: get cloud1.0  Questionnaire data'''
@server.route('/web_Questionnaire/<func>', methods=['post', 'get'])
def web_questionnaire(func):
    func_list = ['tester_info', 'test_content', '10m_test',
                 '6min_test', 'size_of_tester']
    try:
        if func in func_list:
            sql = mts.get_s_sql(['*'],{},table=func)
            data = run_select(sql,pool3)
        else:
            data = 'NOT EXISTED'
    except Exception as e:
        print e
        data = 'Problems in server'
    message = {func : data}
    return json.dumps(message,ensure_ascii=False)
    # 测试通过


'''WebServer: push exo on-line status to web'''

@server.route('/web/exo_status',methods=['post','get'])
def exo_status_for_web():
    try:
        sql = mts.get_s_sql(['version_name', 'status'],{},table = 'status_of_exo')
        sql_result = run_select(sql,pool2)
        data = list(sql_result)
        data = [j for j in data if j[1]=='1'] + [j for j in data if j[1]=='0']
    except Exception as e:
        data = []
        print '状态推送异常',e
    message = { 'exo_status' : data }
    return json.dumps(message,ensure_ascii = False)
    # 测试通过


'''The server to get data of Exo'''
@server.route('/exo/rehab',methods=['post'])
def exo_rehab_new():
    table_name = 'rehab_information_new'
    try:
        device_id = dict_message['device_id']
        with open('./config/rehab_count_motion_times.json') as fp1:
            devices_dict = json.load(fp1)
            dict_message.update(devices_dict['exo_rehab_data_' + device_id])
        if dict_message['train_project_temp'] == dict_message['train_project']:
            print '更新缓存数据'
            try:
                with open('./config/rehab_count_motion_times.json','w') as fp2:
                    devices_dict['exo_rehab_data_' + device_id].update({'motion_times_temp': dict_message['motion_times'],
                                                             'train_time_temp': dict_message['train_time']})
                    json.dump(devices_dict,fp2)
            except Exception as e:
                print '更新数据异常',e
        else:
            print '记录数据'
            try:
                column_name = 'no_' + device_id
                sql = mts.get_s_sql([column_name],{'train_project':dict_message['train_project_temp']},table=table_name)
                data_from_db_old = run_select(sql,pool2)
                try:
                    data_write_to_db = {'train_project': dict_message['train_project_temp'],
                                    column_name: int(dict_message['motion_times_temp'])
                                    + int(data_from_db_old[0][0])}
                    try:
                        # update 步有重复无用代码
                        update_sql = mts.get_u_sql(data_write_to_db,{'train_project':dict_message['train_project_temp']},
                            table=table_name)
                        flag = run_not_select(update_sql,pool2)
                    except Exception as e:
                        print '数据存储异常',e
                except Exception as e:
                    print '数据求和异常',e
            except Exception as e:
                print '数据读取异常',e
            devices_dict['exo_rehab_data_' + device_id].update({'train_project_temp': dict_message['train_project'],
                                                         'train_time_temp': dict_message['train_time'],
                                                         'motion_times_temp': dict_message['motion_times']})
        except Exception as e:
            print e
        return '0'

@server.route('/exo/v3\.6', methods=['post', 'get'])
def exo_v3():
    table_name = 'v3_6_information'
    # this_work_steps = dict_message['this_work_steps']
    # this_work_time = dict_message['this_work_time']
    try:
        with open('./config/v3_count_steps.json') as fp:
            exo_v3_data = json.load(fp)
        if dict_message['device_id'] == exo_v3_data['device_id']:
            exo_v3_data = dict_message  ###???
        else:
            print '切换设备'
            sql = mts.get_s_sql(['device_id, total_work_steps','total_work_time'],
                {'device_id':exo_v3_data['device_id']})
            data_from_db_old = run_select(sql,pool2)
            # update 步有重复无用代码
            data_write_to_db = {'device_id': exo_v3_data['device_id'],
                            'total_work_steps': int(exo_v3_data['this_work_steps'])
                                                + int(data_from_db_old[0][1]),
                            'total_work_time': float(exo_v3_data['this_work_time'])
                                               + int(data_from_db_old[0][2])}
            sql = mts.get_u_sql(data_write_to_db,{'device_id' : exo_v3_data['device_id']},table=table_name)
            flag = run_not_select(sql,pool2)
            exo_v3_data = dict_message
    except Exception as e:
        print e
    message = {'flag': 'kong'}
    return json.dumps(message, ensure_ascii=False)


'''get exo on-line status'''

@server.route('/exo/status', methods=['post'])
def exo_status():
    table_name = 'status_of_exo'
    version_name = dict_message['version_name']
    status = dict_message['status']
    if version_name[0] == 'E':
        device_id = '01000000' + '000001' + version_name[-1]
        version = '3.6版本:'
    elif version_name[0] == 'R':
        device_id = '10121000' + str(version_name).split('o')[1].zfill(6) + '0'
        version = 'rehab版本:'
    else:
        version = '异常'
        device_id = 'None'
    # print version, version_name, '状态为：',status, '设备ID为：', device_id
    para = {'device_id': device_id,
            'version_name': version_name,
            'status': status}
    try:
        sql = mts.get_u_sql(para,{'device_id' : device_id},table = table_name)
        flag = run_not_select(sql,pool2)
    except Exception as e:
        flag = 'error'
        print '在线状态更新异常为', e
    message = {'exo_status': flag}
    return json.dumps(message, ensure_ascii=False)



# this part is for PC

@server.route('/pc/<func>', methods=['post', 'get'])
def pc(func):
    # func_list = ['login', 'register', 'information_of_patients',
    #              'training_record', 'work_items', 'work_time',
    #              'feedback_of_software']
    # get the json data from PC and changed into dictionary
    try:
        data_dict_values = request.values
        dict_message = {}
        for key,value in data_dict_values.items():
            dict_message[key] = value
        pdb.set_trace()
        
    # if there is no post or get data
    except Exception as e:
        print e
    finally:
        pass

    if func == 'register':
        sql = mts.get_i_sql(dict_message,'information_of_therapists')
        flag = run_not_select(sql)
        message = {func:flag}
        # 测试已通过
    elif func== 'check_known_message':
        job_number = dict_message['job_number']
        phone_number = dict_message['phone_number']
        try:
            message_key_list = mts.dict_to_list_for_select(dict_message)
            # print message_key_list
            sql = mts.get_s_sql(['phone_number','job_number'],{'phone_number':phone_number},table='information_of_therapists')
            # print sql,检测正常
            the_fromat_result = mts.info_match_and_inquire(message_key_list,run_select,sql)
            # print the_fromat_result
            # the format_result was a dictionary like[{'key1':'value1','key2':'value2'},]
            if (the_fromat_result[0]['job_number']==job_number and \
                the_fromat_result[0]['phone_number'] == phone_number) :
                flag = 0
        except Exception as e :
            print '找回密码验证异常', e
            flag = 2
        message = {func: flag}
        # 测试已通过
    elif func == 'reset_password':
        value_dict = dict([('password',dict_message['password'])]) 
        condition_dict  = dict([('job_number',dict_message['job_number'])])
        try:
            sql = mts.get_u_sql(value_dict,condition_dict, 'information_of_therapists')
            flag = run_not_select(sql)
        except Exception as e:
            print '重置密码异常',e
        message = {func: flag}
        # 测试已通过
    elif func == 'login':
        try:
            message_key_list = mts.dict_to_list_for_select(dict_message)
            sql = mts.get_s_sql(message_key_list,{'job_number':dict_message['job_number']},table='information_of_therapists')
            the_fromat_result = mts.info_match_and_inquire(message_key_list,run_select,sql)
            if the_fromat_result[0]['password'] == dict_message['password']:
                print 'login succesfully ! '
                flag =0
            else :
                print 'job_number or the password was wrong ! '
            flag =0 if flag==0 else 1
            if flag==0:
                subkey_list =['password_memory','password','login_auto_memory']
                value_dict = dict([(key,dict_message[key]) for key in subkey_list] ) 
                condition_dict  = dict([('job_number',dict_message['job_number'])])
                update_sql = mts.get_u_sql(value_dict,condition_dict, 'information_of_therapists')
                flag =run_not_select(update_sql)
                select_sql = mts.get_s_sql(['*'],condition_dict)
                feedback_data = run_select(select_sql)[0][1:-2]
            else :
                feedback_data = []
        except Exception as e:
            print e
        message = {func: flag,func + 'data': feedback_data}
        # 测试已通过
    elif func == 'information_of_patients':
        if dict_message['query_key']=='name_of_patients':
            sql1 = mts.get_s_sql(['*'],{dict_message['query_key']:dict_message['query_value']},table = 'information_of_patients')
            data_basic = run_select(sql1)
            basic_information = [i[1:] for i in data_basic]
            sql2 = mts.get_s_sql(['*'],{dict_message['query_key']:dict_message['query_value']},table = 'training_record')
            data_of_training =run_select(sql2)
            training_information = [i[1:-1] for i in data_of_training]
        elif dict_message['query_key']=='id_of_bed':
            sql1 = mts.get_s_sql(['*'],{dict_message['query_key']:dict_message['query_value']},table='information_of_patients')
            # here the data_basic was the output of fetchall()
            data_basic = run_select(sql1)
            basic_information = [i[1:] for i in data_basic][-3:]
            name_of_special_bed = [i[0] for i in basic_information]
            training_information_group = []
            for i in name_of_special_bed:
                # print i
                sqli = mts.get_s_sql(['*'],{'name_of_patients':i})
                training_information_i = run_select(sqli)
                training_information_i = [i[1:-1] for i in training_information_i]
                training_information_group.append(training_information_i)
            # training_information = dict(zip(name_of_special_bed, training_information_group))
            training_information = training_information_group
        else:
            basic_information = 'error'
            training_information = 'error'
        message = {func: basic_information,'training_record': training_information}
    # 测试已通过
    elif func == 'training_record':
        sql  = mts.get_i_sql(dict_message,table='training_record')
        flag = run_not_select(sql)
        message = {func:flag}
        # 测试已通过
    elif func == 'feedback_of_software':
        sql  = mts.get_i_sql(dict_message,table='feedback_of_software')
        flag = run_not_select(sql)
        message = {func:flag}
        # 测试已通过
    elif func == 'group_leader': 
        # every time when the leader add new doctor 
        '''delete the message of leader in dict_message {'name_of_leaders': 'bfr',
                'name_of_member_0': '康复师0',
                'name_of_member_1': '康复师1'} '''
        # 去除空值
        for i in dict_message.keys():
            if dict_message[i] == None:
                dict_message.pop(i)
            else:
                pass
        try:
            name_of_leader = dict_message['name_of_leaders']
            # the sql is to check if the leader has existed
            sql = "select count(name_of_memberOrleader) from group_leader where name_of_memberOrleader ='%s' " %(name_of_leader)
            the_num_of_leader = int(run_select(sql)[0][0])
            # print type(the_num_of_leader)
            # the leader dosen't exist
            if the_num_of_leader ==0:
                # print 'yes'
                sql_leader = mts.get_i_sql({'name_of_memberOrleader':name_of_leader})
                flag = run_not_select(sql_leader)
                if flag==0:
                    # print 'yyes'
                    # only insert members if the leader has existed
                    dict_message.pop('name_of_leaders')
                    ID = int(run_select("select ID from group_leader where name_of_memberOrleader='%s'"%(name_of_leader))[0][0])
                    # print ID
                    for value in dict_message.values():
                        sql_member = mts.get_i_sql({'name_of_memberOrleader':value,'parent_id':ID})
                        flag = run_not_select(sql_member)
            # the leader has existed
            else:
                # print 'no'
                ID = int(run_select("select ID from group_leader where name_of_memberOrleader='%s'"%(name_of_leader))[0][0])
                # print ID
                # only insert members
                dict_message.pop('name_of_leaders')
                for value in dict_message.values():
                    sql_member = mts.get_i_sql({'name_of_memberOrleader':value,'parent_id':ID})
                    flag = run_not_select(sql_member)
        except Exception as e:
            print '更新数据异常',e
            flag =1
        message = {func:flag}
        # 测试已通过

    elif func == 'query_group_members':
        try:
            data=get_memberNames_Of_leader(dict_message['name_of_leaders'],run_select)

        except Exception as e:
            print '查询组员异常', e
            data = 'error'
        message = {func:data}
        # message is the form of ['康复师1','康复师2']
        # 测试已通过


    elif func =='all_patients_information':
        try:
            sql = mts.get_s_sql(['*'],{},table='information_of_patients')
            data = run_select(sql)
            data = [i[1:] for i in data]
        except Exception as e:
            print 'all patients information reading error', e
        message = {func: data}
        # 测试已通过
    elif func == 'training_feedback':
        start_time = dict_message['start_time']
        stop_time = dict_message['stop_time']
        job_number = dict_message['job_number']
        try:
            member_name_data=get_memberNames_Of_leader(job_number,run_select)
            # 诊断反馈汇总,job_number是组长工号,受interface_of_pc约束，
            # 此处等于name_of_leaders,返回训练详情

            collection_of_train_record = []
            for i in range(len(member_name_data)):
                data_to_query = member_name_data[i]
                # print data_to_query
                sql = "select name_of_patients, training_time, training_item, advice_of_therapist, name_of_therapists " \
                  "from training_record where name_of_therapists = '%s'" \
                  "and (training_time > '%s' and training_time < '%s')" \
                  % (data_to_query, start_time, stop_time)
                print sql
                try:
                    member_train_result =  run_select(sql)
                    # print member_train_result
                    # if the therapists has training_record,get it 
                    if member_train_result:
                        collection_of_train_record.append(member_train_result)
                        # print collection_of_train_record 
                        # print 'yes'
                except Exception as e:
                    print 'DB error',e
            
            collection_of_train_record = [i for j in collection_of_train_record for i in j]
            data = collection_of_train_record
        # data = mts.collection_of_train_record(dict_message,run_select)
        except Exception as e:
            print '查询组员记录异常',e
            data = 'error'
        message = {func: data}
        #测试已通过
    elif func == 'count_training_item':
        start_time = dict_message['start_time']
        stop_time = dict_message['stop_time']
        job_number = dict_message['job_number']
        try:
            sql = mts.get_s_sql(['name_of_therapists', 'identity_type'],{'job_number':job_number})
          #   sql = "select name_of_therapists, identity_type from information_of_therapists " \
          # "where job_number = '%s'" % job_number
            sql_result = run_select(sql)
            sql_result_format =mts.select_sql_result_format(sql_result,['name_of_therapists', 'identity_type'])
            # print sql_result_format
            # print 'yes'
            # the sql_result_format is the form of [{'name_of_therapists' : xxx,'identity_type':xx}]
            try:
                if sql_result_format[0]['identity_type'] == '组员':
                    train_items_data,num_of_record = get_member_trainItems(sql_result_format[0]['name_of_therapists'],\
                        start_time,stop_time,run_select)

                    message = {'count_training_item': train_items_data,'num_of_training_record': int(num_of_record)}
                if sql_result_format[0]['identity_type'] == '组长':
                    # data_of_train_record is the totally count of every training item for every therapist
                    data_of_train_record=[]
                    # num_of_record is the totally training count of every therapist
                    num_of_record = []
                    member_name_data=get_memberNames_Of_leader(sql_result_format[0]['name_of_therapists'],run_select)
                    # append the name of group_leader
                    member_name_data.append(sql_result_format[0]['name_of_therapists'])
                    for member in member_name_data:
                        sql = "select training_item " \
                        "from training_record where name_of_therapists = '%s' " \
                        "and (training_time > '%s' and training_time < '%s')" \
                        % (member,start_time, stop_time)
                        # print sql
                        train_item_sql_result = run_select(sql)
                        num_of_record.append(len(train_item_sql_result))
                        # print num_of_record
                        single_data_of_train_record = [i for j in train_item_sql_result for i in str(j[0]).split('、')]
                        data_of_train_record += single_data_of_train_record
                    member_name_data[-1] = '组长'

                    res = {}
                    for train_item in data_of_train_record:
                        res[train_item]=data_of_train_record.count(train_item)

                    message = {'num_of_training_record':dict(zip(member_name_data,num_of_record)),\
                    'count_training_item':res}

            except Exception as e:
                print '搜集信息异常',e
                data = {'count_training_item':'error'}
                message =data              
        except Exception as e:
             print '身份识别异常',e
        # 测试已通过
    else:
        message = {'ErrorInfo': 'Please input correct url'}

            # data = mts.count_training_item(dict_message,run_select)
     
    # 测试的时候全是字符型数据，所以不用设置json.dumps()的cls参数，
    #在实际应用中,training_time 是timestamp(时间戳)类型数据，
    # 但由于json不支持此类型数据的序列化，所以必须对时间戳类型数据进行处理
    # 详见datetime2json.py和sever.py相关部分
    print json.dumps(message, ensure_ascii=False,cls=CJsonEncoder)
    return json.dumps(message, ensure_ascii=False,cls = CJsonEncoder)



if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 4399), server)
    http_server.serve_forever()






