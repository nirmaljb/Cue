import './RecordButton.css';

/**
 * Recording button component with animation
 */
export function RecordButton({ isRecording, onStart, onStop, disabled }) {
    const handleClick = () => {
        if (isRecording) {
            onStop?.();
        } else {
            onStart?.();
        }
    };

    return (
        <button
            className={`record-button ${isRecording ? 'recording' : ''}`}
            onClick={handleClick}
            disabled={disabled}
            title={isRecording ? 'Stop Recording' : 'Record Interaction'}
        >
            <div className="record-button-inner">
                {isRecording ? (
                    <div className="stop-icon"></div>
                ) : (
                    <div className="mic-icon">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                        </svg>
                    </div>
                )}
            </div>
            {isRecording && (
                <div className="recording-indicator">
                    <span className="recording-dot"></span>
                    Recording...
                </div>
            )}
        </button>
    );
}
