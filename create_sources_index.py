#!/usr/bin/env python3
import hashlib
import json
import os

# Список файлов в порядке чтения
files = [
    'prompts/guides/[v3.3] Гайд AJTBD-интервью для B2C-продуктов.md',
    'prompts/standards/user_template.md',
    'prompts/standards/jtbd_levels_reading.md',
    'prompts/standards/interview_ajtbd.md',
    'prompts/standards/jtbd.md',
    'prompts/standards/jtbd_longform.md',
    'prompts/guides/Evidence_Tags.md',
    'prompts/context/CompanyCard.md',
    'prompts/context/MarketCard.md',
    'prompts/context/Lessons.md',
    'prompts/context/CA.md',
    'prompts/context/knowledge/ajtbd/AJTBD.txt',
    'prompts/context/knowledge/ajtbd/AJTBD1.txt',
    'prompts/context/knowledge/ajtbd/AJTBD2.txt',
    'prompts/context/knowledge/ajtbd/AJTBD3.txt',
    'prompts/context/knowledge/ajtbd/AJTBD4.txt',
    'prompts/context/knowledge/ajtbd/AJTBD5.txt',
    'prompts/context/knowledge/ajtbd/AJTBD6.txt',
    'prompts/context/knowledge/ajtbd/AJTBD7.txt',
    'prompts/context/knowledge/ajtbd/AJTBD8.txt',
    'prompts/context/knowledge/ajtbd/AJTBD9.txt',
    'prompts/context/knowledge/ajtbd/AJTBD10.txt',
    'prompts/context/knowledge/ajtbd/INDEX.md',
    'prompts/context/knowledge/ajtbd/Job_Levels_Classification.md',
    'prompts/context/knowledge/ajtbd/Risk_Assumptions_RAT.md',
    'prompts/context/knowledge/ajtbd/Segment_Hypotheses_B2C.md',
    'prompts/context/knowledge/ajtbd/Segmentation_Rules.md'
]

sources = []

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
            sha256_hash = hashlib.sha256(content).hexdigest()
            sources.append({
                'path': file_path,
                'sha256': sha256_hash
            })
    else:
        print(f"Warning: File not found: {file_path}")

# Создаем SOURCES_INDEX.json
sources_index = {
    'sources': sources,
    'total_files': len(sources),
    'created_at': '2025-01-04T01:47:48Z',
    'run_id': 'run_20250904_014748_0c5e'
}

# Сохраняем в файл
with open('artifacts/run_20250904_014748_0c5e/iter_2/SOURCES_INDEX.json', 'w', encoding='utf-8') as f:
    json.dump(sources_index, f, indent=2, ensure_ascii=False)

print(f"Created SOURCES_INDEX.json with {len(sources)} files")
print("Files processed:")
for source in sources:
    print(f"  - {source['path']}")
