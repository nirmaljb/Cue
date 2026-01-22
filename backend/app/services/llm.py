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
    
    def generate_whisper(self, name: str, relation: str, routines: list[dict] = None, contextual_note: str = None) -> str:
        """Generate 3-4 sentence dementia-safe whisper for ElevenLabs TTS.
        
        Creates structured comfort message using database routines.
        
        Args:
            name: Person's name
            relation: Relationship (e.g., "your son")
            routines: List of routine dicts from database (optional)
            contextual_note: Caregiver's note (optional, fallback)
        
        Returns:
            Whisper text (3-4 sentences, ~30 words max)
        """
        if not self._initialized:
            self.initialize()
        
        # Build routine context for LLM
        routine_text = ""
        if routines and len(routines) > 0:
            # Use top 2 routines
            routine_text = "\n".join([f"- {r['text']}" for r in routines[:2]])
        
        # Prepare prompt
        if routines and len(routines) > 0:
            # WITH MEMORIES: Use routines - MUST be 4 sentences
            prompt = f"""You MUST generate EXACTLY 4 separate sentences for a dementia patient.

Person: {name}
Relation: {relation}
Known routines:
{routine_text}

OUTPUT FORMAT (REQUIRED - ALL 4 SENTENCES):
Sentence 1: "This is [name]. He's/She's your [relation]."
Sentence 2: "You usually feel [comfort feeling] around him/her."
Sentence 3: "[Use one of the routines above]"
Sentence 4: "[Reassurance: You can take your time. OR You're safe here. OR There's no rush.]"

EXAMPLE OUTPUT:
This is Rahul. He's your close friend.
You usually feel comfortable around him.
You both enjoy talking about cricket.
You can take your time.

CRITICAL: You MUST output exactly 4 sentences. Do NOT combine them into 1-2 sentences."""
        else:
            # NO MEMORIES: Short fallback
            note = f" {contextual_note}" if contextual_note else ""
            prompt = f"""Generate a SHORT, dementia-safe whisper for a person with dementia seeing someone they know.

Person: {name}
Relation: {relation}{note}

Create 1-2 SHORT sentences:
- Present tense
- Simple and warm
- Reassuring

Example: "This is {name}. You're safe with them."

Return ONLY the sentences, nothing else."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You create warm, dementia-safe whispers. Always use present tense and simple language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=150,
            )
            
            whisper_text = response.choices[0].message.content.strip()
            # Remove quotes if present
            whisper_text = whisper_text.strip('"').strip("'")
            
            print(f"🗣️ Generated whisper: {whisper_text}")
            return whisper_text
            
        except Exception as e:
            print(f"⚠️ LLM whisper error: {e}")
            # Ultra-safe fallback
            return f"This is {name}. You're safe with them."
    def extract_routines_from_memories(self, memories: list[dict]) -> list[dict]:
        """Extract routine patterns from conversation memories.
        
        Args:
            memories: List of memory dicts with 'summary' field
        
        Returns:
            List of routines: [{"text": "...", "confidence": 0.X, "pattern_type": "..."}]
        """
        if not self._initialized:
            self.initialize()
        
        if not memories:
            return []
        
        # Build memory summary text
        memory_summaries = "\n".join(
            f"{i+1}. {m.get('summary', '')}" 
            for i, m in enumerate(memories[:20])  # Limit to 20 most recent
        )
        
        prompt = f"""Analyze these conversation summaries to find SPECIFIC routine patterns:

{memory_summaries}

Extract ONLY concrete, specific patterns. REJECT generic/vague statements.

✅ GOOD Examples (Specific):
- "You both talk about cricket matches."
- "You discuss coding competitions."
- "You visit a chicken shop together."

❌ BAD Examples (Too generic):
- "You often reminisce about the past."
- "You enjoy talking together."
- "You share memories."

Requirements:
- Must mention SPECIFIC activities, topics, or places
- Must be concrete and meaningful
- Only include if clearly mentioned
- Skip vague patterns

Return as JSON array:
[
  {{"text": "You both talk about cricket.", "confidence": 0.85, "pattern_type": "emotional"}},
  {{"text": "You discuss coding daily.", "confidence": 0.75, "pattern_type": "action"}}
]

