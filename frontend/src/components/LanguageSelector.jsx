import React from 'react';
import './LanguageSelector.css';

/**
 * Language selector dropdown for multi-language support.
 * Stores selection in localStorage under 'cue_language' key.
 */

const LANGUAGES = [
    { code: 'en', name: 'English', native: 'English', flag: '🇬🇧' },
    { code: 'hi', name: 'Hindi', native: 'हिंदी', flag: '🇮🇳' },
    { code: 'ta', name: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
    { code: 'bn', name: 'Bengali', native: 'বাংলা', flag: '🇮🇳' },
    { code: 'te', name: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
];

const STORAGE_KEY = 'cue_language';

export function getStoredLanguage() {
    return localStorage.getItem(STORAGE_KEY) || 'en';
}

export function setStoredLanguage(lang) {
    localStorage.setItem(STORAGE_KEY, lang);
}

export default function LanguageSelector({ value, onChange }) {
    const handleChange = (e) => {
        const newLang = e.target.value;
        setStoredLanguage(newLang);
        if (onChange) {
            onChange(newLang);
        }
    };

    return (
        <div className="language-selector">
            <select
                value={value || getStoredLanguage()}
                onChange={handleChange}
                className="language-dropdown"
            >
                {LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                        {lang.flag} {lang.native}
                    </option>
                ))}
            </select>
        </div>
    );
}

export { LANGUAGES };
