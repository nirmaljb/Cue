import React from 'react';
import './HUD.css';

/**
 * Dementia-Safe HUD Overlay (Cue)
 * Bottom-right positioning relative to face with smooth tracking
 */
export function HUD({ data, position }) {
    if (!data) return null;

    // Default to center if no position provided
    const x = position ? position.x : 0.5;
    const y = position ? position.y : 0.5;

    // HUD positioning: Bottom-right of face
    // Requirements:
    // - Never overlap face
    // - Max 25% of screen (handled in CSS)
    // - Smooth tracking (handled by useFaceTracking)
    // - Bottom-right relative to face center

    // IMPORTANT: Invert X for natural tracking (webcam is mirrored)
    // When user moves left in real life, they appear right in video
    // So we invert the x coordinate to make HUD track naturally
    const invertedX = 1 - x;

    // Calculate safe positioning
    // Face is at (invertedX%, y%) - place HUD to bottom-right with offset
    const faceOffsetX = 15; // Offset from face center (viewport %)
    const faceOffsetY = -5; // Offset ABOVE face center to prevent going off-screen

    // Position: Bottom-right of face
    // Clamp to keep on screen (5% margin from edges)
    const hudLeft = Math.min(
        Math.max(5, (invertedX * 100) + faceOffsetX),
        70 // Max 70% to ensure HUD doesn't go off right edge (25% width + 5% margin)
    );

    const hudTop = Math.min(
        Math.max(5, (y * 100) + faceOffsetY),
        75 // Max 75% to keep bottom visible
    );

    const style = {
        position: 'absolute',
        left: `${hudLeft}%`,
        top: `${hudTop}%`,
        zIndex: 1000,
        pointerEvents: 'none',
    };

    return (
        <div className="hud-container fade-in" style={style}>
            {/* Person's Name */}
            <h2 className="hud-name">{data.name}</h2>

            {/* Relationship Descriptor in Green Pill */}
            <span className="hud-relation">{data.relation}</span>

            {/* Contextual Note */}
            {data.contextual_note && (
                <p className="hud-routine">{data.contextual_note}</p>
            )}

            {/* Routine Activity */}
            {data.routine && (
                <p className="hud-routine">{data.routine}</p>
            )}
        </div>
    );
}