Return empty array [] if NO specific patterns found."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You extract routine patterns from conversations. Always respond in valid JSON array format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
            )
            
            content = response.choices[0].message.content.strip()
            print(f"🤖 LLM routine extraction response: {content[:300] if content else 'EMPTY'}")
            
            # Parse JSON
            import json
            try:
                routines = json.loads(content)
                if isinstance(routines, list):
                    print(f"✅ Successfully parsed {len(routines)} routines")
                    return routines
                else:
                    print(f"⚠️ LLM returned non-list type: {type(routines)}")
                    return []
            except json.JSONDecodeError as je:
                print(f"⚠️ Failed to parse routines JSON")
                print(f"   Content: {content[:200] if content else 'EMPTY'}")
                print(f"   Error: {je}")
                return []
                
        except Exception as e:
            print(f"⚠️ Routine extraction error: {e}")
            return []
    
    def select_best_routine(self, routines: list[dict], recent_memory: str = None) -> Optional[str]:
        """Select the most relevant routine for display.
        
        Args:
            routines: List of routine dicts
            recent_memory: Optional recent memory summary for context
        
        Returns:
            Selected routine text or None
        """
        if not self._initialized:
            self.initialize()
        
        if not routines:
            return None
        
        if len(routines) == 1:
            return routines[0]["text"]
        
        # Build routines list
        routine_list = "\n".join(
            f"{i+1}. {r['text']} (confidence: {r.get('confidence', 0.5)})"
            for i, r in enumerate(routines[:5])
        )
        
        context_text = f"Recent conversation: {recent_memory}" if recent_memory else "No recent context."
        
        prompt = f"""Choose the ONE most relevant routine to display:
    
    Available routines:
    {routine_list}
    
    {context_text}
    
    Select the routine that is:
    1. Most relevant to recent conversation (if any)
    2. Most comforting/reassuring
    3. Most concrete (avoid vague patterns)
    
    Return ONLY the chosen routine text, nothing else."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You select the most relevant routine for display. Return ONLY the routine text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=50,
            )
            
            selected = response.choices[0].message.content.strip()
            # Remove quotes if present
            selected = selected.strip('"').strip("'")
            return selected
            
        except Exception as e:
            print(f"⚠️ Routine selection error: {e}")
            # Fallback to highest confidence
            return max(routines, key=lambda r: r.get('confidence', 0.5))["text"]
    
    def transform_contextual_note_to_routine(self, contextual_note: str) -> str:
        """Transform contextual note into routine format (fallback when no memories).
        
        Args:
            contextual_note: Caregiver's note (e.g., "Grandson who visits on weekends")
        
        Returns:
            Routine-style sentence (e.g., "Your grandson usually visits on weekends.")
        """
        if not self._initialized:
            self.initialize()
        
        if not contextual_note or contextual_note.strip() == "":
            return "You know this person well."
        
        prompt = f"""Transform this contextual note into a warm, routine-style sentence:
    
    Input: "{contextual_note}"
    
    Format like:
    - "You usually have tea together."
    - "You both enjoy talking about cricket."
    - "Your grandson usually visits on weekends."
    
    Make it personal, warm, and present-tense.
    Return ONLY the transformed sentence, nothing else."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You transform contextual notes into warm routine sentences. Return ONLY the sentence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=30,
            )
            
            routine = response.choices[0].message.content.strip()
            # Remove quotes if present
            routine = routine.strip('"').strip("'")
            
            # Check if LLM returned empty
            if not routine or routine.strip() == "":
                print(f"⚠️ LLM returned empty for contextual note: '{contextual_note}'")
                # Fallback: use first 8 words or original
                words = contextual_note.split()
                if len(words) > 8:
                    return ' '.join(words[:8]) + "."
                return contextual_note
            
            print(f"✅ Transformed contextual note: '{contextual_note}' → '{routine}'")
            return routine
            
        except Exception as e:
            print(f"⚠️ Contextual note transformation error: {e}")
            # Fallback
            return f"You know {contextual_note}."
    
    def condense_to_few_words(self, text: str) -> str:
        """Condense text smartly - keep if already short and meaningful, otherwise condense.
        
        Args:
            text: Text to condense
        
        Returns:
            Short, condensed version (prefer full sentences if meaningful)
        """
        if not self._initialized:
            self.initialize()
        
        # If empty or None, return original
        if not text or text.strip() == "":
            return text if text else ""
        
        # If already short (under 8 words), keep it
        if len(text.split()) <= 8:
            return text
        
        prompt = f"""Condense this text to be SHORT but meaningful:

Input: "{text}"

Rules:
- If already clear and concise → Keep it as is
- If too wordy → Condense to essential meaning
- Prefer short full sentences over fragments
- Keep warmth and context
- Present tense

Examples:
"He is currently in his second year, pursuing B.Tech Computer Science" → "He is studying in University." OR "He is in his second year." OR "He is getting his engineering degree."
"You usually have tea together in the evening" → Keep it (already good)
"Your grandson who visits every weekend and brings flowers" → "Visits every weekend."

Return ONLY the condensed text, nothing else."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You condense text smartly. Keep if already good, condense if wordy. Return ONLY the text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=30,
            )
            
            condensed = response.choices[0].message.content.strip()
            # Remove quotes if present
            condensed = condensed.strip('"').strip("'")
            
            # If LLM returned empty, use original
            if not condensed or condensed == "":
                print(f"⚠️ LLM returned empty, using original: {text[:50]}")
                # Fallback: take first 10 words
                words = text.split()
                if len(words) > 10:
                    return ' '.join(words[:10])
                return text
            
            # Ensure reasonable length (max 12 words)
            if len(condensed.split()) > 12:
                # Fallback: take first 10 words
                condensed = ' '.join(text.split()[:10])
            
            return condensed
            
        except Exception as e:
            print(f"⚠️ Text condensing error: {e}")
            # Fallback: take first 10 words or return original if short
            words = text.split()
            if len(words) > 10:
                return ' '.join(words[:10])
            return text
    
    
    # Singleton instance


# Singleton instance
llm_service = LLMService()
