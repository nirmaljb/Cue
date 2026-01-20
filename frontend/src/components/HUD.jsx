import React from 'react';
import './HUD.css';

/**
 * Dementia-Safe HUD Overlay (Cue)
 * Simple, clean positioning that follows the face
 */
export function HUD({ data, position }) {
    if (!data) return null;

    // Default to center-top if no position provided
    const x = position ? position.x : 0.5;
    const y = position ? position.y : 0.3;

    // Simple offset positioning
    // Smoothing handled by useFaceTracking
    const style = {
        position: 'absolute',

        // Vertical: Offset slightly above face center
        top: `calc(${y * 100}% - 100px)`,

        // Horizontal: Offset to the right of face
        left: `calc(${x * 100}% + 80px)`,

        maxWidth: '300px',
        zIndex: 1000,
        pointerEvents: 'none',
    };

    return (
        <div className="hud-container fade-in" style={style}>
            {/* Person's Name */}
            <h2 className="hud-name">{data.name}</h2>

            {/* Relationship Descriptor in Green Pill */}
            <span className="hud-relation">{data.relation}</span>
        </div>
    );
}
