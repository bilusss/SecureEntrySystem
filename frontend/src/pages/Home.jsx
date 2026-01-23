import { useState, useRef, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Webcam from 'react-webcam';
import jsQR from 'jsqr';
import { entriesApi } from '../services/api';

const Home = () => {
  const [mode, setMode] = useState('qr'); // 'qr' | 'face'
  const [qrCodePayload, setQrCodePayload] = useState(null);
  const [statusMessage, setStatusMessage] = useState('Pokaż kod QR do kamery...');
  const [statusType, setStatusType] = useState('info'); // 'info' | 'success' | 'error'
  const [isProcessing, setIsProcessing] = useState(false);
  const [manualQrInput, setManualQrInput] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);
  const webcamRef = useRef(null);
  const timerRef = useRef(null);
  const scanIntervalRef = useRef(null);

  const videoConstraints = {
    width: 640,
    height: 480,
    facingMode: 'user',
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (scanIntervalRef.current) clearInterval(scanIntervalRef.current);
    };
  }, []);

  // Automatyczne skanowanie QR co 200ms gdy w trybie 'qr'
  useEffect(() => {
    if (mode !== 'qr') {
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
        scanIntervalRef.current = null;
      }
      return;
    }

    scanIntervalRef.current = setInterval(() => {
      if (!webcamRef.current) return;
      
      const video = webcamRef.current.video;
      if (!video || video.readyState !== 4) return;

      // Stwórz canvas do analizy obrazu
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imageData.data, imageData.width, imageData.height);
      
      if (code && code.data) {
        // Znaleziono QR!
        console.log('QR detected:', code.data);
        handleQrInput(code.data);
      }
    }, 200);

    return () => {
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
      }
    };
  }, [mode]);

  // Funkcja do przechwycenia zdjęcia z kamery jako Blob
  const capturePhoto = useCallback(() => {
    if (!webcamRef.current) return null;
    
    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return null;
    
    // Konwertuj base64 na Blob
    const byteString = atob(imageSrc.split(',')[1]);
    const mimeString = imageSrc.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
  }, []);

  // Obsługa wprowadzenia kodu QR
  const handleQrInput = useCallback((payload) => {
    if (!payload || payload.trim() === '') {
      setStatusMessage('Kod QR jest pusty');
      setStatusType('error');
      return;
    }

    // Walidacja formatu: employee_id:token
    if (!payload.includes(':')) {
      setStatusMessage('Nieprawidłowy format kodu QR');
      setStatusType('error');
      return;
    }

    // Zatrzymaj skanowanie
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }

    setQrCodePayload(payload);
    setStatusMessage('✅ Kod QR odczytany! Teraz spójrz w kamerę...');
    setStatusType('success');
    setMode('face');

    // Timer 15 sekund na weryfikację twarzy
    timerRef.current = setTimeout(() => {
      setStatusMessage('Czas minął - nie udało się zweryfikować twarzy. Spróbuj ponownie.');
      setStatusType('error');
      setTimeout(() => {
        resetToQrScan();
      }, 3000);
    }, 15000);
  }, []);

  // Weryfikacja wejścia - wysłanie do backendu
  const handleVerifyEntry = useCallback(async () => {
    if (!qrCodePayload) {
      setStatusMessage('Brak kodu QR');
      setStatusType('error');
      return;
    }

    setIsProcessing(true);
    setStatusMessage('Weryfikacja twarzy w toku...');
    setStatusType('info');

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    try {
      const photoBlob = capturePhoto();
      if (!photoBlob) {
        throw new Error('Nie udało się przechwycić zdjęcia z kamery');
      }

      await entriesApi.verifyEntry(qrCodePayload, photoBlob);
      
      setStatusMessage('✅ DOSTĘP PRZYZNANY! Witaj w pracy.');
      setStatusType('success');
      
      setTimeout(() => {
        resetToQrScan();
      }, 5000);

    } catch (err) {
      console.error('Błąd weryfikacji:', err);
      setStatusMessage(`❌ ODMOWA DOSTĘPU: ${err.message || 'Nieznany błąd'}`);
      setStatusType('error');
      
      setTimeout(() => {
        resetToQrScan();
      }, 5000);
    } finally {
      setIsProcessing(false);
    }
  }, [qrCodePayload, capturePhoto]);

  const resetToQrScan = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (scanIntervalRef.current) clearInterval(scanIntervalRef.current);
    
    setMode('qr');
    setQrCodePayload(null);
    setStatusMessage('Pokaż kod QR do kamery...');
    setStatusType('info');
    setManualQrInput('');
    setIsProcessing(false);
  }, []);

  const handleManualQrSubmit = (e) => {
    e.preventDefault();
    handleQrInput(manualQrInput);
    setShowManualInput(false);
  };

  const getStatusColor = () => {
    switch (statusType) {
      case 'success': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
      case 'error': return 'bg-red-500/20 text-red-400 border-red-500/50';
      default: return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-emerald-400">
            🔐 SecureEntrySystem
          </h1>
          <Link
            to="/admin"
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors font-medium"
          >
            Panel Admina
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Status Bar */}
          <div className="mb-6 text-center">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
              mode === 'qr' 
                ? 'bg-blue-500/20 text-blue-400' 
                : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              <span className="relative flex h-3 w-3">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  mode === 'qr' ? 'bg-blue-400' : 'bg-emerald-400'
                }`}></span>
                <span className={`relative inline-flex rounded-full h-3 w-3 ${
                  mode === 'qr' ? 'bg-blue-500' : 'bg-emerald-500'
                }`}></span>
              </span>
              {mode === 'qr' ? 'Krok 1: Pokaż kod QR' : 'Krok 2: Weryfikacja twarzy'}
            </div>
          </div>

          {/* Camera View */}
          <div className="relative bg-slate-800 rounded-2xl overflow-hidden shadow-2xl border border-slate-700">
            <div className="aspect-video relative">
              <Webcam
                ref={webcamRef}
                audio={false}
                videoConstraints={videoConstraints}
                className="w-full h-full object-cover"
                screenshotFormat="image/jpeg"
              />
              
              {/* QR Scan Overlay */}
              {mode === 'qr' && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    {/* QR frame */}
                    <div className="w-64 h-64 border-4 border-blue-400 rounded-lg relative">
                      {/* Corner markers */}
                      <div className="absolute -top-1 -left-1 w-8 h-8 border-t-4 border-l-4 border-blue-400 rounded-tl-lg"></div>
                      <div className="absolute -top-1 -right-1 w-8 h-8 border-t-4 border-r-4 border-blue-400 rounded-tr-lg"></div>
                      <div className="absolute -bottom-1 -left-1 w-8 h-8 border-b-4 border-l-4 border-blue-400 rounded-bl-lg"></div>
                      <div className="absolute -bottom-1 -right-1 w-8 h-8 border-b-4 border-r-4 border-blue-400 rounded-br-lg"></div>
                      
                      {/* Scan line animation */}
                      <div className="absolute top-0 left-0 right-0 h-1 bg-blue-400 animate-pulse"></div>
                    </div>
                    <p className="mt-4 text-blue-300 text-center font-medium">
                      📱 Pokaż kod QR do kamery
                    </p>
                  </div>
                </div>
              )}
              
              {/* Face Verification Overlay */}
              {mode === 'face' && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-64 h-80 border-4 border-emerald-400 rounded-full opacity-70 animate-pulse flex items-center justify-center">
                    <span className="text-emerald-400 text-sm text-center px-4">
                      👤 Ustaw twarz w ramce
                    </span>
                  </div>
                </div>
              )}

              {/* Processing Overlay */}
              {isProcessing && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-4 border-emerald-400 border-t-transparent mx-auto mb-4"></div>
                    <p className="text-white text-lg">Weryfikuję...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Status Message */}
            {statusMessage && (
              <div className={`p-4 text-center border-t ${getStatusColor()}`}>
                <p className="text-lg font-medium">{statusMessage}</p>
              </div>
            )}
          </div>

          {/* Face Verification Buttons */}
          {mode === 'face' && (
            <div className="mt-6 flex gap-4 justify-center">
              <button
                onClick={handleVerifyEntry}
                disabled={isProcessing}
                className="px-8 py-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-800 disabled:cursor-not-allowed rounded-xl font-bold text-lg transition-colors flex items-center gap-2 shadow-lg"
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                    Weryfikacja...
                  </>
                ) : (
                  <>✅ ZWERYFIKUJ TWARZ</>
                )}
              </button>
              <button
                onClick={resetToQrScan}
                disabled={isProcessing}
                className="px-6 py-4 bg-slate-600 hover:bg-slate-700 disabled:opacity-50 rounded-xl font-medium transition-colors"
              >
                ↩️ Anuluj
              </button>
            </div>
          )}

          {/* Instructions */}
          <div className="mt-8 bg-slate-800/50 rounded-xl p-6 border border-slate-700">
            <h2 className="text-lg font-semibold mb-4 text-emerald-400">Jak wejść do fabryki?</h2>
            <ol className="space-y-3 text-slate-300 list-decimal list-inside">
              <li className={mode === 'qr' ? 'text-blue-400 font-medium' : ''}>
                <strong>Pokaż kod QR</strong> do kamery (kod z przepustki/telefonu)
              </li>
              <li className={mode === 'face' ? 'text-emerald-400 font-medium' : ''}>
                <strong>Spójrz w kamerę</strong> - system rozpozna Twoją twarz
              </li>
              <li>
                <strong>Kliknij "Zweryfikuj twarz"</strong> i poczekaj na wynik
              </li>
            </ol>
            <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <p className="text-sm text-yellow-400">
                ⚠️ Masz 15 sekund na weryfikację twarzy po zeskanowaniu QR
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;
