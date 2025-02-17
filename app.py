from flask import Flask, render_template, request, jsonify
import json
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # 讀取 .env 檔案
app = Flask(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=OPENAI_API_KEY)  # 正確初始化 OpenAI 客戶端

if not OPENAI_API_KEY:
    raise ValueError("❌ 環境變數 `OPENAI_API_KEY` 未設定，請在系統中設定 API Key！")


# 載入籤詩數據
with open('data/fortunes.json', 'r', encoding='utf-8') as f:
    fortunes_data = json.load(f)

def validate_question(question, fortune):
    """使用 OpenAI 驗證問題是否與運勢相關"""
    prompt = f"""
    請判斷以下問題是否與抽到的籤詩和個人運勢相關。
    籤詩內容：{fortune['content']}
    問題：{question}
    
    只回答 '相關' 或 '不相關'。
    如果問題是關於天氣、新聞等與個人運勢無關的話題，請回答'不相關'。
    """
    
    response = client.chat.completions.create(
    model="gpt-4o-mini-2024-07-18",
    messages=[
        {"role": "system", "content": "你是一個專業的解籤師。"},
        {"role": "user", "content": prompt}
    ]
)
    
    result = response.choices[0].message.content.strip()
    return result == "相關"

def interpret_fortune(question, fortune, name, birthday):
    """使用 OpenAI 解釋籤詩"""
    # 解析生日
    date_parts = birthday.split(' ')
    birth_date = date_parts[0]
    
    
    prompt = f"""
    作為專業解籤師，請根據以下信息為求籤者解答：

    求籤者資料：
    姓名：{name}
    生辰：{birth_date} 
    
    抽到的籤詩：
    {fortune['title']}
    {fortune['content']}
    
    籤詩基本解釋：
    {fortune['explanation']}
    
    求籤者的問題：
    {question}
    
    請提供完整解籤分析：
    1. 籤詩與求籤者的資料（考慮姓名及出生年月日）
    2. 籤詩對當前問題的指引
    3. 近期運勢分析和建議
    4. 化解方法和開運建議（根據籤詩及姓名及出生年月日）
    
    請以專業廟宇解籤師的身份回答，給予詳細且積極正面的指導。回答時要考慮：
    - 姓名及出生年月日
    - 當前時節與運勢
    - 籤詩暗示的吉凶
    - 具體可行的建議
    - 僅針對提的問題回答，不要延伸其他問題
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "system", "content": "你是一位經驗豐富的廟宇解籤師，籤詩解讀與人生指導。"},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html', fortunes=fortunes_data['籤詩'])

@app.route('/interpret', methods=['POST'])
def get_interpretation():
    data = request.json
    name = data.get('name')
    birthday = data.get('birthday')
    fortune_id = int(data.get('fortune_id'))
    question = data.get('question')
    
    # 找到選擇的籤詩
    fortune = next((f for f in fortunes_data['籤詩'] if f['id'] == fortune_id), None)
    
    if not fortune:
        return jsonify({'error': '無效的籤詩ID'}), 400
        
    # 驗證問題是否相關
    if not validate_question(question, fortune):
        return jsonify({'error': '您的問題與運勢無關，請重新提問'}), 400
    
    # 解釋籤詩，加入姓名和生日資訊
    interpretation = interpret_fortune(question, fortune, name, birthday)
    
    return jsonify({
        'interpretation': interpretation,
        'fortune': fortune
    })

if __name__ == '__main__':
    app.run(debug=True) 