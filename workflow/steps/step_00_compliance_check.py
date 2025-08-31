from .base import BaseStep, StepResult
import validators
from urllib.parse import urlparse

class Step(BaseStep):
    name = "step_00_compliance_check"

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Проверяет корректность входных данных и готовность к выполнению workflow.
        """
        input_data = context.get("input", {})
        issues = []
        warnings = []
        
        # Проверка обязательных полей
        required_fields = ["landing_url", "company_name"]
        for field in required_fields:
            if not input_data.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Валидация URL
        landing_url = input_data.get("landing_url", "")
        if landing_url:
            try:
                parsed = urlparse(landing_url)
                if not all([parsed.scheme, parsed.netloc]):
                    issues.append(f"Invalid URL format: {landing_url}")
                elif parsed.scheme not in ['http', 'https']:
                    issues.append(f"URL must use HTTP or HTTPS: {landing_url}")
            except Exception as e:
                issues.append(f"URL validation error: {str(e)}")
        
        # Проверка организационного контекста
        org_context = context.get("org_context", {})
        if not org_context.get("CompanyCard.md") or "Сюда скопируйте ваш текст" in org_context.get("CompanyCard.md", ""):
            warnings.append("CompanyCard.md is not properly filled out")
        
        if not org_context.get("MarketCard.md") or "Здесь будет описание" in org_context.get("MarketCard.md", ""):
            warnings.append("MarketCard.md is not properly filled out")
        
        # Проверка доступности схем
        schemas = context.get("schemas", {})
        expected_schemas = ["step_03_offers_inventory", "step_04_jtbd", "step_05_segments", 
                          "step_06_decision_mapping", "step_11_synthesis", "step_13_tasks"]
        missing_schemas = [s for s in expected_schemas if s not in schemas]
        if missing_schemas:
            warnings.append(f"Missing schemas: {', '.join(missing_schemas)}")
        
        # Определяем результат проверки
        if issues:
            return StepResult(
                data={
                    "compliance_status": "FAILED",
                    "issues": issues,
                    "warnings": warnings,
                    "can_proceed": False
                },
                score=0.0,
                uncertainty=0.0,
                notes=f"Compliance check failed with {len(issues)} critical issues"
            )
        
        return StepResult(
            data={
                "compliance_status": "PASSED",
                "issues": [],
                "warnings": warnings,
                "can_proceed": True,
                "validated_input": input_data
            },
            score=1.0 if not warnings else 0.8,
            uncertainty=0.1 if warnings else 0.0,
            notes=f"Compliance check passed with {len(warnings)} warnings"
        )