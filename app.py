from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
from dotenv import load_dotenv
import openai

from uuid import uuid4
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.schema import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# .env 파일 로드
load_dotenv()

app = Flask(__name__)

def is_valid_api_key(api_key):
    """OpenAI API 키의 유효성을 검사합니다."""
    try:
        client = openai.OpenAI(api_key=api_key)
        client.models.list()
        return True
    except:
        return False

def create_custom_prompt(system_prompt):
    """사용자 정의 시스템 프롬프트로 ChatPromptTemplate 생성"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    return prompt

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate_api_key', methods=['POST'])
def validate_api_key():
    data = request.get_json()
    api_key = data.get('api_key')
    
    if is_valid_api_key(api_key):
        return jsonify({'valid': True})
    else:
        return jsonify({'valid': False})

@app.route('/compare', methods=['POST'])
def compare_responses():
    data = request.get_json()
    api_key = data.get('api_key')
    user_input = data.get('user_input')
    
    # 오늘 날짜 가져오기
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 한글 시스템 프롬프트 (고정)
    system_prompt = f"""당신은 웹 검색 기능을 가진 최고의 AI 어시스턴트입니다. 오늘은 {today}입니다.
사용자의 질문에 답할 때는 다음 지침을 따르세요:

1. 질문을 분석하여 가장 효과적인 검색 쿼리를 작성하세요. 여러 각도에서 검색이 필요하면 다양한 키워드를 활용하세요.
2. 최신 정보가 필요한 질문의 경우 반드시 웹 검색을 활용하여 정확하고 최신의 정보를 제공하세요.
3. 검색 결과를 종합적으로 분석하여 한국어로 자세하고 유용한 답변을 작성하세요.
4. 불확실한 정보는 추측하지 말고 반드시 검색을 통해 확인하세요 참고한 링크를 답변에 함께 알려주면 더 좋습니다.
5. 검색 쿼리를 작성할 때는 다음을 고려하세요:
   - 핵심 키워드 식별
   - 시간 관련 키워드 (최신, 2024, 현재 등)
   - 구체적인 용어와 일반적인 용어 조합
   - 한국어와 영어 키워드 모두 고려"""
    
    if not api_key or not is_valid_api_key(api_key):
        return jsonify({'error': 'Invalid API key'}), 400
    
    if not user_input:
        return jsonify({'error': 'User input is required'}), 400
    
    try:
        # OpenAI API 키 설정
        os.environ["OPENAI_API_KEY"] = api_key
        
        # LLM 모델 초기화
        llm = ChatOpenAI(model='gpt-4.1-mini', temperature=0)
        
        # 일반 LLM 응답 (날짜 정보 포함)
        llm_prompt = f"오늘은 {today}입니다. 다음 질문에 답해주세요: {user_input}"
        llm_response = llm.invoke([HumanMessage(content=llm_prompt)])
        
        # Agent 초기화 (DuckDuckGoSearchResults 사용)
        # max_results를 조정하여 더 많은 검색 결과를 받을 수 있습니다
        search_tool = DuckDuckGoSearchResults(max_results=5)
        tools = [search_tool]
        llm_with_tools = llm.bind_tools(tools)
        prompt = create_custom_prompt(system_prompt)

        runnable_agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
            }
            | prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )

        agent_executor = AgentExecutor(
            agent=runnable_agent,
            tools=tools,
            handle_parsing_errors=True
        )
        
        # Agent 응답
        agent_response = agent_executor.invoke({"input": user_input})
        
        return jsonify({
            'llm_response': llm_response.content,
            'agent_response': agent_response['output']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)