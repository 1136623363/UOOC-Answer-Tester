import json
import requests
from itertools import product

course_id = 11111111 #此处填入课程编号cid
Authorization= 'Bearer xxxxxx' #此处改为你的登录令牌，需要通过手机app的优课联盟抓包获取

burp0_headers = {
    "xgTokenFlag": "",
    "versionFlag": "v2.0.3",
    "machineFlag": "",
    "productFlag": "OnePlus PJA110 13",
    "sourceFlag": "android",
    "Authorization": Authorization,
    "User-Agent": "UoocOnline Android v2.0.3",
    "Connection": "close",
    "Accept-Encoding": "gzip, deflate"
}

def extract_ids(data):#递归提取所有catalog_id
    ids = []
    if isinstance(data, list):
        for item in data:
            ids.extend(extract_ids(item))
    elif isinstance(data, dict):
        if 'id' in data:
            ids.append(data['id'])
        for key, value in data.items():
            ids.extend(extract_ids(value))
    return ids

def get_catalog_id(course_id):
    burp0_url = f"http://www.uooconline.com:80/home/learn/getCatalogList?cid={course_id}"
    resp = requests.get(burp0_url, headers=burp0_headers)
    CatalogList = json.loads(resp.text)['data']
    # catalog_id_list = [i["children"][-1]["id"] if i.get("children") else None for i in CatalogList]
    catalog_id_list=extract_ids(CatalogList)
    print(f'章节catalog_id: {catalog_id_list}')
    return catalog_id_list

def get_task_id(course_id,catalog_id):
    # catalog_id = 397705352
    burp0_url = f"http://www.uooconline.com:80/home/learn/getUnitLearn?cid={course_id}&catalog_id={catalog_id}"
    resp = json.loads(requests.get(burp0_url, headers=burp0_headers).text)
    # print(resp)
    data = resp['data'] if resp.get('data') else ''
    task_id_list = [i["task_id"] if i.get('task_id') and i["task_id"]!=0 else None for i in data]
    # if task_id_list:
    #     print(task_id_list)
    return task_id_list

def get_qid(task_id):

    burp0_url = f"http://www.uooconline.com:80/exam/getTaskPaper?tid={task_id}"
    resp = requests.get(burp0_url, headers=burp0_headers)
    # print(json.loads(resp.text))
    if json.loads(resp.text)['code'] != 600:
        questions = json.loads(resp.text)['data']['questions']
        # print(questions)
        answer = [{'answer': [''], 'qid': i['id']} for i in questions]
        options = [list(i['options'].keys()) for i in questions]
        type = [int(i['type']) for i in questions]
        return answer,options,type
    print(json.loads(resp.text))
    return None,None,None

def guess_ans(course_id,task_id):
    burp0_url = "http://www.uooconline.com:80/exam/commit"
    answer,options,type =  get_qid(task_id)
    # print(answer,options,type)

    if answer:
        for i in range(len(answer)):
            if type[i] == 10:#单选题
                for j  in options[i]:#
                    burp0_data = {
                        "cid": course_id,
                        "tid": task_id,
                        "data": json.dumps([{'answer': [j], 'qid': answer[i]["qid"]}])
                    }
                    print(burp0_data)
                    resp = requests.post(burp0_url, headers=burp0_headers, data=burp0_data)
                    if json.loads(resp.text)['data']['score'] != 0:
                        answer[i]['answer'] = [j]
                        break
                    print(json.loads(resp.text))
            elif type[i] != 10:#多选题或判断题

                all_combinations = list(product([0, 1], repeat=len(options[i])))
                # 打印所有可能的组合
                for combination in all_combinations:
                    result = [options[i][j] for j in range(len(options[i])) if combination[j] == 1]

                    burp0_data = {
                        "cid": course_id,
                        "tid": task_id,
                        "data": json.dumps([{'answer': result, 'qid': answer[i]["qid"]}])
                    }
                    print(burp0_data)
                    resp = requests.post(burp0_url, headers=burp0_headers, data=burp0_data)
                    if json.loads(resp.text)['data']['score'] != 0:
                        answer[i]['answer'] = result
                        break

        print(answer)
        burp0_data = {
                    "cid": course_id,
                    "tid": task_id,
                    "data": json.dumps(answer)
        }
        resp = requests.post(burp0_url, headers=burp0_headers, data=burp0_data)
        print(json.loads(resp.text))

if __name__ == '__main__':

    catalog_id_list = get_catalog_id(course_id)
    task_id_list=[]
    for i in catalog_id_list:
        task_ids = get_task_id(course_id,i)
        if task_ids :
            task_id_list.append(task_ids)
        else:
            break
    # print(task_id_list)

    valid_task_id_list = [item for sublist in task_id_list if sublist for item in sublist if item is not None]#提取有效task_id

    print(f"\n有效的task_id:{valid_task_id_list}")
    if valid_task_id_list:
        for task_id in valid_task_id_list:
            if task_id !=0:
                guess_ans(course_id,task_id)

    print('目前无可做测验')
