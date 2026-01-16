import { useState, useRef, useCallback } from 'react';

/**
 * Custom hook for audio recording using MediaRecorder API
 */
export function useAudioRecorder() {
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const startRecording = useCallback(async () => {
        try {
            setError(null);
            chunksRef.current = [];

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus',
            });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start(1000); // Collect data every second
            setIsRecording(true);
        } catch (err) {
            setError('Failed to access microphone');
            console.error('Audio recording error:', err);
        }
    }, []);

    const stopRecording = useCallback(() => {
        return new Promise((resolve) => {
            if (!mediaRecorderRef.current || !isRecording) {
                resolve(null);
                return;
            }

            mediaRecorderRef.current.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });

                // Convert to base64
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64 = reader.result;
                    resolve(base64);
                };
                reader.readAsDataURL(blob);

                // Stop all tracks
                mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.stop();
            setIsRecording(false);
        });
    }, [isRecording]);

    return {
        isRecording,
        error,
        startRecording,
        stopRecording,
    };
}
