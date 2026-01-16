import { useState, useCallback, useRef, useEffect } from 'react';
import { Camera } from '../components/Camera';
import { HUD } from '../components/HUD';
import { RecordButton } from '../components/RecordButton';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useFaceTracking, SessionState } from '../hooks/useFaceTracking';
import { recognizeFace, getHUDContext, saveMemory } from '../services/api';
import './PatientMode.css';

/**
 * Patient Mode - Main view for dementia patient
 * 
 * Architecture:
 * - Event-driven face recognition (no polling)
 * - Multi-frame capture for better quality
 * - ONE backend call per session
 * - Gentle retry affordance for recovery
 */
export function PatientMode() {
    const [hudData, setHudData] = useState(null);
    const [currentPersonId, setCurrentPersonId] = useState(null);
    const [notification, setNotification] = useState(null);

    const videoRef = useRef(null);
    const { isRecording, startRecording, stopRecording } = useAudioRecorder();

    // Show notification
    const showNotification = useCallback((message, type = 'info') => {
        setNotification({ message, type });
        setTimeout(() => setNotification(null), 3000);
    }, []);

    // Handle recognition request from face tracking hook
    // Receives array of frames captured over 1.5 seconds
    const handleRecognitionRequest = useCallback(async (frames) => {
        try {
            console.log(`🔍 Sending ${frames.length} frames for recognition...`);
            const recognition = await recognizeFace(frames);

            if (recognition.recognized && recognition.status === 'confirmed') {
                // Get HUD context for recognized person
                const hud = await getHUDContext(recognition.person_id, recognition.status);
                setHudData(hud);
                setCurrentPersonId(recognition.person_id);
                return { recognized: true, ...recognition };
            } else {
                // Not recognized
                setHudData(null);
                setCurrentPersonId(null);
                return { recognized: false };
            }
        } catch (error) {
            console.error('Recognition error:', error);
            setHudData(null);
            setCurrentPersonId(null);
            return { recognized: false, error };
        }
    }, []);

    // Face tracking hook with multi-frame capture
    const {
        sessionState,
        startTracking,
        stopTracking,
        retryRecognition,
        isIdle,
        isCapturing,
        isScanning,
        isRecognized,
        isNotFound,
    } = useFaceTracking(videoRef, handleRecognitionRequest);

    // Clear HUD when session ends (face leaves)
    useEffect(() => {
        if (isIdle) {
            setHudData(null);
            setCurrentPersonId(null);
        }
    }, [isIdle]);

    // Handle video ready
    const handleVideoReady = useCallback((ref) => {
        videoRef.current = ref.current;
        startTracking();
    }, [startTracking]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopTracking();
        };
    }, [stopTracking]);

    // Handle retry tap
    const handleRetry = useCallback(() => {
        retryRecognition();
    }, [retryRecognition]);

    // Handle recording
    const handleStartRecording = useCallback(() => {
        startRecording();
        showNotification('Recording...', 'info');
    }, [startRecording, showNotification]);

    const handleStopRecording = useCallback(async () => {
        const audioBase64 = await stopRecording();

        if (!audioBase64) {
            showNotification('Recording failed', 'error');
            return;
        }

        if (!currentPersonId) {
            showNotification('No person identified. Recording not saved.', 'warning');
            return;
        }

        showNotification('Processing...', 'info');

        try {
            const result = await saveMemory(currentPersonId, audioBase64);
            showNotification(`Memory saved: "${result.summary}"`, 'success');
        } catch (error) {
            console.error('Save error:', error);
            showNotification('Failed to save memory', 'error');
        }
    }, [stopRecording, currentPersonId, showNotification]);

    // Get status indicator text and class
    const getStatusInfo = () => {
        switch (sessionState) {
            case SessionState.IDLE:
                return { text: 'Looking for face...', className: 'idle' };
            case SessionState.CAPTURING:
                return { text: 'Capturing...', className: 'capturing' };
            case SessionState.SCANNING:
                return { text: 'Identifying...', className: 'scanning' };
            case SessionState.RECOGNIZED:
                return { text: hudData?.name ? `Hi, ${hudData.name}!` : 'Recognized', className: 'found' };
            case SessionState.NOT_FOUND:
                return { text: 'Unknown person', className: 'not_found' };
            default:
                return { text: 'Ready', className: 'idle' };
        }
    };

    const statusInfo = getStatusInfo();

    return (
        <div className="patient-mode">
            <Camera onVideoReady={handleVideoReady}>
                {/* HUD Overlay - only show when recognized */}
                {isRecognized && hudData && (
                    <HUD data={hudData} />
                )}
            </Camera>

            {/* Record Button */}
            <RecordButton
                isRecording={isRecording}
                onStart={handleStartRecording}
                onStop={handleStopRecording}
                disabled={isScanning || isCapturing}
            />

            {/* Gentle Retry Affordance - visible in NOT_FOUND state */}
            {isNotFound && (
                <div className="retry-affordance" onClick={handleRetry}>
                    <span>Look at camera</span>
                    <span className="retry-tap">Tap to try again</span>
                </div>
            )}

            {/* Notification */}
            {notification && (
                <div className={`notification ${notification.type}`}>
                    {notification.message}
                </div>
            )}

            {/* Status Indicator */}
            <div className="mode-indicator">
                <span className={`mode-dot ${statusInfo.className}`}></span>
                {statusInfo.text}
            </div>

            {/* Caregiver Link */}
            <a href="/caregiver" className="caregiver-link">
                Caregiver Panel →
            </a>
        </div>
    );
}
