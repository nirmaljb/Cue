import { useState, useCallback, useRef, useEffect } from 'react';
import { Camera } from '../components/Camera';
import { HUD } from '../components/HUD';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useFaceTracking, SessionState } from '../hooks/useFaceTracking';
import { recognizeFace, getHUDContext, saveMemory, getWhisper } from '../services/api';
import { getStoredLanguage } from '../components/LanguageSelector';
import './PatientMode.css';

/**
 * Patient Mode (Cue) - Passive, Dementia-Safe Experience
 * 
 * Logic:
 * - Passive Face Recognition (Multi-frame)
 * - Passive Audio Recording (Starts on recognition, stops on exit)
 * - Silent/Unknown state (No errors)
 * - Static Contextual Cues
 */
export function PatientMode() {
    const [hudData, setHudData] = useState(null);
    const [currentPersonId, setCurrentPersonId] = useState(null);
    const [notification, setNotification] = useState(null);

    const videoRef = useRef(null);
    const { isRecording, startRecording, stopRecording } = useAudioRecorder();

    // Track the person who was being recorded to save memory after session ends
    const recordingPersonIdRef = useRef(null);

    // Show notification (Internal/Debug mainly, or subtle confirmation)
    const showNotification = useCallback((message, type = 'info') => {
        // Reduced visibility for patient calm checks
        // setNotification({ message, type });
        // setTimeout(() => setNotification(null), 3000);
        console.log(`[Notification] ${message}`);
    }, []);

    // Handle recognition request
    const handleRecognitionRequest = useCallback(async (frames) => {
        try {
            const recognition = await recognizeFace(frames);

            if (recognition.recognized && recognition.status === 'confirmed') {
                // Get language from localStorage
                const lang = getStoredLanguage();
                const hud = await getHUDContext(recognition.person_id, recognition.status, lang);
                setHudData(hud);
                setCurrentPersonId(recognition.person_id);
                recordingPersonIdRef.current = recognition.person_id;
                return { recognized: true, ...recognition };
            } else {
                setHudData(null);
                setCurrentPersonId(null);
                recordingPersonIdRef.current = null;
                return { recognized: false };
            }
        } catch (error) {
            console.error('Recognition error:', error);
            setHudData(null);
            setCurrentPersonId(null);
            return { recognized: false, error };
        }
    }, []);

    // Face tracking hook
    const {
        sessionState,
        startTracking,
        stopTracking,
        retryRecognition,
        facePosition, // Smoothed coordinates
        isIdle,
        isRecognized,
        isNotFound,
    } = useFaceTracking(videoRef, handleRecognitionRequest);

    // Passive Recording Logic
    useEffect(() => {
        // Start recording when person is recognized (if enabled)
        if (isRecognized && !isRecording && currentPersonId) {
            // Check if automatic recording is enabled
            const autoRecordEnabled = localStorage.getItem('cue_autoRecord') !== 'false';
            if (autoRecordEnabled) {
                console.log('🎙️ Starting passive recording...');
                startRecording();
            } else {
                console.log('⏸️ Auto-recording disabled by caregiver');
            }
        }
    }, [isRecognized, isRecording, currentPersonId, startRecording]);

    // Whisper Audio Playback (One-time after recognition)
    useEffect(() => {
        if (isRecognized && currentPersonId && hudData) {
            // Check if whisper is enabled
            const whisperEnabled = localStorage.getItem('cue_whisperEnabled') !== 'false';
            if (!whisperEnabled) {
                console.log('⏸️ Whisper disabled by caregiver');
                return;
            }

            // Delay for calm transition (400ms after HUD appears)
            const timer = setTimeout(async () => {
                try {
                    console.log('🔊 Fetching whisper audio...');
                    // Get language from localStorage
                    const lang = getStoredLanguage();
                    const data = await getWhisper(currentPersonId, lang);

                    if (data.audio_url) {
                        console.log('🎵 Playing whisper:', data.text);
                        const audio = new Audio(data.audio_url);
                        audio.volume = 0.6; // Low volume
                        audio.play().catch(e => console.log('Audio play blocked:', e));
                    } else {
                        console.log('⏸️ Whisper skipped:', data.reason);
                    }
                } catch (e) {
                    // Silent fail
                    console.log('⏸️ Whisper fetch failed:', e);
                }
            }, 400);

            return () => clearTimeout(timer);
        }
    }, [isRecognized, currentPersonId, hudData]);

    // Handle Session End (Face Lost) -> Stop Recording & Save
    useEffect(() => {
        if (isIdle) {
            // If we were recording and just went idle, stop and save
            if (isRecording && recordingPersonIdRef.current) {
                console.log('🛑 Face lost, stopping recording...');
                const personIdToSave = recordingPersonIdRef.current;

                stopRecording().then(async (audioBase64) => {
                    if (audioBase64) {
                        console.log('💾 Saving passive memory...');
                        try {
                            await saveMemory(personIdToSave, audioBase64);
                            console.log('✅ Memory saved silently');
                        } catch (error) {
                            console.error('Failed to save memory:', error);
                        }
                    }
                });
            }

            // Clear state
            setHudData(null);
            setCurrentPersonId(null);
            recordingPersonIdRef.current = null;
        }
    }, [isIdle, isRecording, stopRecording]);

    // Handle video ready
    const handleVideoReady = useCallback((ref) => {
        videoRef.current = ref.current;
        startTracking();
    }, [startTracking]);

    // Cleanup
    useEffect(() => {
        return () => stopTracking();
    }, [stopTracking]);

    return (
        <div className="patient-mode">
            <Camera onVideoReady={handleVideoReady}>
                {/* HUD Overlay - only show when recognized */}
                {isRecognized && hudData && (
                    <HUD data={hudData} position={facePosition} />
                )}
            </Camera>

            {/* No Visible Controls / Buttons */}
            {/* Passive recording happens automatically */}

            {/* Subtle Retry (Clean State - Only touch to retry) */}
            {isNotFound && (
                <div className="retry-affordance" onClick={retryRecognition}>
                    <span className="retry-tap">Tap to try again</span>
                </div>
            )}

            {/* Minimal Status Dot (No Text) */}
            <div className="mode-indicator minimal">
                <span className={`mode-dot ${sessionState.toLowerCase()}`}></span>
            </div>

            {/* Caregiver Link */}
            <a href="/caregiver" className="caregiver-link">
                cue.
            </a>
        </div>
    );
}
