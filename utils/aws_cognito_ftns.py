import sys
import boto3
import re
from uuid import UUID
import pandas as pd
from datetime import date, timedelta
from tabulate import tabulate


def is_email_address(string):
    return re.match(r"[^@]+@[^@]+\.[^@]+", string)


def is_uuid(uuid_to_test, version=4):
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test


def find_filter_method(string):
    if is_email_address(string):
        return 'email'
    elif is_uuid(string, version=4):
        return 'uuid'


def get_cognito_id(user_cognito_data):

    for record in user_cognito_data['Attributes']:
        if record['Name'] == "sub":
            return record['Value']


def get_cognito_user(user_list, requested_user):
    """
    :param user_list: result of get_cognito_user_list
    :param by: 'email' or 'uuid'
    :return:
    """
    user_list_dict = build_cognito_user_dict(user_list, by=find_filter_method(requested_user))

    try:
        user_data = user_list_dict[requested_user]
        return user_data
    
    except KeyError:
        print("User not found. Exiting")
        sys.exit(1)


def get_cognito_users_dataframe(user_list, requested_users_list):
    _df = None
    for user in requested_users_list:
        user_cognito_data = get_cognito_user(user_list, user)
        if _df is None:
            _df = user_data_to_dataframe(user_cognito_data)
        else:
            _df = _df.append(user_data_to_dataframe(user_cognito_data))
    return _df


def build_cognito_user_dict(user_list, by):
    """
    :param user_list: result of get_cognito_user_list
    :param by: 'email' or 'uuid'
    :return:
    """
    if by == 'email':
        user_list_dict = {}
        for user in user_list:
            user_list_dict[user['Username']] = user
        return user_list_dict

    elif by == 'uuid':
        user_list_dict = {}
        for user in user_list:
            for attribute in user['Attributes']:
                if attribute['Name'] == 'sub':
                    user_list_dict[attribute['Value']] = user
                    break
        return user_list_dict

    else:
        raise NotImplementedError


def get_cognito_user_list(region_name,pool_name):

    client = boto3.client('cognito-idp',region_name=region_name)

    pool = get_pool_id(region_name,pool_name)

    if not pool:
        print("No participant User Pool found. Speak to one of the Rorys")
        print("Exiting!")
        sys.exit(1)

    response = client.list_users(UserPoolId=pool)
    user_list = response.get("Users")
    page_token = response.get("PaginationToken")

    while page_token:
        response = client.list_users(
            UserPoolId=pool, 
            PaginationToken=page_token
            )
        user_list.extend(response.get("Users"))
        page_token = response.get("PaginationToken")

    return user_list

def get_pool_id(region_name,pool_name):

    client = boto3.client('cognito-idp',region_name=region_name)

    cognito_details = client.list_user_pools(MaxResults=60)

    for user_pool in cognito_details['UserPools']:
        if user_pool['Name'] == pool_name:
            user_pool_id = user_pool['Id']

    return user_pool_id

def get_office_user_list(region_name,pool_name):

    user_list = get_cognito_user_list(region_name,pool_name)

    office_user_list = {}

    for user in user_list:

        for att in user['Attributes']:
            if att['Name'] == "sub":
                cog_id = att['Value']
        
        for att in user['Attributes']:
            if att['Name'] == "custom:arup_office":
                
                if att['Value'] not in office_user_list:
                    office_user_list[att['Value']] = []
                
                office_user_list[att['Value']].append(cog_id)

    offices = office_user_list.keys()
    members_list = office_user_list.values()

    output = []
    for i in range(0,len(offices)):
        office = offices[i]
        members = members_list[i]
        output.append({"office":office,"members": members})

    return output

