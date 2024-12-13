import streamlit as st
import os
from dotenv import load_dotenv

from uuid import uuid4
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.schema import HumanMessage

# 페이지 설정 (반드시 첫 번째로 호출)
st.set_page_config(
    page_title="LLM vs 덕덕고 Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# .env 파일 로드
load_dotenv()

# CSS 스타일 정의
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        margin-top: 1rem;
    }
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #FF4B4B;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
        border: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# 제목과 설명
st.title("🤖 LLM vs 덕덕고 Agent 🦆")
st.markdown("""
    <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h4>🎯 이 앱은 일반 LLM과 검색 기능이 있는 덕덕고 Agent의 답변을 비교해볼 수 있습니다.</h4>
        <p>왼쪽은 일반 LLM의 답변이고, 오른쪽은 실시간 웹 검색이 가능한 덕덕고 Agent의 답변입니다.</p>
    </div>
""", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password", help="OpenAI API 키를 입력해주세요")
    os.environ["OPENAI_API_KEY"] = api_key

# 개별 고유 ID
# unique_id = uuid4().hex[0:8]

if api_key:
    # LLM 모델 초기화
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    
    # Agent 초기화
    tool = DuckDuckGoSearchRun()
    tools = [tool]
    llm_with_tools = llm.bind_tools(tools)
    prompt = hub.pull('wfh/langsmith-agent-prompt:5d466cbc')

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

    # 사용자 입력
    user_input = st.text_area("💭 질문을 입력하세요:", height=100, 
                             placeholder="예: 2024년 AIDT 도입 과목을 알려줄 수 있어?")

    if st.button("🚀 답변 받기"):
        if user_input:
            # 두 개의 컬럼 생성
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🤖 LLM 답변")
                with st.spinner("LLM이 답변을 생성 중..."):
                    llm_response = llm([HumanMessage(content=user_input)])
                    st.markdown(f"""
                        <div class="response-box">
                            {llm_response.content}
                        </div>
                    """, unsafe_allow_html=True)

            with col2:
                st.markdown("### 🦆 덕덕고 Agent 답변")
                with st.spinner("덕덕고 Agent가 검색하며 답변을 생성 중..."):
                    agent_response = agent_executor.invoke({"input": user_input})
                    st.markdown(f"""
                        <div class="response-box">
                            {agent_response['output']}
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ 질문을 입력해주세요.")
else:
    st.warning("⚠️ OpenAI API 키를 입력해주세요.")
