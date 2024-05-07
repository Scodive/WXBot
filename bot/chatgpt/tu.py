import requests

def get_text_from_api(api_url):
    try:
        response = requests.get("https://act.jiawei.xin:10086/lib/api/maren.php?catalog=yang")
        if response.status_code == 200:
            return response.text.strip()  # 返回去除首尾空白字符的文本
        else:
            print(f"请求失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"发生异常：{e}")
    return None

# 示例 API URL
api_url = "https://act.jiawei.xin:10086/lib/api/maren.php?catalog=yang"

# 获取文本
text = get_text_from_api(api_url)
if text:
    print("获取到的文本:", text)
else:
    print("获取文本失败")
