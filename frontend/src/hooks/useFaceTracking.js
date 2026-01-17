import { useState, useRef, useCallback, useEffect } from 'react';
import { FaceDetection } from '@mediapipe/face_detection';
import { Camera } from '@mediapipe/camera_utils';

/**
 * Session States:
 * - IDLE: No face detected, waiting for face to appear
 * - CAPTURING: Face detected, capturing multiple frames
 * - SCANNING: Frames captured, calling backend ONCE
 * - RECOGNIZED: Backend returned a match, showing HUD
 * - NOT_FOUND: Backend returned no match, showing neutral UI
 */
const SessionState = {
    IDLE: 'IDLE',
    CAPTURING: 'CAPTURING',
    SCANNING: 'SCANNING',
    RECOGNIZED: 'RECOGNIZED',
    NOT_FOUND: 'NOT_FOUND',
};

// Thresholds
const FACE_STABLE_FRAMES = 10;     // Frames with face before starting capture
const FACE_LOST_FRAMES = 30;       // Frames without face before resetting (~1 second)
const CAPTURE_FRAME_COUNT = 5;     // Number of frames to capture
const CAPTURE_INTERVAL_MS = 300;   // Interval between captures (total ~1.5s)

/**
 * Event-driven face tracking hook using MediaPipe.
 * 
 * Architecture:
 * - Frontend = Perception authority (face presence detection)
 * - Backend = Identity authority (who is this person?)
 * - Multi-frame capture for better quality
 * - ONE backend call per session
 * - No polling, no timers that cause state changes
 */
