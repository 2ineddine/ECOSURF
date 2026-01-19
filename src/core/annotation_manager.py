"""
ECOSURF Annotation Manager
Handles CSV storage and retrieval of audio annotations
"""
import os
import csv
from datetime import datetime
from pathlib import Path


class AnnotationManager:
    """Manages audio annotations stored in CSV format"""

    # Default event types for bioacoustic annotation
    EVENT_TYPES = [
        # Birds
        ("Bird - Song", "bird_song"),
        ("Bird - Call", "bird_call"),
        ("Bird - Alarm", "bird_alarm"),
        # Mammals
        ("Mammal - Vocalization", "mammal_vocal"),
        ("Mammal - Howler Monkey", "howler_monkey"),
        ("Mammal - Spider Monkey", "spider_monkey"),
        # Amphibians
        ("Amphibian - Frog", "frog"),
        ("Amphibian - Toad", "toad"),
        # Insects
        ("Insect - Cicada", "cicada"),
        ("Insect - Cricket", "cricket"),
        ("Insect - Other", "insect_other"),
        # Environment
        ("Environment - Rain", "rain"),
        ("Environment - Thunder", "thunder"),
        ("Environment - Wind", "wind"),
        ("Environment - Water", "water"),
        # Anthropogenic
        ("Anthropogenic - Human", "human"),
        ("Anthropogenic - Vehicle", "vehicle"),
        ("Anthropogenic - Aircraft", "aircraft"),
        # Other
        ("Unknown", "unknown"),
        ("Other", "other"),
    ]

    CSV_HEADERS = [
        "id",
        "timestamp",
        "file_path",
        "file_name",
        "start_time",
        "end_time",
        "duration",
        "channel",
        "sample_rate",
        "freq_min",
        "freq_max",
        "event_type",
        "event_code",
        "quality",
        "notes",
        "source_type"
    ]

    def __init__(self, csv_path=None):
        """Initialize annotation manager with CSV file path"""
        if csv_path is None:
            # Default path in user's documents
            docs_path = Path.home() / "Documents" / "ECOSURF"
            docs_path.mkdir(parents=True, exist_ok=True)
            csv_path = docs_path / "annotations.csv"

        self.csv_path = Path(csv_path)
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()

    def _get_next_id(self):
        """Get next available annotation ID"""
        annotations = self.get_all_annotations()
        if not annotations:
            return 1
        max_id = max(int(a.get('id', 0)) for a in annotations)
        return max_id + 1

    def add_annotation(self, annotation_data: dict) -> int:
        """
        Add a new annotation to the CSV file

        Args:
            annotation_data: Dictionary with annotation fields

        Returns:
            ID of the new annotation
        """
        annotation_id = self._get_next_id()
        annotation_data['id'] = annotation_id
        annotation_data['timestamp'] = datetime.now().isoformat()

        # Ensure all fields exist
        for header in self.CSV_HEADERS:
            if header not in annotation_data:
                annotation_data[header] = ""

        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writerow(annotation_data)

        return annotation_id

    def get_all_annotations(self) -> list:
        """Get all annotations from CSV file"""
        if not self.csv_path.exists():
            return []

        annotations = []
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                annotations.append(row)

        return annotations

    def get_annotations_for_file(self, file_path: str) -> list:
        """Get all annotations for a specific audio file"""
        all_annotations = self.get_all_annotations()
        return [a for a in all_annotations if a.get('file_path') == file_path]

    def delete_annotation(self, annotation_id: int) -> bool:
        """Delete an annotation by ID"""
        annotations = self.get_all_annotations()
        filtered = [a for a in annotations if int(a.get('id', 0)) != annotation_id]

        if len(filtered) == len(annotations):
            return False  # Nothing deleted

        # Rewrite CSV without the deleted annotation
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            writer.writerows(filtered)

        return True

    def update_annotation(self, annotation_id: int, updates: dict) -> bool:
        """Update an existing annotation"""
        annotations = self.get_all_annotations()
        updated = False

        for a in annotations:
            if int(a.get('id', 0)) == annotation_id:
                a.update(updates)
                updated = True
                break

        if updated:
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                writer.writerows(annotations)

        return updated

    def export_to_csv(self, output_path: str, annotations: list = None):
        """Export annotations to a specific CSV file"""
        if annotations is None:
            annotations = self.get_all_annotations()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            writer.writerows(annotations)

    def import_from_csv(self, input_path: str, merge: bool = True):
        """
        Import annotations from another CSV file

        Args:
            input_path: Path to CSV file to import
            merge: If True, merge with existing; if False, replace all
        """
        with open(input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported = list(reader)

        if merge:
            existing = self.get_all_annotations()
            # Reassign IDs to imported annotations
            next_id = self._get_next_id()
            for a in imported:
                a['id'] = next_id
                next_id += 1

            all_annotations = existing + imported
        else:
            all_annotations = imported

        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            writer.writerows(all_annotations)

    def get_csv_path(self) -> str:
        """Return the current CSV file path"""
        return str(self.csv_path)

    def set_csv_path(self, new_path: str):
        """Change the CSV file path"""
        self.csv_path = Path(new_path)
        self._ensure_csv_exists()

    @classmethod
    def get_event_types(cls) -> list:
        """Get list of available event types"""
        return cls.EVENT_TYPES

    @classmethod
    def get_event_label(cls, event_code: str) -> str:
        """Get display label for an event code"""
        for label, code in cls.EVENT_TYPES:
            if code == event_code:
                return label
        return event_code
