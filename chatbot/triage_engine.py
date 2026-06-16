import json
import os
from django.conf import settings


class TriageEngine:
    """Dataset-driven emergency detection - runs BEFORE RAG"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self):
        try:
            path = os.path.join(settings.BASE_DIR, "triage_rules.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("rules", [])
        except Exception as e:
            print(f"[TriageEngine] Failed to load triage_rules.json: {e}")
            return []
    
    def _normalize(self, text):
        """
        Normalize layman symptom phrases to canonical medical keywords.
        Order matters — longer/more-specific phrases must come BEFORE shorter ones.
        """
        replacements = [
            # ── BREATHING ──────────────────────────────────────────────────
            ("finding it very hard to breathe",   "shortness of breath"),
            ("finding it hard to breathe",        "shortness of breath"),
            ("very hard to breathe",              "shortness of breath"),
            ("hard to breathe",                   "shortness of breath"),
            ("shortness in breathing",            "shortness of breath"),
            ("trouble breathing",                 "shortness of breath"),
            ("struggling to breathe",             "shortness of breath"),
            ("difficulty breathing",              "shortness of breath"),
            ("severe breathing",                  "shortness of breath"),
            ("unable to breathe",                 "shortness of breath"),
            ("cannot breathe",                    "shortness of breath"),
            ("can't breathe",                     "shortness of breath"),
            ("breathlessness",                    "shortness of breath"),

            # ── CHEST ──────────────────────────────────────────────────────
            ("chest is hurting very badly",       "chest pain"),
            ("chest is hurting badly",            "chest pain"),
            ("chest is hurting",                  "chest pain"),
            ("chest hurting",                     "chest pain"),
            ("severe chest pain",                 "chest pain"),
            ("crushing chest pain",               "chest pain"),
            ("chest tightness",                   "chest pain"),
            ("heart pain",                        "chest pain"),
            ("tight chest",                       "chest pain"),

            # ── SWEATING ───────────────────────────────────────────────────
            ("sweating a lot",                    "sweating"),
            ("sweating heavily",                  "sweating"),
            ("profuse sweating",                  "sweating"),
            ("night sweating",                    "night sweats"),
            ("sweating at night",                 "night sweats"),

            # ── COUGH / TB ─────────────────────────────────────────────────
            ("chronic coughing",                  "chronic cough"),
            ("long-term cough",                   "chronic cough"),
            ("long term cough",                   "chronic cough"),
            ("persistent cough",                  "chronic cough"),
            ("coughing for weeks",                "chronic cough"),
            ("cough for weeks",                   "chronic cough"),
            ("cough for months",                  "chronic cough"),
            ("been coughing for many days",       "chronic cough"),
            ("been coughing for weeks",           "chronic cough"),
            ("coughing for many days",            "chronic cough"),

            # ── BLOOD IN COUGH ─────────────────────────────────────────────
            # IMPORTANT: normalize BEFORE generic "cough" replacements
            ("coughing up blood",                 "coughing blood"),
            ("blood in cough",                    "coughing blood"),
            ("blood in sputum",                   "coughing blood"),
            ("blood in phlegm",                   "coughing blood"),
            ("blood when coughing",               "coughing blood"),
            ("blood with cough",                  "coughing blood"),
            ("spitting blood",                    "coughing blood"),
            ("spit blood",                        "coughing blood"),
            # Indirect layman phrases — "there is blood" after cough context
            ("sometimes there is blood",          "coughing blood"),
            ("there is blood",                    "coughing blood"),
            ("blood came out",                    "coughing blood"),
            ("hemoptysis",                        "coughing blood"),

            # ── WEIGHT / SYSTEMIC ──────────────────────────────────────────
            ("losing weight",                     "weight loss"),

            # ── STROKE — SPEECH ────────────────────────────────────────────
            ("can't speak properly",              "slurred speech"),
            ("cannot speak properly",             "slurred speech"),
            ("can't speak",                       "slurred speech"),
            ("cannot speak",                      "slurred speech"),
            ("slurred words",                     "slurred speech"),
            ("unable to speak",                   "slurred speech"),
            ("difficulty speaking",               "slurred speech"),

            # ── STROKE — FACE ──────────────────────────────────────────────
            # Map ALL variants to the SAME keyword that is in JSON
            ("face feels droopy",                 "facial drooping"),
            ("face feels numb",                   "facial drooping"),
            ("face droops",                       "facial drooping"),
            ("facial droop",                      "facial drooping"),
            ("face drooping",                     "facial drooping"),
            ("face droopy",                       "facial drooping"),
            ("mouth is drooping",                 "facial drooping"),

            # ── STROKE — LIMBS ─────────────────────────────────────────────
            ("one side weakness",                 "sudden weakness"),
            ("one sided weakness",                "sudden weakness"),
            ("one side weak",                     "sudden weakness"),
            ("arm weak",                          "arm weakness"),
            ("weak arm",                          "arm weakness"),
            ("leg weak",                          "leg weakness"),
            ("weak leg",                          "leg weakness"),

            # ── HEADACHE ───────────────────────────────────────────────────
            ("worst headache i've ever had",      "worst headache"),
            ("worst headache i have ever had",    "worst headache"),
            ("worst headache of my life",         "worst headache"),
            ("worst headache ever",               "worst headache"),
            ("sudden severe headache",            "worst headache"),

            # ── SEIZURE / COLLAPSE ─────────────────────────────────────────
            ("suddenly collapsed",                "collapsed"),
            ("suddenly fell down",                "collapsed"),
            ("fell to the ground",                "collapsed"),
            ("started shaking",                   "started shaking"),
            ("shaking uncontrollably",            "started shaking"),
            ("body is shaking",                   "started shaking"),
            ("not waking up",                     "not waking up"),
            ("won't wake up",                     "not waking up"),
            ("wont wake up",                      "not waking up"),
            ("cannot wake up",                    "not waking up"),
            ("not responding",                    "not waking up"),

            # ── CYANOSIS ───────────────────────────────────────────────────
            ("lips look bluish",                  "cyanosis"),
            ("lips look blue",                    "cyanosis"),
            ("bluish lips",                       "cyanosis"),
            ("blue lips",                         "cyanosis"),
            ("lips turning blue",                 "cyanosis"),
            ("fingertips blue",                   "cyanosis"),

            # ── DENGUE / BODY PAIN ─────────────────────────────────────────
            ("terrible body pain",                "body pain"),
            ("severe body pain",                  "body pain"),
            ("bad body pain",                     "body pain"),
            ("body is aching",                    "body pain"),
            ("whole body pain",                   "body pain"),
            ("very high fever",                   "high fever"),
            ("extremely high fever",              "high fever"),
            ("high grade fever",                  "high fever"),
            ("red rashes",                        "red rashes"),
            ("red spots",                         "rash"),
            ("skin rash",                         "rash"),

            # ── SEPSIS ─────────────────────────────────────────────────────
            ("extremely weak",                    "very weak"),
            ("feel extremely weak",               "very weak"),
            ("feeling very weak",                 "very weak"),
            ("very confused",                     "confused"),
            ("feeling confused",                  "confused"),
        ]

        t = text.lower()
        for source, target in replacements:
            t = t.replace(source, target)
        return t
    
    def assess(self, user_input):
        """
        Check for dangerous symptom combinations.
        Returns triage dict if danger detected, None otherwise.
        """
        text = self._normalize(user_input)
        
        for rule in self.rules:
            keywords = rule.get("keywords", [])
            trigger_type = rule.get("trigger_type", "ANY_2")
            
            matched = [k for k in keywords if k in text]
            hits = len(matched)
            
            triggered = False
            if trigger_type == "ANY_1" and hits >= 1:
                triggered = True
            elif trigger_type == "ALL" and hits == len(keywords):
                triggered = True
            elif trigger_type == "ANY_2" and hits >= 2:
                triggered = True
            
            # Severity modifier override: 1 keyword + severity word → trigger
            if not triggered and "severity_modifiers" in rule:
                severity_words = rule["severity_modifiers"]
                if hits >= 1 and any(s in user_input.lower() for s in severity_words):
                    triggered = True
            
            if triggered:
                print(f"[TRIAGE HIT] {rule['disease']} via {hits} keywords: {matched}")
                return {
                    "level": rule["level"],
                    "disease": rule["disease"],
                    "action": "CALL_EMERGENCY" if rule["level"] == "IMMEDIATE_EMERGENCY" else "URGENT_CLINIC_VISIT",
                    "message": rule["message"]
                }
        
        print(f"[TRIAGE MISS] Input='{user_input[:50]}...' | Checked {len(self.rules)} rules")
        return None