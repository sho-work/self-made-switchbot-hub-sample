import React, { useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [status, setStatus] = useState('待機中');
  const [message, setMessage] = useState('');
  const [lastRecognition, setLastRecognition] = useState(null);
  const [serverStatus, setServerStatus] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const recognitionIntervalRef = useRef(null);

  // サーバーステータスの取得
  useEffect(() => {
    const checkServerStatus = async () => {
      try {
        const response = await axios.get('/api/status');
        setServerStatus(response.data);
      } catch (error) {
        console.error('サーバーステータスの取得に失敗:', error);
        setServerStatus({ status: 'error', known_faces_count: 0 });
      }
    };

    checkServerStatus();
    const interval = setInterval(checkServerStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // カメラの起動
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }

      setStatus('カメラ起動中');
      setMessage('');
    } catch (error) {
      console.error('カメラの起動に失敗:', error);
      setStatus('エラー');
      setMessage('カメラにアクセスできません。権限を確認してください。');
    }
  };

  // カメラの停止
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setStatus('待機中');
  };

  // 画像をキャプチャしてBase64に変換
  const captureImage = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL('image/jpeg', 0.8);
  }, []);

  // 顔認証の実行
  const recognizeFace = useCallback(async () => {
    const imageData = captureImage();
    if (!imageData) return;

    try {
      const response = await axios.post('/api/face_recognition', {
        image_data: imageData
      });

      const data = response.data;
      setLastRecognition(data);

      if (data.recognized) {
        setStatus('認証成功');
        setMessage(`${data.name} として認証されました (信頼度: ${(data.confidence * 100).toFixed(1)}%)`);

        // 認証成功後、5秒間は再認証しない
        if (recognitionIntervalRef.current) {
          clearInterval(recognitionIntervalRef.current);
          recognitionIntervalRef.current = null;
        }

        setTimeout(() => {
          if (isRecognizing) {
            // 5秒後に再度認証を開始
            recognitionIntervalRef.current = setInterval(() => {
              recognizeFace();
            }, 1000);
          }
        }, 5000);
      } else {
        setStatus('認証中');
        setMessage(data.message);
      }
    } catch (error) {
      console.error('認証エラー:', error);
      setStatus('エラー');
      setMessage('認証処理でエラーが発生しました');
    }
  }, [captureImage, isRecognizing]);

  // 顔認証の開始/停止
  const toggleRecognition = () => {
    if (isRecognizing) {
      // 停止
      if (recognitionIntervalRef.current) {
        clearInterval(recognitionIntervalRef.current);
        recognitionIntervalRef.current = null;
      }
      stopCamera();
      setIsRecognizing(false);
      setStatus('待機中');
      setMessage('');
    } else {
      // 開始
      startCamera();
      setIsRecognizing(true);
      setStatus('認証中');

      // 1秒ごとに認証を実行
      setTimeout(() => {
        recognitionIntervalRef.current = setInterval(() => {
          recognizeFace();
        }, 1000);
      }, 1000);
    }
  };

  // コンポーネントのアンマウント時にクリーンアップ
  useEffect(() => {
    return () => {
      if (recognitionIntervalRef.current) {
        clearInterval(recognitionIntervalRef.current);
      }
      stopCamera();
    };
  }, []);

  // 手動でSwitchBotを操作
  const pressSwitchBot = async () => {
    try {
      const response = await axios.post('/api/switch_bot/press', {
        action: 'press'
      });

      if (response.data.success) {
        setMessage('SwitchBotを動作させました');
      } else {
        setMessage('SwitchBotの動作に失敗しました');
      }
    } catch (error) {
      console.error('SwitchBot操作エラー:', error);
      setMessage('SwitchBotの操作でエラーが発生しました');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>顔認証システム</h1>
        {serverStatus && (
          <div className="server-status">
            サーバーステータス: {serverStatus.status === 'running' ? '稼働中' : 'エラー'} |
            登録済み顔データ: {serverStatus.known_faces_count}件
          </div>
        )}
      </header>

      <main className="app-main">
        <div className="video-container">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="video-feed"
          />
          <canvas
            ref={canvasRef}
            style={{ display: 'none' }}
          />
          {isRecognizing && (
            <div className="recognition-overlay">
              <div className="scanning-animation"></div>
            </div>
          )}
        </div>

        <div className="status-container">
          <div className={`status ${status === '認証成功' ? 'success' : status === 'エラー' ? 'error' : ''}`}>
            ステータス: {status}
          </div>
          {message && (
            <div className="message">{message}</div>
          )}
          {lastRecognition && lastRecognition.recognized && (
            <div className="recognition-details">
              <p>認証者: {lastRecognition.name}</p>
              <p>信頼度: {(lastRecognition.confidence * 100).toFixed(1)}%</p>
            </div>
          )}
        </div>

        <div className="controls">
          <button
            onClick={toggleRecognition}
            className={`btn ${isRecognizing ? 'btn-stop' : 'btn-start'}`}
          >
            {isRecognizing ? '認証を停止' : '認証を開始'}
          </button>

          <button
            onClick={pressSwitchBot}
            className="btn btn-secondary"
            disabled={isRecognizing}
          >
            手動でSwitchBotを操作
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;