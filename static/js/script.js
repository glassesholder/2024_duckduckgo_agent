document.addEventListener('DOMContentLoaded', function() {
    const apiKeyInput = document.getElementById('apiKey');
    const apiKeyStatus = document.getElementById('apiKeyStatus');
    const validateBtn = document.getElementById('validateBtn');
    const userInput = document.getElementById('userInput');
    const compareBtn = document.getElementById('compareBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');
    const llmResponse = document.getElementById('llmResponse');
    const agentResponse = document.getElementById('agentResponse');
    const errorMessage = document.getElementById('errorMessage');

    let isValidApiKey = false;

    // API 키 입력 시 검증 버튼 활성화
    apiKeyInput.addEventListener('input', function() {
        const apiKey = apiKeyInput.value.trim();
        validateBtn.disabled = !apiKey;
        
        if (!apiKey) {
            apiKeyStatus.textContent = '';
            apiKeyStatus.className = 'status-message';
            isValidApiKey = false;
            updateCompareButton();
        }
    });

    // API 키 검증 버튼 클릭
    validateBtn.addEventListener('click', async function() {
        const apiKey = apiKeyInput.value.trim();
        
        if (!apiKey) {
            showError('API 키를 입력해주세요.');
            return;
        }

        // 버튼 상태 변경
        validateBtn.disabled = true;
        validateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 검증 중...';
        
        try {
            const response = await fetch('/validate_api_key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ api_key: apiKey })
            });

            const result = await response.json();
            
            if (result.valid) {
                apiKeyStatus.textContent = '✅ 유효한 API 키입니다!';
                apiKeyStatus.className = 'status-message success';
                validateBtn.innerHTML = '<i class="fas fa-check"></i> 검증 완료';
                validateBtn.style.background = 'linear-gradient(135deg, #4caf50 0%, #388e3c 100%)';
                isValidApiKey = true;
            } else {
                apiKeyStatus.textContent = '❌ 올바르지 않은 API 키입니다. 다시 확인해주세요.';
                apiKeyStatus.className = 'status-message error';
                validateBtn.innerHTML = '<i class="fas fa-times"></i> 실패';
                validateBtn.style.background = 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)';
                isValidApiKey = false;
                validateBtn.disabled = false;
            }
        } catch (error) {
            apiKeyStatus.textContent = '❌ API 키 검증 중 오류가 발생했습니다.';
            apiKeyStatus.className = 'status-message error';
            validateBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 오류';
            validateBtn.style.background = 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)';
            isValidApiKey = false;
            validateBtn.disabled = false;
        }

        updateCompareButton();
    });

    // 사용자 입력 변경 시 버튼 상태 업데이트
    userInput.addEventListener('input', updateCompareButton);

    function updateCompareButton() {
        const hasInput = userInput.value.trim().length > 0;
        compareBtn.disabled = !isValidApiKey || !hasInput;
    }

    // 답변 비교 버튼 클릭
    compareBtn.addEventListener('click', async function() {
        const apiKey = apiKeyInput.value.trim();
        const userQuestion = userInput.value.trim();

        if (!apiKey || !userQuestion) {
            showError('API 키와 질문을 모두 입력해주세요.');
            return;
        }

        // UI 상태 업데이트
        hideError();
        hideResults();
        showLoading();
        compareBtn.disabled = true;

        try {
            const response = await fetch('/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    api_key: apiKey,
                    user_input: userQuestion
                })
            });

            const result = await response.json();

            if (response.ok) {
                displayResults(result.llm_response, result.agent_response);
            } else {
                showError(result.error || '답변 생성 중 오류가 발생했습니다.');
            }
        } catch (error) {
            showError('서버와의 통신 중 오류가 발생했습니다: ' + error.message);
        } finally {
            hideLoading();
            updateCompareButton();
        }
    });

    function showLoading() {
        loadingIndicator.style.display = 'block';
    }

    function hideLoading() {
        loadingIndicator.style.display = 'none';
    }

    function showResults() {
        resultsSection.style.display = 'block';
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function displayResults(llmText, agentText) {
        llmResponse.innerHTML = formatResponse(llmText);
        agentResponse.innerHTML = formatResponse(agentText);
        showResults();
    }

    function formatResponse(text) {
        // 텍스트를 HTML로 변환 (줄바꿈을 <br>로, 링크를 클릭 가능하게)
        return text
            .replace(/\n/g, '<br>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    // 초기 버튼 상태 설정
    updateCompareButton();
    validateBtn.disabled = true;
});