def get_study_stats(region_name,user_stats,pool_name):

    user_list = get_cognito_user_list(region_name,pool_name)
    office_user_list = get_office_user_list(region_name,pool_name)

    user_count = len(user_list)

    cog_ids = []
    users_data = []
    offices = []
    planners = 0
    for user in user_list:
        cog_id = user['Attributes'][0]['Value']
        user_data = {"user":user['Username'],"signup":user['UserCreateDate']}
        for att in user['Attributes']:
            if att['Name'] == "custom:arup_office":
                offices.append({"office" : att['Value']})
                user_data["office"] = att['Value']
            
            if att['Name'] == "custom:is_transport_planner" and att['Value'] == "true":
                planners = planners + 1

        users_data.append(user_data)

    global_new_user_count = 0
    
    for user in user_stats:
        for office in office_user_list:
            if user['user'] in office['members']:
                if "data" not in office:
                    office['data'] = []
                office['data'].append(user)

    for office in office_user_list:
        
        if "data" in office:
            
            record_count = 0
            trip_count = 0
            
            for record in office['data']:
                trip_count = trip_count + record['trip_count']
                record_count = record_count + record['total_records']

            office.pop('data')

        else:
            trip_count = 0
            record_count = 0
        
        office['trip_count'] = trip_count
        office['record_count'] = record_count

        yesterday = (date.today() - timedelta(1)).timetuple()

        if "new_users_24hr" not in office:
            office['new_users_24hr'] = 0

        for user in user_list:
            creation_date = user['UserCreateDate'].timetuple()
            
            if creation_date > yesterday:
                
                for record in user['Attributes']:
                    if record['Name'] == "sub":
                        cog_id = record['Value']
                
                if cog_id in office['members']:
                    
                    office['new_users_24hr'] = office['new_users_24hr'] + 1
                    global_new_user_count = global_new_user_count + 1

    for office in office_user_list:
        office['User'] = len(office["members"])
        office.pop("members")

    for office in office_user_list:
        if office['office'] == "-1":
            office['office'] = "Unkown office (intrigue)"

    top_office = sorted(office_user_list, key=lambda k: k['new_users_24hr'],reverse=True)

    growth = int(float(global_new_user_count) / len(user_list) * 100.0)

    print("{} new users since yesterday").format(global_new_user_count)

    summary_stats_df = pd.DataFrame(office_user_list)

    summary_stats_df['New users'] = summary_stats_df['new_users_24hr']
    summary_stats_df['Points'] = summary_stats_df['record_count']
    summary_stats_df['Trips'] = summary_stats_df['trip_count']

    output = summary_stats_df.drop(columns=["new_users_24hr","record_count","trip_count"])
    output = output[['office',"Trips","New users"]]

    output = output.sort_values("Trips",ascending=False)

    overall_stats = "```" + tabulate(output, tablefmt="simple", headers="keys",showindex=False) + "```"

    return user_count, global_new_user_count, growth, top_office, overall_stats

def find_new_users_since_yesterday(user_list):

    yesterday = (date.today() - timedelta(1)).timetuple()

    new_user_count = 0
    offices = []

    for user in user_list:

        creation_date = user['UserCreateDate'].timetuple()
        
        if creation_date > yesterday:
            
            new_user_count = new_user_count + 1

            for att in user['Attributes']:
                if att['Name'] == "custom:arup_office":
                    offices.append(att['Value'])

    return new_user_count, offices


def find_percentage_of_verified_users(region_name, pool_name):

    # this is a dummy method to test the integration with AWS Cognito
    # email_verified is an attribute that should exist in all user pools

    user_list = get_cognito_user_list(region_name,pool_name)

    user_count = len(user_list)
    verified_user_count = 0

    for user in user_list:
        for att in user['Attributes']:
            if att['Name'] == "email_verified":
                if att['Value'] == "true":
                    verified_user_count += 1

    verified_user_percentage = (user_count / verified_user_count) * 100

    return user_count, verified_user_percentage


def user_data_to_dataframe(user_cognito_data):
    flat_user_cognito_data = {}

    for key, value in user_cognito_data.items():
        if isinstance(value, list):
            for attribute in value:
                flat_user_cognito_data[attribute['Name']] = attribute['Value']
        else:
            flat_user_cognito_data[key] = value
    return pd.DataFrame(flat_user_cognito_data, index=[0])