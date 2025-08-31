import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from .base import BaseStep, StepResult

class Step(BaseStep):
    name = "step_02_extract"

    def run(self, context: dict, artifacts: dict) -> StepResult:
        """
        Извлекает контент с лендинговой страницы и структурирует его для дальнейшего анализа.
        """
        input_data = context.get("input", {})
        landing_url = input_data.get("landing_url")
        
        if not landing_url:
            return StepResult(
                data={"error": "No landing_url provided in input"},
                score=0.0,
                uncertainty=0.0,
                notes="Cannot extract content without URL"
            )
        
        try:
            # Получаем контент страницы
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            print(f"Fetching content from: {landing_url}")
            response = requests.get(landing_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлекаем структурированные данные
            extracted_data = self._extract_structured_content(soup, landing_url)
            
            # Оценка качества извлечения
            score = self._assess_extraction_quality(extracted_data)
            uncertainty = self._assess_uncertainty(extracted_data)
            
            return StepResult(
                data=extracted_data,
                score=score,
                uncertainty=uncertainty,
                notes=f"Successfully extracted content from {landing_url}. Found {len(extracted_data.get('sections', []))} sections."
            )
            
        except requests.RequestException as e:
            return StepResult(
                data={"error": f"Failed to fetch URL: {str(e)}"},
                score=0.0,
                uncertainty=1.0,
                notes=f"Network error while fetching {landing_url}: {str(e)}"
            )
        except Exception as e:
            return StepResult(
                data={"error": f"Extraction failed: {str(e)}"},
                score=0.0,
                uncertainty=1.0,
                notes=f"Unexpected error during extraction: {str(e)}"
            )

    def _extract_structured_content(self, soup: BeautifulSoup, base_url: str) -> dict:
        """Извлекает структурированный контент со страницы."""
        
        # Удаляем скрипты и стили
        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()
        
        # Извлекаем основные элементы
        title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})
        
        # Извлекаем заголовки
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                if heading.get_text(strip=True):
                    headings.append({
                        "level": level,
                        "text": heading.get_text(strip=True),
                        "tag": f"h{level}"
                    })
        
        # Извлекаем CTA (кнопки и ссылки)
        ctas = []
        for element in soup.find_all(['a', 'button']):
            text = element.get_text(strip=True)
            href = element.get('href', '')
            if text and (
                any(keyword in text.lower() for keyword in ['купить', 'заказать', 'попробовать', 'получить', 'скачать', 'начать', 'подписаться', 'регистрация', 'buy', 'order', 'try', 'get', 'download', 'start', 'subscribe', 'sign up']) 
                or element.get('type') == 'submit'
            ):
                ctas.append({
                    "text": text,
                    "href": urljoin(base_url, href) if href else "",
                    "type": element.name
                })
        
        # Извлекаем текстовые блоки
        sections = []
        for element in soup.find_all(['div', 'section', 'article']):
            text = element.get_text(strip=True)
            if text and len(text) > 50:  # Игнорируем короткие блоки
                # Проверяем, не является ли это дублем
                if not any(text in section['content'] for section in sections):
                    sections.append({
                        "content": text[:1000],  # Ограничиваем длину
                        "word_count": len(text.split()),
                        "tag": element.name
                    })
        
        # Извлекаем списки (features, benefits)
        lists = []
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            if items and len(items) > 1:
                lists.append({
                    "items": items[:10],  # Ограничиваем количество элементов
                    "type": ul.name
                })
        
        # Извлекаем формы
        forms = []
        for form in soup.find_all('form'):
            inputs = [inp.get('name', inp.get('placeholder', '')) for inp in form.find_all('input')]
            if inputs:
                forms.append({
                    "action": form.get('action', ''),
                    "method": form.get('method', 'get'),
                    "inputs": inputs
                })
        
        return {
            "url": base_url,
            "title": title.get_text(strip=True) if title else "",
            "meta_description": meta_description.get('content', '') if meta_description else "",
            "headings": headings,
            "ctas": ctas,
            "sections": sections,
            "lists": lists,
            "forms": forms,
            "extraction_timestamp": time.time()
        }
    
    def _assess_extraction_quality(self, data: dict) -> float:
        """Оценивает качество извлеченных данных."""
        score = 1.0
        
        # Проверяем наличие ключевых элементов
        if not data.get("title"):
            score -= 0.1
        if not data.get("headings"):
            score -= 0.2
        if not data.get("ctas"):
            score -= 0.3  # CTA критичны для анализа
        if not data.get("sections"):
            score -= 0.3
        
        # Проверяем качество контента
        total_text_length = sum(len(section.get("content", "")) for section in data.get("sections", []))
        if total_text_length < 500:
            score -= 0.1  # Мало контента
        
        return max(0.0, score)
    
    def _assess_uncertainty(self, data: dict) -> float:
        """Оценивает неопределенность извлечения."""
        uncertainty = 0.0
        
        # Высокая неопределенность, если мало данных
        if len(data.get("sections", [])) < 3:
            uncertainty += 0.3
        if len(data.get("ctas", [])) == 0:
            uncertainty += 0.2
        if not data.get("title"):
            uncertainty += 0.1
            
        return min(1.0, uncertainty)