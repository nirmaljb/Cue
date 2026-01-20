"""LLM service using Groq for reasoning and summarization."""

from groq import Groq
import json
from typing import Optional

from app.config import settings


class LLMService:
    """Service for LLM-powered reasoning using Groq."""
    
    def __init__(self):
        self.client: Optional[Groq] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the Groq client."""
        if self._initialized:
            return
        
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self._initialized = True
        print("✅ Groq LLM client initialized")
    
    def generate_hud_context(
        self,
        name: str,
        relation: str,
        memories: list[dict],
        familiarity_score: float,
    ) -> dict:
        """Generate HUD context for a confirmed person.
        
        Args:
            name: Person's name
            relation: Relationship to user
            memories: List of memory summaries
            familiarity_score: Familiarity score (0-1)
        
        Returns:
            HUD payload dict
        """
        if not self._initialized:
            self.initialize()
        
        # Build memory context
        memory_context = ""
        if memories:
            memory_texts = [m.get("summary", "") for m in memories[:5]]
            memory_context = "\n".join(f"- {m}" for m in memory_texts if m)
        else:
            memory_context = "No recorded memories yet."
        
        # Familiarity description
        if familiarity_score >= 0.8:
            familiarity_label = "Very Familiar"
        elif familiarity_score >= 0.5:
            familiarity_label = "Familiar"
        elif familiarity_score >= 0.2:
            familiarity_label = "Somewhat Familiar"
        else:
            familiarity_label = "New Acquaintance"
        
        prompt = f"""You are helping a dementia patient recognize someone.

Person Information:
- Name: {name}
- Relationship: {relation}
- Familiarity Level: {familiarity_label} ({familiarity_score:.0%})

Recent Memories/Interactions:
{memory_context}

Generate a warm, supportive emotional cue that helps the patient connect with this person.
The cue should be:
- Short (1-2 sentences max)
- Positive and reassuring
- Reference shared memories if available
- Simple and easy to understand

Also decide if audio should be spoken (true if this is a close relationship or first encounter of the day).

Respond in this exact JSON format only, no other text:
{{
    "emotionalCue": "Your emotional cue here",
    "speak": true or false,
    "speechText": "Simple greeting like 'This is [Name], your [relation]'"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a calm, supportive assistant helping dementia patients recognize loved ones. Always respond in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            
            return {
                "name": name,
                "relation": relation,
                "emotionalCue": result.get("emotionalCue", f"{name} is your {relation}."),
                "familiarity": familiarity_score,
                "speak": result.get("speak", False),
                "speechText": result.get("speechText"),
            }
            
        except Exception as e:
            print(f"⚠️ LLM error: {e}")
            # Fallback response
            return {
                "name": name,
                "relation": relation,
                "emotionalCue": f"{name} is your {relation}.",
                "familiarity": familiarity_score,
                "speak": False,
                "speechText": None,
            }
    
    def summarize_memory(self, transcript: str) -> dict:
        """Summarize a conversation transcript into a memory.
        
        Args:
            transcript: Raw conversation transcript
        
        Returns:
            dict with summary, emotional_tone, important_event
        """
        if not self._initialized:
            self.initialize()
        
        prompt = f"""Summarize this conversation into a short memory for a dementia patient.

Transcript:
{transcript}

Rules:
- Do NOT guess names or relationships
- Keep the summary short (1-2 sentences)
- Focus on what happened, not who said what
- Identify the emotional tone (happy, neutral, sad, excited, etc.)
- Note any important events (birthdays, announcements, etc.)

Respond in this exact JSON format only, no other text:
{{
    "summary": "Short summary of what happened",
    "emotional_tone": "happy/neutral/sad/excited/etc",
    "important_event": "null or brief description of important event"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a memory summarization assistant. Create concise, gentle summaries. Always respond in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            
            return {
                "summary": result.get("summary", "A conversation took place."),
                "emotional_tone": result.get("emotional_tone", "neutral"),
                "important_event": result.get("important_event"),
            }
            
        except Exception as e:
            print(f"⚠️ LLM error: {e}")
            # Fallback response
            return {
                "summary": "A conversation took place.",
                "emotional_tone": "neutral",
                "important_event": None,
            }
    
    def generate_whisper_text(
        self,
        name: str,
        relation: str,
        contextual_note: str = None,
        recent_memory: str = None,
    ) -> Optional[str]:
        """Generate a calm whisper text for a dementia patient.
        
        Args:
            name: Person's name
            relation: Relationship to user
            contextual_note: Caregiver-provided context (optional)
            recent_memory: Latest memory summary (optional)
        
        Returns:
            1-2 sentence whisper text, or None if failed
        """
        if not self._initialized:
            self.initialize()
        
        # Build context
        context_parts = []
        if contextual_note:
            context_parts.append(f"Caregiver Note: {contextual_note}")
        if recent_memory:
            context_parts.append(f"Recent Memory: {recent_memory}")
        
        context_str = "\n".join(context_parts) if context_parts else "No additional context."
        
        prompt = f"""Generate a gentle, dementia-safe audio whisper.

PERSON DETAILS:
- Name: {name}
- Relation: {relation}
{context_str}

STRICT RULES (CRITICAL - DO NOT VIOLATE):
❌ FORBIDDEN:
- NO timelines (\"three days ago\", \"last week\", \"yesterday\")
- NO inferred emotions (\"they seem happy\", \"you look tired\")
- NO system language (\"your memory says\", \"we detected\")
- NO lists or multiple facts
- NO medical terms or clinical language

✅ REQUIRED:
- Exactly 1-2 simple sentences
- Start with identity: \"This is [Name]\"
- Use present tense only
- Calm, warm, caregiver tone
- If context exists, add ONE gentle routine statement

SAFE PATTERNS:
- Core identity: \"This is [Name]. [He/She]'s your [relation].\"
- With context: \"This is [Name]. You usually [gentle routine].\"
- Familiarity: \"You know this person well. You're safe with them.\"
- Care-focused: \"[He/She] helps take care of you.\"

EXAMPLES OF PERFECT OUTPUT:
- \"This is Rahul. He's your grandson.\"
- \"This is Ananya. She's your daughter and visits often.\"  
- \"This is Doctor Sharma. You're safe with him.\"
- \"This is your friend. You enjoy spending time together.\"

Generate ONLY the whisper text (no quotes, no explanation)."""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a compassionate caregiver providing gentle, grounding reassurance to someone with dementia. Speak as if leaning in quietly to whisper comfort. Never mention time, emotions, or system details. Keep it simple, warm, and safe."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Lower for more consistent, safe output
                max_tokens=80,    # Shorter to enforce brevity
            )
            
            whisper_text = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            if whisper_text.startswith('"') and whisper_text.endswith('"'):
                whisper_text = whisper_text[1:-1]
            if whisper_text.startswith("'") and whisper_text.endswith("'"):
                whisper_text = whisper_text[1:-1]
            
            # Ensure proper sentence structure for ElevenLabs
            if not whisper_text.endswith(('.', '!', '?')):
                whisper_text += '.'
            
            print(f"🗣️ Generated whisper: {whisper_text}")
            return whisper_text
            
        except Exception as e:
            print(f"⚠️ LLM whisper error: {e}")
            # Ultra-safe fallback
            return f"This is {name}. You're safe with them."



# Singleton instance
llm_service = LLMService()
