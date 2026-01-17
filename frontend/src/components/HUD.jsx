import React from 'react';
import './HUD.css';

/**
 * Dementia-Safe HUD Overlay (Cue)
 * Refined Logic:
 * - Content: Name + Relation ONLY. (Contextual notes removed from overlay)
 * - Positioning: Loosely anchored to face, upper third preferred.
 */
export function HUD({ data, position }) {
    if (!data) return null;

    // Default to center-top if no position provided
    const x = position ? position.x : 0.5;
    const y = position ? position.y : 0.3;

    // Calculate dynamic position
    // Anchor: To the right of the face, slightly above eye level
    // Increased offsets to strictly prevent face overlap (Safe Zone)
    const style = {
        left: `min(65%, calc(${x * 100}% + 20vw))`, // Offset right by 20% viewport width
        top: `clamp(10%, calc(${y * 100}% - 30vh), 40%)`, // Offset up by 30% viewport height
    };

    return (
        <div className="hud-container fade-in" style={style}>
            {/* Person's Name */}
            <h2 className="hud-name">{data.name}</h2>

            {/* Relationship Descriptor */}
            <span className="hud-relation">{data.relation}</span>

            {/* Contextual Note REMOVED per specific design request for minimal overlay */}
        </div>
    );
}
