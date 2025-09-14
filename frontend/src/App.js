// src/App.js (WebSocket 연동을 위한 구조 변경)
import React, { useState } from 'react';
import './App.css';
import InputPage from './pages/InputPage';
import LoadingPage from './pages/LoadingPage';
import ResultPage from './pages/ResultPage';

function App() {
  const [pageState, setPageState] = useState('input');
  const [resultData, setResultData] = useState(null);
  const [taskId, setTaskId] = useState(null); // <<< 1. task_id를 관리할 state 추가

  const renderPage = () => {
    switch (pageState) {
      case 'loading':
        // <<< 2. LoadingPage에 taskId와 페이지 전환 함수들을 넘겨줌
        return <LoadingPage taskId={taskId} setPageState={setPageState} setResultData={setResultData} />;
      case 'result':
        return <ResultPage data={resultData} />;
      case 'input':
      default:
        // <<< 3. InputPage에는 taskId를 설정하는 함수만 넘겨줌
        return <InputPage setPageState={setPageState} setTaskId={setTaskId} />;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Gemggark: AI 아크그리드 최적화</h1>
      </header>
      {/* <<< className="App-main" 추가 */}
      <main className="App-main">
        {renderPage()}
      </main>
    </div>
  );
  
}

export default App;