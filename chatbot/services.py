import os
import json
from django.conf import settings
try:
    from rag.retriever import MedicalRetriever
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

class GeminiService:
    def __init__(self):
        self.disease_data = self.load_disease_data()
        # Initialize RAG retriever if available
        if RAG_AVAILABLE:
            try:
                self.retriever = MedicalRetriever()
                self.rag_enabled = True
            except Exception as e:
                print(f"RAG initialization failed: {e}")
                self.rag_enabled = False
        else:
            self.rag_enabled = False
    
    def load_disease_data(self):
        """Load disease data from JSON file"""
        try:
            json_path = os.path.join(settings.BASE_DIR, 'disease_data.json')
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get('diseases', data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"Error loading disease data: {e}")
            return []
    
    def find_matching_disease(self, symptoms):
        """Find matching disease based on symptoms"""
        symptoms_lower = symptoms.lower()
        best_match = None
        max_matches = 0
        
        for disease in self.disease_data:
            matches = 0
            # Check symptoms
            for symptom in disease['symptoms']:
                if any(word in symptoms_lower for word in symptom.lower().split()):
                    matches += 1
            
            # Check disease name (handle both old and new format)
            disease_name = disease.get('disease_name', disease.get('disease', ''))
            if any(word in symptoms_lower for word in disease_name.lower().split()):
                matches += 2
            
            if matches > max_matches:
                max_matches = matches
                best_match = disease
        
        return best_match if max_matches > 0 else None
    
    def format_disease_response(self, disease_info):
        """Format disease information in humanized medical tone"""
        disease_name = disease_info.get('disease_name', disease_info.get('disease', 'Unknown'))
        
        # Calculate confidence percentage (70% for legacy matching)
        confidence_pct = 70
        
        # MANDATORY HEADER: Disease name and confidence
        response = f"<div style='margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--border);'>"
        response += f"<p style='color: var(--text-primary); font-size: 1.1em; font-weight: 600; margin-bottom: 6px;'>Condition: {disease_name}</p>"
        response += f"<p style='color: var(--text-secondary); font-size: 0.95em; margin-bottom: 0;'>Confidence: {confidence_pct}%</p>"
        response += "</div>"
        
        # Opening with empathy
        response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>Based on what you've shared, {disease_name.lower()} is a possible explanation for your symptoms.</p>"
        
        # Summary
        if 'summary' in disease_info:
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>{disease_info['summary']}</p>"
        
        # Symptoms
        if 'symptoms' in disease_info and disease_info['symptoms']:
            symptoms_text = ', '.join(disease_info['symptoms'])
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>People with this condition commonly experience {symptoms_text.lower()}.</p>"
        
        # Treatment
        if 'treatment' in disease_info and disease_info['treatment']:
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 8px;'><strong>Management typically includes:</strong></p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding-left: 24px;'>"
            for item in disease_info['treatment']:
                response += f"<li>{item}</li>"
            response += "</ul>"
        
        # Warning signs
        if 'warning_signs' in disease_info and disease_info['warning_signs']:
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 8px;'><strong>You should consider seeking medical attention if:</strong></p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding-left: 24px;'>"
            for item in disease_info['warning_signs']:
                response += f"<li>{item}</li>"
            response += "</ul>"
        
        # Prevention
        if 'prevention' in disease_info and disease_info['prevention']:
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 8px;'><strong>To help prevent this:</strong></p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding-left: 24px;'>"
            for item in disease_info['prevention']:
                response += f"<li>{item}</li>"
            response += "</ul>"
        
        # Soft disclaimer
        response += f"<p style='color: var(--text-secondary); font-size: 0.9em; line-height: 1.6; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border);'>If symptoms worsen or don't improve, it would be a good idea to speak with a healthcare professional who can examine you in person.</p>"
        
        return f"<div style='margin-bottom: 24px;'>{response}</div>"
    
    def get_severity_color(self, severity):
        """Get color for severity level"""
        colors = {
            'Low': '#2d2d2d',
            'Medium': '#444444', 
            'High': '#666666',
            'Critical': '#888888'
        }
        return colors.get(severity, '#2d2d2d')
    
    def get_rag_health_advice(self, symptoms):
        """Get health advice using RAG (Retrieval-Augmented Generation)"""
        try:
            # Retrieve relevant medical chunks
            retrieved_chunks = self.retriever.retrieve(symptoms, top_k=5)
            
            if not retrieved_chunks:
                return self.get_fallback_response()
            
            # Format retrieved knowledge for display
            return self.format_rag_response(retrieved_chunks, symptoms)
            
        except Exception as e:
            print(f"RAG retrieval failed: {e}")
            return self.get_fallback_response()
    
    def calculate_confidence(self, chunk_score, rank, total_chunks):
        """Calculate confidence score based on retrieval strength"""
        # Normalize score (0.0 to 1.0)
        base_score = min(chunk_score / 100.0, 1.0) if chunk_score > 1 else chunk_score
        # Apply rank penalty (first result gets highest weight)
        rank_weight = 1.0 - (rank * 0.1)
        confidence = base_score * max(rank_weight, 0.5)
        return round(min(confidence, 0.99), 2)
    
    def apply_symptom_role_weighting(self, disease_name, symptoms, sections):
        """Apply primary/secondary symptom weighting and negative evidence penalties"""
        symptoms_lower = symptoms.lower()
        disease_lower = disease_name.lower()
        
        # Primary symptom definitions (hallmark symptoms)
        primary_symptoms = {
            'diarrhea': ['loose stool', 'watery stool', 'diarrhea', 'urgency'],
            'gastritis': ['burning', 'acidity', 'acid reflux', 'heartburn', 'post-meal'],
            'tonsillitis': ['throat pain', 'sore throat', 'swollen tonsils', 'difficulty swallowing'],
            'cold': ['runny nose', 'congestion', 'sneezing', 'nasal'],
            'fever': ['fever', 'high temperature', 'chills'],
            'headache': ['headache', 'head pain', 'migraine'],
            'food poisoning': ['vomiting', 'nausea', 'contaminated food']
        }
        
        # Co-occurrence pairs that boost confidence
        co_occurrence_boost = 0
        if 'stomach pain' in symptoms_lower or 'abdominal pain' in symptoms_lower:
            if 'diarrhea' in symptoms_lower or 'loose stool' in symptoms_lower:
                if any(term in disease_lower for term in ['diarrhea', 'food poisoning', 'gastroenteritis']):
                    co_occurrence_boost = 0.15
            elif 'acidity' in symptoms_lower or 'burning' in symptoms_lower:
                if any(term in disease_lower for term in ['gastritis', 'indigestion', 'acidity']):
                    co_occurrence_boost = 0.15
        
        # Primary symptom matching
        primary_match_score = 0
        secondary_match_score = 0
        
        for disease_key, primary_list in primary_symptoms.items():
            if disease_key in disease_lower:
                matched_primary = sum(1 for symptom in primary_list if symptom in symptoms_lower)
                if matched_primary > 0:
                    primary_match_score = 0.30  # +30 points for primary match
                else:
                    # Negative evidence penalty: hallmark symptom missing
                    if len(primary_list) > 0:
                        primary_match_score = -0.25  # -25 points penalty
                break
        
        # Secondary symptoms (general symptoms)
        secondary_symptoms = ['pain', 'discomfort', 'tired', 'fatigue', 'weakness']
        matched_secondary = sum(1 for symptom in secondary_symptoms if symptom in symptoms_lower)
        if matched_secondary > 0:
            secondary_match_score = 0.10  # +10 points for secondary match
        
        total_adjustment = primary_match_score + secondary_match_score + co_occurrence_boost
        return total_adjustment
    
    def enforce_confidence_separation(self, sorted_diseases):
        """Enforce meaningful separation between top-ranked conditions"""
        if len(sorted_diseases) < 2:
            return sorted_diseases
        
        top_conf = sorted_diseases[0][1]['confidence']
        second_conf = sorted_diseases[1][1]['confidence']
        
        # Require at least 12% separation
        min_separation = 0.12
        current_separation = top_conf - second_conf
        
        if current_separation < min_separation:
            # Reduce secondary scores proportionally
            reduction_factor = 0.85
            for i in range(1, len(sorted_diseases)):
                sorted_diseases[i][1]['confidence'] *= reduction_factor
        
        return sorted_diseases
    
    def generate_ranking_explanation(self, sorted_diseases, symptoms):
        """Generate clinical reasoning explanation for ranking"""
        if len(sorted_diseases) < 2:
            return None
        
        top_disease = sorted_diseases[0][0]
        symptoms_lower = symptoms.lower()
        
        # Identify key symptom that drove ranking
        key_symptoms = {
            'diarrhea': 'loose stools',
            'gastritis': 'acidity or burning sensation',
            'tonsillitis': 'throat pain and swelling',
            'cold': 'nasal congestion',
            'fever': 'elevated temperature'
        }
        
        explanation = None
        for disease_key, symptom_desc in key_symptoms.items():
            if disease_key in top_disease.lower():
                explanation = f"{top_disease} ranks higher because {symptom_desc} strongly indicates this condition."
                break
        
        # Add why others ranked lower
        if len(sorted_diseases) > 1:
            lower_disease = sorted_diseases[-1][0]
            for disease_key, symptom_desc in key_symptoms.items():
                if disease_key in lower_disease.lower():
                    explanation += f" {lower_disease} is ranked lower because key symptoms like {symptom_desc} were not mentioned."
                    break
        
        return explanation
    
    def analyze_symptom_quality(self, symptoms):
        """Analyze symptom description quality and return confidence modifier"""
        symptoms_lower = symptoms.lower()
        words = symptoms_lower.split()
        
        # Base quality score
        quality_score = 1.0
        uncertainty_reasons = []
        
        # Age detection and modifier
        age_modifier = 1.0
        age_keywords = {'child': 0.95, 'kid': 0.95, 'baby': 0.9, 'infant': 0.9, 'elderly': 1.05, 'senior': 1.05, 'old': 1.05}
        for keyword, modifier in age_keywords.items():
            if keyword in symptoms_lower:
                age_modifier = modifier
                break
        quality_score *= age_modifier
        
        # Comorbidity detection
        comorbidity_keywords = ['diabetes', 'diabetic', 'asthma', 'asthmatic', 'hypertension', 'blood pressure', 'heart disease', 'immunocompromised']
        has_comorbidity = any(kw in symptoms_lower for kw in comorbidity_keywords)
        if has_comorbidity:
            quality_score *= 1.08  # 8% boost for comorbidity context
        
        # Severity analysis
        severity_keywords = {
            'mild': 1.0,
            'slight': 1.0,
            'moderate': 1.15,
            'severe': 1.25,
            'intense': 1.25,
            'extreme': 1.3,
            'unbearable': 1.3
        }
        
        severity_found = False
        severity_boost = 1.0
        for keyword, boost in severity_keywords.items():
            if keyword in symptoms_lower:
                severity_found = True
                severity_boost = max(severity_boost, boost)
        
        if severity_found:
            quality_score *= severity_boost
            if severity_boost == 1.0:
                quality_score = min(quality_score, 0.65)
        else:
            quality_score *= 0.90
            uncertainty_reasons.append("symptom severity")
        
        # Single symptom penalty
        if len(words) <= 3:
            quality_score *= 0.75
            uncertainty_reasons.append("limited symptom details")
        
        # Duration analysis
        duration_keywords = {
            'hour': 'acute', 'hours': 'acute', 'day': 'acute', 'days': 'acute',
            'week': 'subacute', 'weeks': 'subacute',
            'month': 'chronic', 'months': 'chronic', 'year': 'chronic'
        }
        
        duration_found = False
        for keyword in duration_keywords:
            if keyword in symptoms_lower:
                duration_found = True
                break
        
        if not duration_found:
            quality_score *= 0.88
            uncertainty_reasons.append("symptom duration")
        
        # Contradiction detection
        contradictions = []
        if ('sudden' in symptoms_lower or 'acute' in symptoms_lower) and any(w in symptoms_lower for w in ['month', 'months', 'year', 'chronic']):
            contradictions.append("sudden onset with long duration")
        if ('severe' in symptoms_lower or 'extreme' in symptoms_lower) and ('normal' in symptoms_lower or 'functioning' in symptoms_lower):
            contradictions.append("severe symptoms with normal functioning")
        
        if contradictions:
            quality_score *= 0.70  # 30% penalty for contradictions
            quality_score = min(quality_score, 0.60)  # Cap at 60%
            uncertainty_reasons.append("conflicting symptom patterns")
        
        # Progression keywords
        if any(word in symptoms_lower for word in ['worsening', 'worse', 'getting worse', 'deteriorating']):
            quality_score *= 1.1
        elif any(word in symptoms_lower for word in ['improving', 'better', 'getting better']):
            quality_score *= 0.85
        
        return min(quality_score, 1.5), uncertainty_reasons, has_comorbidity
    
    def apply_regional_weighting(self, disease_name, base_confidence):
        """Apply regional disease prevalence weighting (India-focused)"""
        # Default region: India
        import datetime
        current_month = datetime.datetime.now().month
        
        # Monsoon season in India (June-September)
        is_monsoon = current_month in [6, 7, 8, 9]
        
        disease_lower = disease_name.lower()
        
        # Monsoon-related diseases (boost during monsoon)
        if is_monsoon:
            if any(term in disease_lower for term in ['dengue', 'malaria', 'typhoid', 'cholera', 'leptospirosis']):
                return base_confidence * 1.15  # 15% boost
        
        # Common year-round conditions in India
        if any(term in disease_lower for term in ['cold', 'flu', 'fever', 'throat', 'tonsil', 'gastro']):
            return base_confidence * 1.05  # 5% boost for common conditions
        
        return base_confidence
    
    def generate_unlikely_conditions(self, disease_name, confidence_pct):
        """Generate 'what this is not' reassurance based on primary condition"""
        disease_lower = disease_name.lower()
        
        # Only provide reassurance if confidence is reasonable
        if confidence_pct < 50:
            return None
        
        unlikely_statements = []
        
        # Throat/tonsil conditions
        if 'throat' in disease_lower or 'tonsil' in disease_lower:
            unlikely_statements.append("Based on what you've described, this does not currently suggest a serious airway emergency or deep neck infection.")
        
        # Respiratory conditions
        elif 'cold' in disease_lower or 'flu' in disease_lower or 'cough' in disease_lower:
            unlikely_statements.append("At this stage, there are no strong signs pointing toward pneumonia or a more severe respiratory condition.")
        
        # Headache conditions
        elif 'headache' in disease_lower or 'migraine' in disease_lower:
            unlikely_statements.append("Your symptoms do not currently suggest a neurological emergency or serious brain condition.")
        
        # Fever conditions
        elif 'fever' in disease_lower:
            unlikely_statements.append("There are no immediate signs of a life-threatening infection at this point.")
        
        # Gastrointestinal conditions
        elif 'gastro' in disease_lower or 'stomach' in disease_lower or 'diarrhea' in disease_lower:
            unlikely_statements.append("Based on your description, this does not appear to be a surgical emergency or severe inflammatory condition.")
        
        return unlikely_statements[0] if unlikely_statements else None
    
    def format_uncertainty_explanation(self, uncertainty_reasons):
        """Format transparent uncertainty explanation"""
        if not uncertainty_reasons:
            return ""
        
        reasons_text = ", ".join(uncertainty_reasons)
        if len(uncertainty_reasons) == 1:
            explanation = f"The confidence is moderate because {reasons_text} information is not yet clear."
        else:
            explanation = f"The confidence is moderate because details such as {reasons_text} are not yet clear."
        
        html = "<div style='margin-bottom: 20px; padding: 12px; background: var(--bg-glass); border-radius: 12px; border-left: 3px solid var(--warning);'>"
        html += f"<p style='color: var(--text-primary); font-weight: 600; margin-bottom: 6px;'>Why confidence is not higher:</p>"
        html += f"<p style='color: var(--text-secondary); margin: 0; line-height: 1.6;'>{explanation} A clearer picture would help narrow this down further.</p>"
        html += "</div>"
        return html
    
    def generate_followup_questions(self, disease_name, confidence_pct, sections):
        """Generate relevant follow-up questions based on disease and confidence"""
        if confidence_pct > 85:
            return None
        
        questions = []
        
        # Generic questions based on common medical assessment
        if 'fever' not in str(sections).lower():
            questions.append("Have you noticed a fever?")
        
        questions.append("How long have these symptoms been present?")
        
        # Disease-specific questions
        if 'throat' in disease_name.lower() or 'tonsil' in disease_name.lower():
            questions.append("Is swallowing becoming more painful?")
        elif 'cold' in disease_name.lower() or 'flu' in disease_name.lower():
            questions.append("Are you experiencing body aches or fatigue?")
        elif 'headache' in disease_name.lower():
            questions.append("Is the pain on one side or both sides of your head?")
        
        return questions[:3]  # Max 3 questions
    
    def format_rag_response(self, chunks, symptoms):
        """Format RAG retrieved chunks into humanized medical advice with multi-disease ranking"""
        # Analyze symptom quality for confidence adjustment
        quality_modifier, uncertainty_reasons, has_comorbidity = self.analyze_symptom_quality(symptoms)
        
        # Group chunks by disease and section
        diseases = {}
        for idx, chunk in enumerate(chunks):
            disease_name = chunk['metadata']['disease_name']
            section = chunk['metadata']['section']
            
            if disease_name not in diseases:
                # Calculate confidence with quality adjustment
                base_confidence = self.calculate_confidence(
                    chunk.get('score', 0.8), 
                    idx, 
                    len(chunks)
                )
                adjusted_confidence = base_confidence * quality_modifier
                
                # Apply regional weighting
                regional_confidence = self.apply_regional_weighting(disease_name, adjusted_confidence)
                
                # Apply comorbidity modifier
                if has_comorbidity:
                    regional_confidence *= 1.05
                
                diseases[disease_name] = {
                    'source': chunk['metadata']['source'],
                    'sections': {},
                    'confidence': regional_confidence,
                    'rank': idx
                }
            
            diseases[disease_name]['sections'][section] = chunk['text'].replace(f"{disease_name} - {section}:", "").strip()
        
        # Apply symptom role weighting and negative evidence penalties
        for disease_name, disease_info in diseases.items():
            symptom_adjustment = self.apply_symptom_role_weighting(disease_name, symptoms, disease_info['sections'])
            disease_info['confidence'] += symptom_adjustment
            
            # Cap at 90% maximum, or 85% if incomplete info
            max_cap = 0.85 if uncertainty_reasons else 0.90
            disease_info['confidence'] = min(max(disease_info['confidence'], 0.0), max_cap)
        
        # Filter diseases above 25% threshold
        diseases = {k: v for k, v in diseases.items() if v['confidence'] >= 0.25}
        
        # Sort diseases by confidence
        sorted_diseases = sorted(diseases.items(), key=lambda x: x[1]['confidence'], reverse=True)
        
        # Enforce confidence separation
        sorted_diseases = self.enforce_confidence_separation(sorted_diseases)
        
        # Generate ranking explanation
        ranking_explanation = self.generate_ranking_explanation(sorted_diseases, symptoms)
        
        # Build response with multi-disease ranking
        html_response = ""
        
        # Show ranked conditions if multiple diseases found
        if len(sorted_diseases) > 1:
            html_response += "<div style='margin-bottom: 20px; padding: 12px; background: var(--bg-glass); border-radius: 12px; border: 1px solid var(--border);'>"
            html_response += "<p style='color: var(--text-primary); font-weight: 600; margin-bottom: 10px;'>Possible Conditions:</p>"
            html_response += "<ul style='color: var(--text-primary); line-height: 1.8; margin: 0; padding-left: 24px;'>"
            for disease_name, disease_info in sorted_diseases[:3]:  # Max 3 conditions
                conf_pct = int(disease_info['confidence'] * 100)
                html_response += f"<li>{disease_name} — Confidence: {conf_pct}%</li>"
            html_response += "</ul></div>"
        
        # Add ranking explanation if available
        if ranking_explanation:
            html_response += "<div style='margin-bottom: 20px; padding: 12px; background: var(--bg-glass); border-radius: 12px; border-left: 3px solid var(--accent);'>"
            html_response += f"<p style='color: var(--text-primary); font-weight: 600; margin-bottom: 6px;'>Why this ranking:</p>"
            html_response += f"<p style='color: var(--text-secondary); margin: 0; line-height: 1.6;'>{ranking_explanation}</p>"
            html_response += "</div>"
        
        # Add uncertainty explanation if reasons exist
        if uncertainty_reasons:
            html_response += self.format_uncertainty_explanation(uncertainty_reasons)
        
        # Primary disease explanation
        primary_disease = sorted_diseases[0]
        html_response += self.format_humanized_response(primary_disease[0], primary_disease[1], symptoms, has_comorbidity)
        
        if not html_response:
            return self.get_fallback_response()
            
        return html_response
    
    def format_humanized_response(self, disease_name, disease_info, symptoms="", has_comorbidity=False):
        """Format disease information in calm, empathetic medical tone"""
        sections = disease_info['sections']
        confidence = disease_info['confidence']
        
        # Convert confidence to percentage
        confidence_pct = int(confidence * 100)
        
        # MANDATORY HEADER: Disease name and confidence percentage
        response = f"<div style='margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid var(--border);'>"
        response += f"<p style='color: var(--text-primary); font-size: 1.1em; font-weight: 600; margin-bottom: 6px;'>Condition: {disease_name}</p>"
        response += f"<p style='color: var(--text-secondary); font-size: 0.95em; margin-bottom: 0;'>Confidence: {confidence_pct}%</p>"
        response += "</div>"
        
        # Opening with empathy
        response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>Based on what you've shared, {disease_name.lower()} appears to be a likely explanation for your symptoms.</p>"
        
        # Summary/Description
        if 'summary' in sections:
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>{sections['summary']}</p>"
        
        # Symptoms (conversational)
        if 'symptoms' in sections:
            symptoms_text = sections['symptoms'].replace(',', ', ')
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px;'>People with this condition commonly experience {symptoms_text.lower()}.</p>"
        
        # Treatment (gentle guidance) - deduplicated
        if 'treatment' in sections:
            treatment_items = list(set([t.strip() for t in sections['treatment'].split(',')]))
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 8px;'><strong>Management typically includes:</strong></p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding-left: 24px;'>"
            for item in treatment_items:
                if item:
                    response += f"<li>{item}</li>"
            response += "</ul>"
        
        # "What this is NOT" reassurance
        unlikely_statement = self.generate_unlikely_conditions(disease_name, confidence_pct)
        if unlikely_statement:
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding: 10px; background: var(--bg-glass); border-radius: 8px; border-left: 3px solid var(--success);'>{unlikely_statement}</p>"
        
        # Warning signs (calm but clear) - deduplicated
        if 'warning_signs' in sections:
            warning_items = list(set([w.strip() for w in sections['warning_signs'].split(',')]))
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 8px;'><strong>You should consider seeking medical attention if:</strong></p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding-left: 24px;'>"
            for item in warning_items:
                if item:
                    response += f"<li>{item}</li>"
            response += "</ul>"
        
        # Prevention (if available) - deduplicated
        if 'prevention' in sections:
            prevention_items = list(set([p.strip() for p in sections['prevention'].split(',')]))
            response += f"<p style='color: var(--text-primary); line-height: 1.6; margin-bottom: 8px;'><strong>To help prevent this:</strong></p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.6; margin-bottom: 12px; padding-left: 24px;'>"
            for item in prevention_items:
                if item:
                    response += f"<li>{item}</li>"
            response += "</ul>"
        
        # Follow-up questions (if confidence < 85%)
        followup_questions = self.generate_followup_questions(disease_name, confidence_pct, sections)
        if followup_questions:
            response += "<div style='margin: 20px 0; padding: 12px; background: var(--bg-glass); border-radius: 12px; border-left: 3px solid var(--accent);'>"
            response += "<p style='color: var(--text-primary); font-weight: 600; margin-bottom: 10px;'>To better understand your situation, could you tell me:</p>"
            response += "<ul style='color: var(--text-primary); line-height: 1.8; margin: 0; padding-left: 24px;'>"
            for question in followup_questions:
                response += f"<li>{question}</li>"
            response += "</ul></div>"
        
        # Doctor-style closing reassurance (confidence-based)
        if has_comorbidity:
            if confidence_pct >= 75:
                reassurance = "Given your existing health conditions, monitoring your symptoms closely is important. Most people improve with appropriate care, but if symptoms persist or worsen, seeking medical advice would be appropriate."
            elif confidence_pct >= 50:
                reassurance = "With your health background, it's worth keeping a close eye on how you feel. If things don't improve or you notice changes, a healthcare professional can provide personalized guidance."
            else:
                reassurance = "Given your medical history, it would be helpful to discuss these symptoms with a healthcare provider who can consider your full health picture."
        else:
            if confidence_pct >= 75:
                reassurance = "Most people with these symptoms improve with appropriate care. If symptoms persist or worsen, seeking in-person medical advice would be appropriate."
            elif confidence_pct >= 50:
                reassurance = "These symptoms can have various causes. Monitoring how you feel over the next day or two can be helpful. If things don't improve or you feel worse, a healthcare professional can provide more specific guidance."
            else:
                reassurance = "Your symptoms could relate to several conditions. It would be helpful to observe any changes and consider speaking with a healthcare provider who can examine you properly."
        
        response += f"<p style='color: var(--text-secondary); font-size: 0.95em; line-height: 1.6; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border); font-style: italic;'>{reassurance}</p>"
        
        return f"<div style='margin-bottom: 24px;'>{response}</div>"
    
    def get_fallback_response(self):
        """Fallback response when RAG fails"""
        return "<p style='color: var(--text-primary); line-height: 1.6;'>I'm currently unable to provide specific medical information for your symptoms. For your safety and peace of mind, I'd recommend speaking with a healthcare professional who can properly evaluate your condition.</p>"
    
    def get_health_advice(self, symptoms):
        """Get health advice using RAG if available, fallback to legacy matching"""
        if self.rag_enabled:
            return self.get_rag_health_advice(symptoms)
        else:
            # Fallback to legacy disease matching
            matching_disease = self.find_matching_disease(symptoms)
            if matching_disease:
                return self.format_disease_response(matching_disease)
            else:
                return "<p style='color: var(--text-primary); line-height: 1.6;'>I don't have specific information about these symptoms in my current knowledge base. For your safety, I'd recommend consulting with a healthcare professional who can properly assess your condition.</p>"
