// src/pages/LoadingPage.js
import React, { useState, useEffect } from 'react';
import { Box, Typography, LinearProgress } from '@mui/material';

const LoadingPage = ({ taskId, setPageState, setResultData }) => {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('서버에 연결하는 중입니다...');

  useEffect(() => {
    if (!taskId) return;

    // WebSocket 주소 (ws://는 http://와 같고, wss://는 https://와 같습니다)
    const ws = new WebSocket(`ws://localhost:8000/ws/progress/${taskId}`);

    ws.onopen = () => {
      console.log('WebSocket 연결 성공');
      setMessage('작업 상태를 기다리는 중입니다...');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket 메시지 수신:', data);

      // 서버에서 받은 데이터로 상태 업데이트
      setProgress(data.progress || 0);
      setMessage(data.message || '');

      // 작업 완료 시
      if (data.status === 'completed') {
        setResultData(data.result);
        setPageState('result');
        ws.close();
      }

      // 작업 실패 시
      if (data.status === 'failed') {
        alert(`작업 실패: ${data.message}`);
        setPageState('input');
        ws.close();
      }
    };

    ws.onclose = () => {
      console.log('WebSocket 연결 종료');
    };

    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      alert('실시간 연결에 실패했습니다. 페이지를 새로고침 해주세요.');
      setPageState('input');
    };

    // 컴포넌트가 언마운트될 때 WebSocket 연결을 정리합니다.
    return () => {
      if (ws.readyState === 1) { // 연결된 상태일 때만
        ws.close();
      }
    };
  }, [taskId, setPageState, setResultData]); // taskId가 변경될 때만 이 effect를 실행

  return (
    <Box sx={{ width: '80%', margin: 'auto', textAlign: 'center', padding: 4 }}>
      <Typography variant="h6" gutterBottom>
        {message}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', marginTop: 2 }}>
        <Box sx={{ width: '100%', mr: 1 }}>
          <LinearProgress variant="determinate" value={progress} />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">{`${Math.round(progress)}%`}</Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default LoadingPage;