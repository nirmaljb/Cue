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
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
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
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
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


# Singleton instance
llm_service = LLMService()
