# services.py — CLEAN MEDICAL REASONING ENGINE (STATE SAFE)

import json
from django.core.cache import cache

try:
    from rag.retriever import MedicalRetriever
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

from .followup_engine import FollowUpEngine
from .triage_engine import TriageEngine


# ─────────────────────────────────────────────
# STATE OBJECT (PERSISTED PER CONVERSATION)
# ─────────────────────────────────────────────

class DiagnosisState:
    def __init__(self):
        self.locked_disease = None
        self.confidence = 0
        self.resolved_slots = {}  # {disease: {slot: answer}}
        self.pending_question = None
        self.original_symptoms = ""
        self.cached_sections = {}
        self.high_risk = False
        self.active_system = None


# ─────────────────────────────────────────────
# MAIN SERVICE
# ─────────────────────────────────────────────

class GeminiService:

    # Minimum symptom signals required for diagnosis attempt.
    # If none of these are present, ask the user to describe more.
    SYMPTOM_SIGNALS = [
        "pain", "ache", "aching", "hurt", "hurting",
        "fever", "temperature", "cough", "cold",
        "bleed", "bleeding", "blood",
        "pimple", "pimples", "acne", "blackhead", "whitehead", "breakout",
        "rash", "itch", "itching", "swelling", "swollen",
        "dizzy", "dizziness", "faint", "fainting",
        "nausea", "vomit", "vomiting",
        "sore", "burning", "tingling",
        "breath", "breathing", "breathless",
        "weakness", "weak", "fatigue", "tired",
        "headache", "migraine",
        "chest", "stomach", "abdomen", "throat",
        "discharge", "infection", "wound",
        "collapse", "collapsed", "unconscious", "shaking",
    ]

    # Phrases that are vague enough to warrant asking for more detail
    # even if they contain a SYMPTOM_SIGNAL word.
    VAGUE_PHRASES = [
        "feel uneasy",
        "something feels wrong",
        "something is wrong",
        "not feeling well",
        "feeling off",
        "feel off",
        "don't feel good",
        "dont feel good",
        "feel bad",
        "feeling bad",
        "something wrong",
        "feels wrong",
        "feel strange",
        "feeling strange",
        "feel weird",
        "feeling weird",
    ]

    def __init__(self):
        self.followup = FollowUpEngine()
        self.triage = TriageEngine()
        self.disease_sources = self._load_disease_sources()

        if RAG_AVAILABLE:
            self.retriever = MedicalRetriever()
            self.rag_enabled = True
        else:
            self.rag_enabled = False

    def _load_disease_sources(self):
        """
        Build a lookup dict  {disease_name_lower: (display_name, source_url)}
        from disease_data.json. Only the first entry per disease name is kept.
        """
        try:
            import os
            from django.conf import settings
            path = os.path.join(settings.BASE_DIR, "disease_data.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lookup = {}
            for entry in data:
                name = entry.get("disease", "")
                source = entry.get("source", "")
                key = name.lower().strip()
                if key and source and key not in lookup:
                    lookup[key] = (name, source)
            return lookup
        except Exception as e:
            print(f"[GeminiService] Could not load disease_data.json: {e}")
            return {}

    # ─────────────────────────────────────────
    # ENTRY POINT
    # ─────────────────────────────────────────

    def get_health_advice(self, user_input, conversation_id):
        text_lower = user_input.strip().lower()

        # EDUCATIONAL CHECK FIRST — single disease names must bypass word-count guard
        if self._is_educational(user_input):
            self._reset_state(conversation_id)
            return self._render_educational(user_input)

        # GUARD 1: Reject garbage / trivially short / keyword-only input
        if (
            not any(c.isalnum() for c in user_input)
            or len(user_input.split()) < 3
            or text_lower in ["help", "???", "test"]
        ):
            self._reset_state(conversation_id)
            return "<p style='color: var(--text-primary); line-height: 1.6;'>Please describe your symptoms in a few words so I can help you.</p>"

        # GUARD 2: ABSOLUTE TRIAGE OVERRIDE (BEFORE EVERYTHING)
        triage_result = self.triage.assess(user_input)
        if triage_result:
            self._reset_state(conversation_id)
            return self._render_emergency(triage_result)

        # GUARD 1.5: Vague input with no actionable symptom signal → ask for detail
        # Runs AFTER triage so emergencies phrased vaguely still get caught above.
        if self._is_vague_input(text_lower):
            self._reset_state(conversation_id)
            return "<p style='color: var(--text-primary); line-height: 1.6;'>Could you describe your symptoms in a bit more detail? For example, where does it hurt, or what exactly feels wrong?</p>"

        state = self._load_state(conversation_id)

        # 3. Follow-up answer (STRICT)
        if self._is_followup_payload(user_input):
            return self._handle_followup(user_input, state, conversation_id)

        # 4. NEW COMPLAINT DETECTION (CRITICAL)
        if state.locked_disease and self._is_new_complaint(user_input, state):
            self._reset_state(conversation_id)
            return self.get_health_advice(user_input, conversation_id)

        # 5. Educational query (NO STATE)
        if self._is_educational(user_input):
            self._reset_state(conversation_id)
            return self._render_educational(user_input)

        # 6. If diagnosis locked → refine only
        if state.locked_disease:
            return self._refine(state, conversation_id)

        # 7. New diagnosis
        return self._diagnose(user_input, state, conversation_id)

    # ─────────────────────────────────────────
    # VAGUE INPUT DETECTION
    # ─────────────────────────────────────────

    def _is_vague_input(self, text_lower):
        """
        Returns True if the input matches a known vague phrase OR
        contains no recognisable symptom signal at all.

        Runs AFTER triage — emergency inputs are already handled by then.
        """
        # Explicit vague phrase list takes priority
        if any(phrase in text_lower for phrase in self.VAGUE_PHRASES):
            return True

        # No symptom signal found in the entire input
        return not any(signal in text_lower for signal in self.SYMPTOM_SIGNALS)

    # ─────────────────────────────────────────
    # STATE MANAGEMENT
    # ─────────────────────────────────────────

    def _load_state(self, cid):
        state = cache.get(f"diag:{cid}")
        if not state:
            state = DiagnosisState()
        return state

    def _save_state(self, cid, state):
        cache.set(f"diag:{cid}", state, timeout=3600)

    def _reset_state(self, cid):
        cache.delete(f"diag:{cid}")

    # ─────────────────────────────────────────
    # INTENT DETECTION
    # ─────────────────────────────────────────

    def _is_new_complaint(self, user_input, state):
        """Detect if user switched to unrelated symptoms (body system based)"""
        if not state.locked_disease or not state.active_system:
            return False
        new_system = self._detect_body_system(user_input)
        return new_system != state.active_system

    def _is_educational(self, text):
        if len(text.split()) > 3:
            return False
        return text.strip().lower() in [
            "tuberculosis", "tb", "diabetes", "asthma",
            "hypertension", "dengue", "malaria", "typhoid",
            "heart attack", "stroke", "cancer"
        ]

    def _is_followup_payload(self, text):
        try:
            data = json.loads(text)
            return data.get("type") == "FOLLOWUP_ANSWER"
        except:
            return False

    # ─────────────────────────────────────────
    # DIAGNOSIS
    # ─────────────────────────────────────────

    def _diagnose(self, text, state, cid):
        if not self.rag_enabled:
            return self._fallback()

        chunks = self.retriever.retrieve(text, top_k=5)
        diseases = {}

        for c in chunks:
            d = c["metadata"]["disease_name"]
            diseases.setdefault(d, 0)
            diseases[d] += c.get("score", 0.3)

        if not diseases:
            return self._fallback()

        RED_FLAG_TERMS = [
            "chest pain", "sweating", "shortness of breath",
            "left arm", "face droop", "slurred speech",
            "worst headache", "blood in cough", "blue lips"
        ]
        has_red_flags = any(term in text.lower() for term in RED_FLAG_TERMS)
        if has_red_flags:
            EXCLUDED_DISEASES = ["Panic Disorder", "Anxiety", "Generalized Anxiety Disorder"]
            diseases = {k: v for k, v in diseases.items() if k not in EXCLUDED_DISEASES}

        if not diseases:
            return self._fallback()

        ranked = sorted(diseases.items(), key=lambda x: x[1], reverse=True)
        primary, score = ranked[0]

        BANNED_DIAGNOSES = {"cough", "fever", "pain", "headache", "fatigue", "nausea"}
        if primary.lower() in BANNED_DIAGNOSES:
            triage_result = self.triage.assess(text)
            if triage_result:
                self._reset_state(cid)
                return self._render_emergency(triage_result)
            return self._fallback()

        confidence = min(int((score / sum(diseases.values())) * 100), 70)

        state.locked_disease = primary
        state.confidence = confidence
        state.original_symptoms = text
        state.active_system = self._detect_body_system(text)

        if primary not in state.resolved_slots:
            state.resolved_slots[primary] = {}
        state.resolved_slots[primary] = self.followup.extract_resolved_slots(text, state.active_system)

        state.cached_sections = {
            c["metadata"]["section"]: c["text"]
            for c in chunks if c["metadata"]["disease_name"] == primary
        }

        self._save_state(cid, state)
        return self._render(state)

    # ─────────────────────────────────────────
    # FOLLOW-UP HANDLING
    # ─────────────────────────────────────────

    def _handle_followup(self, payload, state, cid):
        data = json.loads(payload)
        qid = data["question_id"]
        ans = data["answer"]

        if state.locked_disease not in state.resolved_slots:
            state.resolved_slots[state.locked_disease] = {}

        state.resolved_slots[state.locked_disease][qid] = ans
        state.pending_question = None
        state.original_symptoms += f", {qid.replace('_', ' ')}: {ans}"

        CONFIDENCE_RULES = {
            'white_patches': {'Yes': 15, 'No': -5, 'Not sure': 0},
            'duration': {'1-2 days': 5, '3-5 days': 8, 'More than 5 days': -5},
            'painful': {'Yes': 5, 'No': -2},
            'itching': {'Yes, severe': -8, 'Yes, mild': 0, 'No': 5},
            'difficulty_swallowing': {'Mild': 5, 'Moderate': 8, 'Severe': 10},
            'cough_type': {'Dry': 5, 'With phlegm': 8, 'Both': 3}
        }

        delta = CONFIDENCE_RULES.get(qid, {}).get(ans, 5)

        if qid == "duration" and ans == "More than 5 days":
            if "Viral" in state.locked_disease or "Fever" in state.locked_disease:
                if not hasattr(state, 'flags'):
                    state.flags = set()
                state.flags.add("PROLONGED_SYMPTOMS")

        if "Acne" in state.locked_disease and qid == "itching" and ans == "Yes, severe":
            state.confidence = min(state.confidence, 60)
        else:
            state.confidence = max(0, min(state.confidence + delta, 90))

        self._save_state(cid, state)
        return self._render(state)

    # ─────────────────────────────────────────
    # REFINEMENT (NO RAG)
    # ─────────────────────────────────────────

    def _refine(self, state, cid):
        self._save_state(cid, state)
        return self._render(state)

    # ─────────────────────────────────────────
    # RENDERING
    # ─────────────────────────────────────────

    def _render(self, state):
        confidence_label = self._get_confidence_label(state.confidence)
        symptoms = self._extract_symptoms(state.original_symptoms)

        next_q = self.followup.get_next_question(
            state.locked_disease,
            state.resolved_slots.get(state.locked_disease, {})
        )
        is_complete = self._is_followup_complete(state)
        show_followup = next_q and state.confidence < 85 and not is_complete

        html = self._render_primary_condition(state.locked_disease, state.confidence, confidence_label)
        html += self._render_reasoning(symptoms, state.locked_disease, "FOLLOWUP" if state.resolved_slots.get(state.locked_disease) else "DIAGNOSTIC")
        html += self._render_disease_remedies(state.locked_disease)

        if hasattr(state, 'flags') and 'PROLONGED_SYMPTOMS' in state.flags:
            html += self._render_escalation_warning()

        if show_followup:
            html += self._render_followup_card(next_q)
        else:
            html += self._render_reassurance()

        return html

    def _render_primary_condition(self, disease, confidence, label):
        return f"""
        <div style='margin-bottom: 20px; padding: 12px; background: var(--bg-glass); border-radius: 12px; border: 1px solid var(--border);'>
            <p style='color: var(--text-primary); font-weight: 600; margin-bottom: 6px;'>Most likely condition: {disease}</p>
            <p style='color: var(--text-secondary); font-size: 0.95em; margin: 0;'>Confidence: {label} ({confidence}%)</p>
        </div>
        """

    def _render_reasoning(self, symptoms, disease, mode):
        symptom_phrase = ", ".join(symptoms) if symptoms else "your symptoms"
        return f"""
        <p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>Based on the combination of {symptom_phrase}, this appears to be {disease.lower()}.</p>
        """

    # ─────────────────────────────────────────
    # UI BLOCKS
    # ─────────────────────────────────────────

    def _extract_resolved_slots(self, text):
        return self.followup.extract_resolved_slots(text)

    def _detect_body_system(self, text):
        t = text.lower()
        if any(term in t for term in ['pimple', 'acne', 'skin', 'rash']):
            return 'DERMATOLOGY'
        if any(term in t for term in ['throat', 'tonsil', 'ear', 'nose']):
            return 'ENT'
        if any(term in t for term in ['cough', 'breathing', 'chest']):
            return 'RESPIRATORY'
        if any(term in t for term in ['stomach', 'abdomen', 'belly']):
            return 'GASTROINTESTINAL'
        if 'fever' in t and 'joint' in t:
            return 'SYSTEMIC'
        return 'GENERAL'

    def _extract_symptoms(self, text):
        symptoms = []
        t = text.lower()
        if "fever" in t:                               symptoms.append("fever")
        if "cough" in t:                               symptoms.append("cough")
        if "headache" in t:                            symptoms.append("headache")
        if "throat" in t or "tonsil" in t:            symptoms.append("sore throat")
        if "nose" in t or "runny" in t or "running" in t: symptoms.append("runny nose")
        if "joint" in t:                               symptoms.append("joint pain")
        if "rash" in t:                                symptoms.append("rash")
        if "pimple" in t or "acne" in t:              symptoms.append("skin breakouts")
        return symptoms

    def _get_confidence_label(self, confidence):
        if confidence < 40:   return "Possible"
        elif confidence < 70: return "Likely"
        else:                 return "Very likely"

    def _is_followup_complete(self, state):
        if any(term in state.locked_disease for term in ["Tuberculosis", "TB", "Cancer", "Stroke", "Heart Attack"]):
            return True
        AUTO_SLOTS = {'fever', 'cough', 'painful', 'itching', 'vomiting', 'breathing', 'swelling', 'chills'}
        disease_slots = state.resolved_slots.get(state.locked_disease, {})
        answered_count = sum(1 for k in disease_slots.keys() if k not in AUTO_SLOTS)
        return answered_count >= 2

    def _render_disease_remedies(self, disease):
        remedies = []
        recovery_text = "Most mild infections improve within 3-5 days."

        if "Acne" in disease:
            remedies = [
                "Cleanse face twice daily with gentle cleanser",
                "Avoid touching or picking at affected areas",
                "Use oil-free, non-comedogenic products",
                "Consider benzoyl peroxide or salicylic acid (2.5%)"
            ]
            recovery_text = "Visible improvement usually takes 4-8 weeks with consistent care."
        elif "Viral" in disease or "Fever" in disease:
            remedies = [
                "Rest and get adequate sleep",
                "Drink plenty of warm fluids (water, herbal tea)",
                "Steam inhalation to ease congestion",
                "Paracetamol for fever (follow package instructions)"
            ]
            recovery_text = "Symptoms usually improve within 3-5 days."
        elif "Throat" in disease or "Tonsil" in disease or "Pharyngitis" in disease:
            remedies = [
                "Gargle with warm salt water 2-3 times daily",
                "Drink warm fluids (soup, tea, warm water)",
                "Rest your voice and get adequate sleep",
                "Avoid cold drinks and smoking",
                "Paracetamol for pain or fever (as directed)"
            ]
            recovery_text = "Most mild throat infections improve within 3-5 days."
        else:
            remedies = [
                "Rest and hydrate well",
                "Avoid irritants",
                "Paracetamol for pain/fever (if needed)"
            ]

        html = "<div style='margin: 20px 0; padding: 14px; background: var(--bg-glass); border-radius: 12px; border-left: 3px solid var(--success);'>"
        html += "<p style='color: var(--text-primary); font-weight: 600; margin-bottom: 10px;'>What you can do at home:</p>"
        html += "<ul style='color: var(--text-primary); line-height: 1.8; margin: 0; padding-left: 24px;'>"
        for remedy in remedies:
            html += f"<li>{remedy}</li>"
        html += "</ul>"
        html += f"<p style='margin-top: 10px; font-size: 0.9em; color: var(--text-secondary);'>{recovery_text}</p>"
        html += "</div>"
        return html

    def _render_escalation_warning(self):
        return f"""
        <div style='margin: 20px 0; padding: 14px; background: #fff3cd; border-radius: 12px; border-left: 3px solid #ff9800;'>
            <p style='color: #e65100; font-weight: 600; margin-bottom: 6px;'>⚠️ Prolonged Symptoms</p>
            <p style='color: #2d3436; font-size: 0.95em; margin: 0;'>Because symptoms have lasted more than 5 days, medical evaluation is recommended to rule out complications.</p>
        </div>
        """

    def _followup_card(self, q):
        buttons = "".join(
            f"<button class='answer-chip' data-question='{q['id']}' data-answer='{o}' style='padding: 6px 14px; border-radius: 999px; border: 1px solid var(--border); background: transparent; cursor: pointer; transition: 0.2s ease;'>{o}</button>"
            for o in q["options"]
        )
        return f"""
        <div style='margin: 20px 0;'>
            <p style='color: var(--text-primary); font-weight: 600; margin-bottom: 10px;'>One more question to understand better:</p>
            <div style='margin-bottom: 12px; padding: 12px; background: var(--bg-glass); border-radius: 12px; border-left: 3px solid var(--accent);'>
                <p style='color: var(--text-primary); margin-bottom: 8px;'>{q['question']}</p>
                <div style='display: flex; gap: 10px; flex-wrap: wrap;'>
                    {buttons}
                </div>
            </div>
        </div>
        """

    def _render_followup_card(self, q):
        return self._followup_card(q)

    def _render_reassurance(self):
        return f"""
        <p style='color: var(--text-secondary); font-size: 0.95em; line-height: 1.6; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); font-style: italic;'>
        This condition usually improves with appropriate care.
        If symptoms worsen or persist, consult a doctor.
        </p>
        """

    # ─────────────────────────────────────────
    # SPECIAL RENDERS
    # ─────────────────────────────────────────

    def _render_emergency(self, triage):
        level   = triage["level"]
        disease = triage["disease"]
        message = triage["message"]

        if level == "IMMEDIATE_EMERGENCY":
            color  = "#d63031"
            bg     = "#ffe5e5"
            border = "#ff6b6b"
            icon   = "🚨"
            title  = "IMMEDIATE EMERGENCY"
            instructions = [
                "Call emergency services (108) immediately",
                "Do NOT wait — seek professional care now",
                "If alone, ask someone nearby for help",
                "Stay calm and follow dispatcher instructions"
            ]
            footer = "Emergency contact (India): Call 108"
        else:
            color  = "#e65100"
            bg     = "#fff3cd"
            border = "#ff9800"
            icon   = "⚠️"
            title  = "URGENT MEDICAL EVALUATION REQUIRED"
            instructions = [
                "Visit a doctor or clinic within 24 hours",
                "Do NOT delay seeking medical attention",
                "Bring any relevant medical records",
                "Avoid self-medication"
            ]
            footer = "If symptoms worsen suddenly, seek emergency care (India: 108)"

        html = f"""
        <div style='margin-bottom: 20px; padding: 14px; background: {bg}; border-radius: 12px; border: 2px solid {border};'>
            <p style='color: {color}; font-weight: 700; font-size: 1.1em; margin-bottom: 8px;'>{icon} {title}</p>
            <p style='color: #2d3436; font-size: 0.95em; margin: 0;'>{message}</p>
        </div>

        <p style='color: var(--text-primary); font-weight: 600; margin-bottom: 8px;'>Suspected condition:</p>
        <p style='color: var(--text-primary); margin-bottom: 16px; padding: 10px; background: var(--bg-glass); border-radius: 8px;'>{disease}</p>

        <div style='margin: 20px 0; padding: 14px; background: {bg}; border-radius: 12px; border-left: 3px solid {color};'>
            <p style='color: {color}; font-weight: 600; margin-bottom: 10px;'>Required actions:</p>
            <ul style='color: #2d3436; line-height: 1.8; margin: 0; padding-left: 24px;'>
                {''.join(f'<li>{i}</li>' for i in instructions)}
            </ul>
        </div>

        <p style='color: var(--text-secondary); font-size: 0.9em; line-height: 1.6; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); font-style: italic;'>
        This is a safety-critical alert based on symptom patterns. Professional medical evaluation is mandatory. {footer}
        </p>
        """

        # SAFETY ASSERTION: Emergency output must never contain forbidden terms
        forbidden = ["home", "rest", "paracetamol", "confidence", "panic"]
        for term in forbidden:
            assert term not in html.lower(), f"SAFETY VIOLATION: Emergency render contains '{term}'"

        return html

    def _render_educational(self, topic):
        # Look up the canonical name + source URL from disease_data.json
        topic_lower = topic.strip().lower()
        match = self.disease_sources.get(topic_lower)

        # Fuzzy fallback: check if input is a substring of any disease key
        if not match:
            for key, value in self.disease_sources.items():
                if topic_lower in key or key.startswith(topic_lower):
                    match = value
                    break

        if match:
            display_name, source_url = match
            source_block = f"""
        <div style='margin-top: 20px; padding: 12px; background: var(--bg-glass); border-radius: 10px; border: 1px solid var(--border);'>
            <p style='color: var(--text-secondary); font-size: 0.9em; margin-bottom: 6px;'>📚 Learn more from a trusted source:</p>
            <a href='{source_url}' target='_blank' rel='noopener noreferrer'
               style='color: var(--accent); font-size: 0.95em; word-break: break-all;'>{source_url}</a>
        </div>"""
        else:
            display_name = topic
            source_block = ""

        return f"""
        <div style='margin-bottom: 20px; padding: 12px; background: var(--bg-glass); border-radius: 12px; border: 1px solid var(--border);'>
            <p style='color: var(--text-primary); font-weight: 600; margin-bottom: 6px;'>About {display_name}</p>
        </div>
        <p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>This is general information about {display_name}.</p>
        {source_block}
        <p style='color: var(--text-secondary); font-size: 0.95em; line-height: 1.6; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); font-style: italic;'>For personalized guidance, please describe your specific symptoms.</p>
        """

    def _fallback(self):
        return "<p style='color: var(--text-primary); line-height: 1.6;'>I'm currently unable to provide specific medical information. Please consult a healthcare professional.</p>"