from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# 1. Define a Custom Phone Number Pattern (Malaysian Style)
# Matches 01x-xxxxxxx, 01x-xxxxxxxx, or 01x xxxxxxx
msia_phone_pattern = Pattern(
    name="msia_phone_pattern",
    regex=r"(\+?6?01)[0-46-9]-?\d{7,8}",
    score=0.95
)

# 2. Define a more aggressive Credit Card Pattern
card_pattern = Pattern(
    name="card_pattern",
    regex=r"\b(?:\d[ -]*?){13,16}\b",
    score=0.95
)

# 3. Register these patterns with Recognizers
msia_phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER", 
    patterns=[msia_phone_pattern]
)

card_recognizer = PatternRecognizer(
    supported_entity="CREDIT_CARD", 
    patterns=[card_pattern]
)

# 4. Initialize Engine and add our new tools
analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(msia_phone_recognizer)
analyzer.registry.add_recognizer(card_recognizer)

anonymizer = AnonymizerEngine()

def redact_pii(text: str):
    # We explicitly list the entities we want to target
    # Lowering the score_threshold to 0.4 catches "uncertain" items
    results = analyzer.analyze(
        text=text, 
        entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD"], 
        language='en',
        score_threshold=0.4 
    )
    
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )
    
    return anonymized_result.text