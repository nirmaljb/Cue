import { useState, useEffect, useCallback, useRef } from 'react';
import { getConfirmedPeople, enrollPerson, deletePerson } from '../services/api';
import './CaregiverMode.css';

/**
 * Caregiver Mode - Enrollment and management panel
 */
export function CaregiverMode() {
    const [confirmedPeople, setConfirmedPeople] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [notification, setNotification] = useState(null);

    // Enrollment form state
    const [showEnrollForm, setShowEnrollForm] = useState(false);
    const [enrollName, setEnrollName] = useState('');
    const [enrollRelation, setEnrollRelation] = useState('');
    const [enrollImage, setEnrollImage] = useState(null);
    const [enrolling, setEnrolling] = useState(false);
    const [captureMode, setCaptureMode] = useState(null); // 'webcam' or 'upload'

    // Webcam refs
    const videoRef = useRef(null);
    const streamRef = useRef(null);

    // Fetch confirmed people
    const fetchConfirmed = useCallback(async () => {
        try {
            setLoading(true);
            const data = await getConfirmedPeople();
            setConfirmedPeople(data.confirmed_people || []);
            setError(null);
        } catch (err) {
            setError('Failed to load people. Is the backend running?');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchConfirmed();
    }, [fetchConfirmed]);

    // Show notification
    const showNotification = (message, type = 'info') => {
        setNotification({ message, type });
        setTimeout(() => setNotification(null), 3000);
    };

    // Start webcam
    const startWebcam = async () => {
        try {
            console.log('📷 Starting webcam...');
            setCaptureMode('webcam');

            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });
            streamRef.current = stream;

            // Wait for next render cycle when video element exists
            setTimeout(() => {
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.play().catch(console.error);
                    console.log('✅ Webcam started');
                }
            }, 100);
        } catch (err) {
            console.error('Webcam error:', err);
            showNotification('Could not access webcam', 'error');
            setCaptureMode(null);
        }
    };

    // Stop webcam
    const stopWebcam = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setCaptureMode(null);
    };

    // Capture from webcam
    const captureFromWebcam = () => {
        if (!videoRef.current) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0);

        const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);
        setEnrollImage(imageBase64);
        stopWebcam();
    };

    // Handle file upload
    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onloadend = () => {
            setEnrollImage(reader.result);
            setCaptureMode(null);
        };
        reader.readAsDataURL(file);
    };

    // Handle enrollment submit
    const handleEnroll = async () => {
        if (!enrollName || !enrollRelation || !enrollImage) {
            showNotification('Please fill all fields and add a photo', 'warning');
            return;
        }

        setEnrolling(true);
        try {
            await enrollPerson(enrollName, enrollRelation, enrollImage);
            showNotification(`${enrollName} enrolled successfully!`, 'success');

            // Reset form
            setEnrollName('');
            setEnrollRelation('');
            setEnrollImage(null);
            setShowEnrollForm(false);

            // Refresh list
            fetchConfirmed();
        } catch (err) {
            showNotification(err.message || 'Failed to enroll person', 'error');
        } finally {
            setEnrolling(false);
        }
    };

    // Handle delete
    const handleDelete = async (personId, name) => {
        if (!confirm(`Delete ${name}? This cannot be undone.`)) return;

        try {
            await deletePerson(personId);
            showNotification(`${name} removed`, 'success');
            fetchConfirmed();
        } catch (err) {
            showNotification('Failed to delete person', 'error');
        }
    };

    // Cleanup webcam on unmount
    useEffect(() => {
        return () => stopWebcam();
    }, []);

    // Relation options
    const relationOptions = [
        'Son', 'Daughter', 'Spouse', 'Sibling', 'Grandchild',
        'Friend', 'Neighbor', 'Doctor', 'Caregiver', 'Other'
    ];

    return (
        <div className="caregiver-mode">
            <header className="caregiver-header">
                <div className="header-content">
                    <a href="/" className="back-link">← Patient View</a>
                    <h1>Caregiver Panel</h1>
                    <p>Enroll and manage known faces</p>
                </div>
            </header>

            <main className="caregiver-main">
                {/* Enroll Button */}
                {!showEnrollForm && (
                    <button
                        className="btn-enroll-new"
                        onClick={() => setShowEnrollForm(true)}
                    >
                        + Enroll New Person
                    </button>
                )}

                {/* Enrollment Form */}
                {showEnrollForm && (
                    <div className="enroll-form">
                        <h2>Enroll New Person</h2>

                        <div className="form-row">
                            <input
                                type="text"
                                placeholder="Name (e.g., Rahul)"
                                value={enrollName}
                                onChange={(e) => setEnrollName(e.target.value)}
                            />
                            <select
                                value={enrollRelation}
                                onChange={(e) => setEnrollRelation(e.target.value)}
                            >
                                <option value="">Select Relation</option>
                                {relationOptions.map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                        </div>

                        {/* Photo capture section */}
                        <div className="photo-section">
                            {!enrollImage && !captureMode && (
                                <div className="photo-options">
                                    <button onClick={startWebcam} className="btn-photo">
                                        📷 Take Photo
                                    </button>
                                    <label className="btn-photo">
                                        📁 Upload Photo
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={handleFileUpload}
                                            style={{ display: 'none' }}
                                        />
                                    </label>
                                </div>
                            )}

                            {captureMode === 'webcam' && (
                                <div className="webcam-container">
                                    <video
                                        ref={videoRef}
                                        autoPlay
                                        playsInline
                                        muted
                                        className="webcam-preview"
                                    />
                                    <div className="webcam-controls">
                                        <button onClick={captureFromWebcam} className="btn-capture">
                                            📸 Capture
                                        </button>
                                        <button onClick={stopWebcam} className="btn-cancel">
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}

                            {enrollImage && (
                                <div className="image-preview">
                                    <img src={enrollImage} alt="Preview" />
                                    <button
                                        className="btn-remove-image"
                                        onClick={() => setEnrollImage(null)}
                                    >
                                        ✕
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="form-actions">
                            <button
                                onClick={handleEnroll}
                                disabled={enrolling || !enrollName || !enrollRelation || !enrollImage}
                                className="btn-confirm"
                            >
                                {enrolling ? 'Enrolling...' : 'Enroll Person'}
                            </button>
                            <button
                                onClick={() => {
                                    setShowEnrollForm(false);
                                    setEnrollImage(null);
                                    stopWebcam();
                                }}
                                className="btn-cancel"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}

                {/* People List */}
                {loading ? (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Loading...</p>
                    </div>
                ) : error ? (
                    <div className="error-state">
                        <p>{error}</p>
                        <button onClick={fetchConfirmed}>Retry</button>
                    </div>
                ) : confirmedPeople.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">👥</div>
                        <h2>No People Enrolled</h2>
                        <p>Enroll people above so the system can recognize them.</p>
                    </div>
                ) : (
                    <div className="people-list">
                        <h2>Enrolled People ({confirmedPeople.length})</h2>

                        {confirmedPeople.map((person) => (
                            <div key={person.person_id} className="person-card">
                                <div className="person-avatar">
                                    <img
                                        src={`http://localhost:8000${person.face_image_url}`}
                                        alt={person.name}
                                    />
                                </div>

                                <div className="person-info">
                                    <h3>{person.name}</h3>
                                    <p className="person-relation">{person.relation}</p>
                                </div>

                                <div className="person-actions">
                                    <button
                                        className="btn-delete"
                                        onClick={() => handleDelete(person.person_id, person.name)}
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>

            {/* Notification */}
            {notification && (
                <div className={`notification ${notification.type}`}>
                    {notification.message}
                </div>
            )}
        </div>
    );
}
