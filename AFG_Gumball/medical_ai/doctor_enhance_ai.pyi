from typing import List, Tuple

class DoctorEnhanceAI:
    def __init__(self) -> None: ...
    def enhance_medical_record(self, medical_record: str) -> str: ...
    def validate_diagnosis(
        self,
        symptoms: str,
        pathologies_list: List[List[Tuple[str, float]]],
        medical_record: str
    ) -> str: ...