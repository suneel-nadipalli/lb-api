from datetime import datetime

import pytz, sys, re

sys.path.append("..")

edt = pytz.timezone('America/New_York')

def get_time_txt():
    now = datetime.now(edt)

    formatted_date = now.strftime('%d %B %Y %I:%M %p').lstrip('0').replace(' 0', ' ')

    return formatted_date

def get_time_csv():
    now = datetime.now(edt)

    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    
    return formatted_date

def format_rag_resp(res_json):
    try:    

        answer = re.sub(r'\[doc\d+\]', '', res_json['reply'])

        src_dict = {}
        
        for doc in res_json['documents']:
            try:
                src_dict[doc['url']] += doc['score']
            except:
                src_dict[doc['url']] = doc['score']

        src_dict = {
            k.replace(".pdf", ""): round(v,2) 
            for k, v in sorted(src_dict.items(), 
            key=lambda item: item[1], 
            reverse=True)}
        
        srcs = []
        
        for k, v in src_dict.items():
            srcs.append(
                {
                    "source": k,
                    "score": v
                }
            )
        
        return answer, srcs
    except Exception as error:
        
        answer = error.read().decode("utf8", 'ignore')
        
        print("The request failed with status code: " + str(error.code))
        
        print(error.info())
        
        print(error.read().decode("utf8", 'ignore')) 

        return answer, []