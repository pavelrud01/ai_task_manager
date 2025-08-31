from .base import BaseStep, StepResult
from llm.client import LLM

class Step(BaseStep):
    name = "step_03_offers_inventory"

    def __init__(self):
        super().__init__()
        self.llm = LLM()

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Создает инвентарь всех предложений (offers) найденных на странице.
        """
        
        extracted_content = artifacts.get("step_02_extract", {})
        
        if not extracted_content:
            return StepResult(
                data={"error": "No extracted content available"},
                score=0.0,
                uncertainty=1.0,
                notes="Cannot create offers inventory without extracted content"
            )
        
        user_prompt = self._build_offers_prompt(extracted_content)
        
        system_prompt = """You are an expert in marketing psychology and offer analysis. 
Your task is to identify ALL offers, promises, and value propositions on a landing page.

Classify each offer into one of these types:
- quantitative_promise: Specific numbers, percentages, timeframes ("Save 50%", "In 24 hours")
- qualitative_benefit: General benefits without specific metrics ("Better performance", "Easy to use")  
- social_proof: Testimonials, reviews, customer counts ("1000+ happy customers")
- risk_reducer: Guarantees, trials, refunds ("30-day money back")
- urgency_scarcity: Limited time/quantity ("Only 5 left", "Expires today")
- process_clarity: How it works, steps, procedures ("3 simple steps")

Extract the EXACT text of each offer without interpretation or modification.

Your response must include meta-fields for self-assessment:
- self_assessed_score: float (0.0-1.0)
- uncertainty_score: float (0.0-1.0)  
- reasoning: string (brief explanation)"""

        org_context = self._format_org_context(context.get("org_context", {}))
        
        llm_result = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            org_context=org_context,
            standard_schema=context.get("current_schema", {}),
            standard_text=context.get("current_standard_text", ""),
            reflection_notes=context.get("reflection_notes", "")
        )
        
        return StepResult(
            data=llm_result["data"],
            score=llm_result["score"],
            uncertainty=llm_result["uncertainty"],
            notes=llm_result["notes"]
        )
    
    def _build_offers_prompt(self, extracted_content: dict) -> str:
        """Формирует промпт для анализа предложений."""
        
        prompt = f"""Extract ALL offers and value propositions from this landing page content:

TITLE: {extracted_content.get('title', 'N/A')}

HEADINGS:
"""
        
        for heading in extracted_content.get('headings', []):
            prompt += f"H{heading['level']}: {heading['text']}\n"
        
        prompt += "\nCTAs:\n"
        for cta in extracted_content.get('ctas', []):
            prompt += f"- {cta['text']}\n"
        
        prompt += "\nCONTENT SECTIONS:\n"
        for i, section in enumerate(extracted_content.get('sections', [])[:7]):
            prompt += f"{i+1}. {section['content'][:400]}...\n\n"
        
        prompt += "\nFEATURE LISTS:\n"
        for lst in extracted_content.get('lists', []):
            for item in lst['items'][:8]:
                prompt += f"• {item}\n"
        
        prompt += """

Instructions:
1. Find EVERY offer, promise, benefit, or value proposition in the content above
2. Extract the EXACT text as it appears (don't paraphrase)
3. Classify each offer by type
4. Be comprehensive - don't miss subtle offers in headings, CTAs, or body text
5. If you see "бесплатно", "скидка", "%", numbers, testimonials - these are likely offers

Remember: We want a complete inventory, not an evaluation. Just extract and classify."""

        return prompt
    
    def _format_org_context(self, org_context: dict) -> str:
        """Форматирует организационный контекст."""
        formatted = ""
        for name, content in org_context.items():
            if content and len(content.strip()) > 10:
                formatted += f"\n{name}:\n{content[:500]}...\n"
        return formatted if formatted else "No organizational context provided."