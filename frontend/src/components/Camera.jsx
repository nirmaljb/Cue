import { useRef, useEffect, useState } from 'react';
import './Camera.css';

/**
 * Camera component for video feed display
 */
export function Camera({ onVideoReady, children }) {
    const videoRef = useRef(null);
    const [isReady, setIsReady] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        facingMode: 'user',
                    },
                    audio: false,
                });

                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.onloadedmetadata = () => {
                        setIsReady(true);
                        if (onVideoReady) {
                            onVideoReady(videoRef);
                        }
                    };
                }
            } catch (err) {
                console.error('Camera error:', err);
                setError('Unable to access camera. Please grant permission.');
            }
        }

        startCamera();

        // Cleanup
        return () => {
            if (videoRef.current?.srcObject) {
                videoRef.current.srcObject.getTracks().forEach(track => track.stop());
            }
        };
    }, [onVideoReady]);

    return (
        <div className="camera-container">
            {error ? (
                <div className="camera-error">
                    <p>{error}</p>
                </div>
            ) : (
                <>
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="camera-video"
                    />
                    {isReady && (
                        <div className="camera-overlay">
                            {children}
                        </div>
                    )}
                    {!isReady && (
                        <div className="camera-loading">
                            <div className="loading-spinner"></div>
                            <p>Starting camera...</p>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