export function useFaceTracking(videoRef, onRecognitionRequest) {
    const [sessionState, setSessionState] = useState(SessionState.IDLE);
    const [recognitionResult, setRecognitionResult] = useState(null);
    const [error, setError] = useState(null);

    // Refs for tracking
    const faceDetectorRef = useRef(null);
    const cameraRef = useRef(null);
    const faceFrameCountRef = useRef(0);      // Consecutive frames WITH face
    const noFaceFrameCountRef = useRef(0);    // Consecutive frames WITHOUT face
    const sessionStateRef = useRef(SessionState.IDLE);
    const capturedFramesRef = useRef([]);     // Array of captured frames
    const captureInProgressRef = useRef(false);

    // Keep sessionStateRef in sync
    useEffect(() => {
        sessionStateRef.current = sessionState;
    }, [sessionState]);

    // Capture frame from video
    const captureFrame = useCallback(() => {
        if (!videoRef.current || videoRef.current.readyState < 2) return null;

        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        return canvas.toDataURL('image/jpeg', 0.8);
    }, [videoRef]);

    // Capture multiple frames and send to backend
    const captureMultipleFrames = useCallback(async () => {
        if (captureInProgressRef.current) return;
        captureInProgressRef.current = true;

        console.log('📸 Starting multi-frame capture...');
        setSessionState(SessionState.CAPTURING);

        capturedFramesRef.current = [];

        // Capture 5 frames at 300ms intervals
        for (let i = 0; i < CAPTURE_FRAME_COUNT; i++) {
            const frame = captureFrame();
            if (frame) {
                capturedFramesRef.current.push(frame);
                console.log(`  Frame ${i + 1}/${CAPTURE_FRAME_COUNT} captured`);
            }

            if (i < CAPTURE_FRAME_COUNT - 1) {
                await new Promise(resolve => setTimeout(resolve, CAPTURE_INTERVAL_MS));
            }
        }

        console.log(`✅ Captured ${capturedFramesRef.current.length} frames, sending to backend...`);
        setSessionState(SessionState.SCANNING);

        // Send frames to backend for recognition
        if (capturedFramesRef.current.length > 0 && onRecognitionRequest) {
            try {
                const result = await onRecognitionRequest(capturedFramesRef.current);

                if (result?.recognized) {
                    console.log('✅ Person recognized:', result);
                    setRecognitionResult(result);
                    setSessionState(SessionState.RECOGNIZED);
                } else {
                    console.log('❓ Person not recognized');
                    setRecognitionResult(null);
                    setSessionState(SessionState.NOT_FOUND);
                }
            } catch (err) {
                console.error('Recognition error:', err);
                setRecognitionResult(null);
                setSessionState(SessionState.NOT_FOUND);
            }
        }

        captureInProgressRef.current = false;
    }, [captureFrame, onRecognitionRequest]);

    // Smoothing factor (lower = smoother/slower)
    const SMOOTHING_FACTOR = 0.08;
    const [facePosition, setFacePosition] = useState({ x: 0.5, y: 0.3 }); // Initial: center-top
    const targetPositionRef = useRef({ x: 0.5, y: 0.3 });
    const currentPositionRef = useRef({ x: 0.5, y: 0.3 });

    // Handle face detection results from MediaPipe
    const onFaceDetectionResults = useCallback((results) => {
        const hasFace = results.detections && results.detections.length > 0;
        const currentState = sessionStateRef.current;

        if (hasFace) {
            // Face present
            noFaceFrameCountRef.current = 0;
            faceFrameCountRef.current++;

            // Calculate face center (Assume normalized 0-1)
            const detection = results.detections[0];
            const bbox = detection.boundingBox;

            // MediaPipe detection returns relative bounding box (0-1)
            // Center X = xCenter, Center Y = yCenter
            const centerX = bbox.xCenter;
            const centerY = bbox.yCenter;

            // Update target
            targetPositionRef.current = { x: centerX, y: centerY };

            // Apply smoothing (Lerp)
            const cur = currentPositionRef.current;
            const target = targetPositionRef.current;

            const newX = cur.x + (target.x - cur.x) * SMOOTHING_FACTOR;
            const newY = cur.y + (target.y - cur.y) * SMOOTHING_FACTOR;

            currentPositionRef.current = { x: newX, y: newY };
            setFacePosition({ x: newX, y: newY });

            // Trigger capture when face stabilizes and we're in IDLE
            if (currentState === SessionState.IDLE &&
                faceFrameCountRef.current >= FACE_STABLE_FRAMES &&
                !captureInProgressRef.current) {

                console.log('👤 Stable face detected, starting capture window...');
                captureMultipleFrames();
            }
        } else {
            // No face present
            faceFrameCountRef.current = 0;
            noFaceFrameCountRef.current++;

            // If in a session state and face is lost, reset to IDLE
            if ((currentState === SessionState.RECOGNIZED ||
                currentState === SessionState.NOT_FOUND) &&
                noFaceFrameCountRef.current >= FACE_LOST_FRAMES) {

                console.log('👋 Face lost, resetting to IDLE');
                setSessionState(SessionState.IDLE);
                setRecognitionResult(null);
                faceFrameCountRef.current = 0;
                noFaceFrameCountRef.current = 0;
                capturedFramesRef.current = [];
            }
        }
    }, [captureMultipleFrames]);

    // Manual retry function - for gentle retry affordance
    const retryRecognition = useCallback(() => {
        console.log('🔄 Manual retry triggered');
        setSessionState(SessionState.IDLE);
        setRecognitionResult(null);
        faceFrameCountRef.current = 0;
        noFaceFrameCountRef.current = 0;
        capturedFramesRef.current = [];
        captureInProgressRef.current = false;
    }, []);

    // Initialize MediaPipe Face Detection
    const initializeFaceDetection = useCallback(async () => {
        if (!videoRef.current) return;

        try {
            console.log('🚀 Initializing MediaPipe Face Detection...');

            // Create face detector
            const faceDetection = new FaceDetection({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`;
                }
            });

            faceDetection.setOptions({
                model: 'short',
                minDetectionConfidence: 0.5,
            });

            faceDetection.onResults(onFaceDetectionResults);
            faceDetectorRef.current = faceDetection;

            // Create camera
            const camera = new Camera(videoRef.current, {
                onFrame: async () => {
                    if (faceDetectorRef.current && videoRef.current) {
                        await faceDetectorRef.current.send({ image: videoRef.current });
                    }
                },
                width: 640,
                height: 480,
            });

            await camera.start();
            cameraRef.current = camera;

            console.log('✅ Face detection initialized');
        } catch (err) {
            console.error('Failed to initialize face detection:', err);
            setError('Face detection not available');
        }
    }, [videoRef, onFaceDetectionResults]);

    // Start tracking
    const startTracking = useCallback(() => {
        console.log('🎬 Starting face tracking...');
        setSessionState(SessionState.IDLE);
        setRecognitionResult(null);
        faceFrameCountRef.current = 0;
        noFaceFrameCountRef.current = 0;
        capturedFramesRef.current = [];
        captureInProgressRef.current = false;

        initializeFaceDetection();
    }, [initializeFaceDetection]);

    // Stop tracking
    const stopTracking = useCallback(() => {
        console.log('🛑 Stopping face tracking');
        if (cameraRef.current) {
            cameraRef.current.stop();
            cameraRef.current = null;
        }
        if (faceDetectorRef.current) {
            faceDetectorRef.current = null;
        }
        setSessionState(SessionState.IDLE);
        setRecognitionResult(null);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopTracking();
        };
    }, [stopTracking]);

    return {
        sessionState,
        recognitionResult,
        error,
        startTracking,
        stopTracking,
        retryRecognition,
        captureFrame,
        facePosition,
        // Convenience state checks
        isIdle: sessionState === SessionState.IDLE,
        isCapturing: sessionState === SessionState.CAPTURING,
        isScanning: sessionState === SessionState.SCANNING,
        isRecognized: sessionState === SessionState.RECOGNIZED,
        isNotFound: sessionState === SessionState.NOT_FOUND,
    };
}

export { SessionState };
