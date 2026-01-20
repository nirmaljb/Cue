import { useState, useEffect, useCallback, useRef } from 'react';
import { getConfirmedPeople, enrollPerson, deletePerson, updatePerson } from '../services/api';
import './CaregiverMode.css';

/**
 * Caregiver Mode - Premium Assistive Dashboard
 * "Organized Calm" Design Language
 */
export function CaregiverMode() {
    const [confirmedPeople, setConfirmedPeople] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [notification, setNotification] = useState(null);
    const [imageRefreshKey, setImageRefreshKey] = useState(Date.now()); // For cache busting

    // Enrollment form state
    const [showEnrollForm, setShowEnrollForm] = useState(false);
    const [enrollName, setEnrollName] = useState('');
    const [enrollRelation, setEnrollRelation] = useState('');
    const [enrollContextNote, setEnrollContextNote] = useState('');
    const [enrollImage, setEnrollImage] = useState(null);
    const [enrolling, setEnrolling] = useState(false);
    const [captureMode, setCaptureMode] = useState(null); // 'webcam' or 'upload'

    // Edit modal state
    const [editingPerson, setEditingPerson] = useState(null);
    const [editName, setEditName] = useState('');
    const [editRelation, setEditRelation] = useState('');
    const [editContextNote, setEditContextNote] = useState('');
    const [editImage, setEditImage] = useState(null);
    const [editCaptureMode, setEditCaptureMode] = useState(null); // 'webcam' or 'upload' for edit
    const [saving, setSaving] = useState(false);

    // Recording Toggle (localStorage persisted)
    const [autoRecordEnabled, setAutoRecordEnabled] = useState(() => {
        return localStorage.getItem('cue_autoRecord') !== 'false'; // Default: ON
    });

    const toggleAutoRecord = () => {
        const newValue = !autoRecordEnabled;
        setAutoRecordEnabled(newValue);
        localStorage.setItem('cue_autoRecord', String(newValue));
    };

    // Whisper Toggle (localStorage persisted)
    const [whisperEnabled, setWhisperEnabled] = useState(() => {
        return localStorage.getItem('cue_whisperEnabled') !== 'false'; // Default: ON
    });

    const toggleWhisper = () => {
        const newValue = !whisperEnabled;
        setWhisperEnabled(newValue);
        localStorage.setItem('cue_whisperEnabled', String(newValue));
    };

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
            await enrollPerson(enrollName, enrollRelation, enrollContextNote, enrollImage);
            showNotification(`${enrollName} enrolled successfully!`, 'success');

            // Reset form
            setEnrollName('');
            setEnrollRelation('');
            setEnrollContextNote('');
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
        if (!confirm(`Are you sure you want to remove ${name}?`)) return;

        try {
            await deletePerson(personId);
            showNotification(`${name} removed`, 'success');
            fetchConfirmed();
        } catch (err) {
            showNotification('Failed to delete person', 'error');
        }
    };

    // Handle start edit
    const handleStartEdit = (person) => {
        setEditingPerson(person);
        setEditName(person.name);
        setEditRelation(person.relation);
        setEditContextNote(person.contextual_note || '');
        setEditImage(null); // Only set if user uploads new photo
    };

    // Handle cancel edit
    const handleCancelEdit = () => {
        setEditingPerson(null);
        setEditName('');
        setEditRelation('');
        setEditContextNote('');
        setEditImage(null);
    };

    // Handle save edit
    const handleSaveEdit = async () => {
        if (!editName || !editRelation) {
            showNotification('Name and relation are required', 'warning');
            return;
        }

        setSaving(true);
        try {
            await updatePerson(
                editingPerson.person_id,
                editName,
                editRelation,
                editContextNote,
                editImage // Will be null if no new photo
            );
            showNotification(`${editName} updated successfully!`, 'success');
            handleCancelEdit();
            setImageRefreshKey(Date.now()); // Force image cache refresh
            fetchConfirmed();
        } catch (err) {
            showNotification(err.message || 'Failed to update person', 'error');
        } finally {
            setSaving(false);
        }
    };

    // Handle edit file upload
    const handleEditFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onloadend = () => {
            setEditImage(reader.result);
            setEditCaptureMode(null);
        };
        reader.readAsDataURL(file);
    };

    // Start webcam for edit
    const startEditWebcam = async () => {
        try {
            setEditCaptureMode('webcam');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480 }
            });
            streamRef.current = stream;

            setTimeout(() => {
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.play().catch(console.error);
                }
            }, 100);
        } catch (err) {
            console.error('Webcam error:', err);
            showNotification('Could not access webcam', 'error');
            setEditCaptureMode(null);
        }
    };

    // Capture from webcam for edit
    const captureEditFromWebcam = () => {
        if (!videoRef.current) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0);

        const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);
        setEditImage(imageBase64);
        stopWebcam();
        setEditCaptureMode(null);
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
            {/* 1. Header Bar */}
            <header className="caregiver-header">
                <div className="header-left">
                    <span className="logo-small">cue.</span>
                </div>
                <div className="header-right">
                    <a href="/" className="back-link">Switch to Patient View</a>
                </div>
            </header>

            <main className="caregiver-main">
                <div className="dashboard-container">

                    {/* 2. Hero Section */}
                    <section className="hero-section">
                        <h1>Welcome, Caregiver.</h1>
                        <div className="system-status">
                            <span className="status-dot"></span>
                            System Active & Monitoring
                        </div>
                    </section>

                    {/* Settings Row - Side by Side Toggles */}
                    <section className="settings-row">
                        <div className="setting-item">
                            <div className="setting-info">
                                <span className="setting-label">📝 Memories</span>
                                <span className="setting-desc">Record conversations</span>
                            </div>
                            <button
                                className={`toggle-switch ${autoRecordEnabled ? 'active' : ''}`}
                                onClick={toggleAutoRecord}
                                aria-pressed={autoRecordEnabled}
                            >
                                <span className="toggle-knob"></span>
                            </button>
                        </div>
                        <div className="setting-item">
                            <div className="setting-info">
                                <span className="setting-label">🔊 Whisper</span>
                                <span className="setting-desc">Audio reassurance</span>
                            </div>
                            <button
                                className={`toggle-switch ${whisperEnabled ? 'active' : ''}`}
                                onClick={toggleWhisper}
                                aria-pressed={whisperEnabled}
                            >
                                <span className="toggle-knob"></span>
                            </button>
                        </div>
                    </section>

                    {/* 3. Actions Area (Add Person) */}
                    {!showEnrollForm && (
                        <section className="actions-section">
                            <div className="add-person-card" onClick={() => setShowEnrollForm(true)}>
                                <div className="icon-circle">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="12" y1="5" x2="12" y2="19"></line>
                                        <line x1="5" y1="12" x2="19" y2="12"></line>
                                    </svg>
                                </div>
                                <span className="add-label">Add New Person</span>
                            </div>
                        </section>
                    )}

                    {/* Enrollment Form (Card Style) */}
                    {showEnrollForm && (
                        <div className="enroll-form slide-up">
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

                            <div className="form-row">
                                <textarea
                                    placeholder="Contextual Note (e.g., 'You usually talk in the evenings.')"
                                    value={enrollContextNote}
                                    onChange={(e) => setEnrollContextNote(e.target.value)}
                                    className="input-context-note"
                                    rows={2}
                                />
                            </div>

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
                                    {enrolling ? 'Enrolling...' : 'Confirm & Enroll'}
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

                    {/* 4. The Grid (Bento Style) */}
                    <section className="people-section">
                        {!loading && !error && (
                            <h2>{confirmedPeople.length > 0 ? `${confirmedPeople.length} People Active` : 'No People Enrolled'}</h2>
                        )}

                        {loading ? (
                            <div className="loading-state">
                                <div className="loading-spinner"></div>
                                <p>Loading System...</p>
                            </div>
                        ) : error ? (
                            <div className="error-state">
                                <p>{error}</p>
                                <button className="btn-retry" onClick={fetchConfirmed}>Retry Connection</button>
                            </div>
                        ) : (
                            <div className="people-grid">
                                {confirmedPeople.map((person) => (
                                    <div key={person.person_id} className="bento-card">
                                        {/* Edit Icon */}
                                        <button
                                            className="btn-edit-icon"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleStartEdit(person);
                                            }}
                                            title="Edit Person"
                                        >
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                            </svg>
                                        </button>

                                        {/* Delete Icon */}
                                        <button
                                            className="btn-delete-icon"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDelete(person.person_id, person.name);
                                            }}
                                            title="Remove Person"
                                        >
                                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="3 6 5 6 21 6"></polyline>
                                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                            </svg>
                                        </button>

                                        {/* Face Hero */}
                                        <div className="card-image-container">
                                            <img
                                                src={`http://localhost:8000${person.face_image_url}?t=${imageRefreshKey}`}
                                                alt={person.name}
                                            />
                                        </div>

                                        {/* Content */}
                                        <div className="card-content">
                                            <div className="card-header">
                                                <span className="card-name">{person.name}</span>
                                                <span className="card-relation">{person.relation}</span>
                                            </div>
                                            {person.contextual_note && (
                                                <p className="card-note">{person.contextual_note}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            </main>

            {/* Edit Modal */}
            {editingPerson && (
                <div className="modal-overlay" onClick={handleCancelEdit}>
                    <div className="edit-modal" onClick={(e) => e.stopPropagation()}>
                        <h2>Edit {editingPerson.name}</h2>

                        <div className="form-row">
                            <input
                                type="text"
                                placeholder="Name"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                            />
                            <select
                                value={editRelation}
                                onChange={(e) => setEditRelation(e.target.value)}
                            >
                                <option value="">Select Relation</option>
                                {relationOptions.map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-row">
                            <textarea
                                placeholder="Contextual Note"
                                value={editContextNote}
                                onChange={(e) => setEditContextNote(e.target.value)}
                                rows={2}
                            />
                        </div>

                        <div className="photo-section">
                            {editCaptureMode === 'webcam' ? (
                                <div className="webcam-section">
                                    <video ref={videoRef} autoPlay playsInline />
                                    <div className="webcam-controls">
                                        <button onClick={captureEditFromWebcam} className="btn-capture">
                                            📸 Capture
                                        </button>
                                        <button onClick={() => { stopWebcam(); setEditCaptureMode(null); }} className="btn-cancel">
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className="current-photo">
                                        <img
                                            src={editImage || `http://localhost:8000${editingPerson.face_image_url}?t=${imageRefreshKey}`}
                                            alt={editingPerson.name}
                                        />
                                    </div>
                                    <div className="photo-buttons">
                                        <button onClick={startEditWebcam} className="btn-photo">
                                            📷 Webcam
                                        </button>
                                        <label className="btn-photo">
                                            📁 Upload
                                            <input
                                                type="file"
                                                accept="image/*"
                                                onChange={handleEditFileUpload}
                                                style={{ display: 'none' }}
                                            />
                                        </label>
                                    </div>
                                </>
                            )}
                        </div>

                        <div className="form-actions">
                            <button
                                onClick={handleSaveEdit}
                                disabled={saving || !editName || !editRelation}
                                className="btn-confirm"
                            >
                                {saving ? 'Saving...' : 'Save Changes'}
                            </button>
                            <button onClick={handleCancelEdit} className="btn-cancel">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Notification Toast */}
            {notification && (
                <div className={`notification ${notification.type}`}>
                    {notification.message}
                </div>
            )}
        </div>
    );
}
