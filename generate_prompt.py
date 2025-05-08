import requests, json

url = 'http://192.168.8.230:3000/api/chat/completions'
token = "sk-6f93f7852a0e42c8a12aaabf5f959e6f"
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}


def gen_prompt(keyword):
    data = {
        "model": "海报生成器《简洁版》",
        "messages": [
            {
                "role": "user",
                "content": keyword
            }
        ], "stream": True
    }
    models_res = requests.post(url, headers=headers, json=data, stream=True)
    prompt = ''
    for i in models_res.iter_lines():
        chunk = i.decode('utf-8')
        if chunk.startswith('data:'):
            chunk = chunk.replace('data: ', '')
            res_dict = json.loads(chunk)
            try:
                prompt += res_dict['choices'][0]['delta']['content']
                yield res_dict['choices'][0]['delta']['content']

            except:
                break


