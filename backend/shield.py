from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# 1. Malaysian NRIC Pattern (Format: XXXXXX-XX-XXXX or XXXXXXXXXXXX)
msia_nric_pattern = Pattern(
    name="msia_nric_pattern",
    regex=r"\d{6}-?\d{2}-?\d{4}",
    score=0.95
)

# 2. Malaysian Phone Number Pattern
msia_phone_pattern = Pattern(
    name="msia_phone_pattern",
    regex=r"(\+?6?01)[0-46-9]-?\d{7,8}",
    score=0.95
)

# 3. Credit Card Pattern
card_pattern = Pattern(
    name="card_pattern",
    regex=r"\b(?:\d[ -]*?){13,16}\b",
    score=0.95
)

# 4. Custom Address Recognizer for Malaysian keywords
msia_address_pattern = Pattern(
    name="msia_address_pattern",
    regex=r"(?i)\b(No\.?\s?\d+|Jalan|Taman|Persiaran|Lebuh)\b[^.!?]*", 
    score=0.85
)

# Register Custom Recognizers
nric_recognizer = PatternRecognizer(supported_entity="NRIC", patterns=[msia_nric_pattern])
msia_phone_recognizer = PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[msia_phone_pattern])
card_recognizer = PatternRecognizer(supported_entity="CREDIT_CARD", patterns=[card_pattern])
address_recognizer = PatternRecognizer(
    supported_entity="LOCATION", 
    patterns=[msia_address_pattern]
)

# Initialize Engine with the SMALL model
# We pass the default_score_threshold to avoid low-confidence false positives
analyzer = AnalyzerEngine(default_score_threshold=0.4)
analyzer.registry.add_recognizer(nric_recognizer)
analyzer.registry.add_recognizer(msia_phone_recognizer)
analyzer.registry.add_recognizer(card_recognizer)
analyzer.registry.add_recognizer(address_recognizer)

anonymizer = AnonymizerEngine()

def redact_pii(text: str, allow_list: list = None):
    """
    Redacts sensitive info. 
    allow_list: List of strings (like Order IDs) that should NOT be redacted.
    """
    # Define which entities to look for. 
    # 'LOCATION' handles the home addresses via Spacy.
    target_entities = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD", "NRIC", "LOCATION"]
    
    results = analyzer.analyze(
        text=text, 
        entities=target_entities, 
        language='en',
        allow_list=allow_list # This tells Presidio: "If you see these words, leave them alone!"
    )
    
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )
    
    return anonymized_result.text