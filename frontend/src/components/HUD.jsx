import { useEffect, useState } from 'react';
import './HUD.css';

/**
 * AR-style HUD overlay component
 * Shows person info when recognized
 * 
 * Note: TTS disabled for now - can be re-enabled later as opt-in feature
 */
export function HUD({ data }) {
    const [isVisible, setIsVisible] = useState(false);

    // Fade in animation
    useEffect(() => {
        if (data) {
            const timer = setTimeout(() => setIsVisible(true), 100);
            return () => clearTimeout(timer);
        } else {
            setIsVisible(false);
        }
    }, [data]);

    if (!data) return null;

    return (
        <div className={`hud-container ${isVisible ? 'visible' : ''}`}>
            <div className="hud-header">
                <div className="hud-indicator"></div>
                <span className="hud-status">IDENTIFIED</span>
            </div>

            <div className="hud-content">
                <h2 className="hud-name">{data.name}</h2>
                <p className="hud-relation">{data.relation}</p>
                <div className="hud-divider"></div>
                <p className="hud-emotional-cue">{data.emotionalCue}</p>

                <div className="hud-familiarity">
                    <span>Familiarity</span>
                    <div className="familiarity-bar">
                        <div
                            className="familiarity-fill"
                            style={{ width: `${(data.familiarity || 0) * 100}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            <div className="hud-corner tl"></div>
            <div className="hud-corner tr"></div>
            <div className="hud-corner bl"></div>
            <div className="hud-corner br"></div>
        </div>
    );
}
