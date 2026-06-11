from madtitan_contracts.candidate import MonsterCandidate


def test_monster_candidate_contract_accepts_segmented_candidate() -> None:
    candidate = MonsterCandidate.model_validate(
        {
            "candidate_id": "synthetic-p0001-reloader-candidate-v1",
            "status": "pending",
            "source": {
                "source_book_id": "synthetic-fixtures",
                "book_title": "Synthetic Fixtures",
                "ruleset": "DND 5.5e",
                "source_file_id": "synthetic-fixtures-file",
                "source_file_checksum": "sha256:example",
                "page_start": 1,
                "page_end": 1,
                "page_labels": ["1"],
            },
            "source_format": {
                "profile_id": "synthetic-2024-style",
                "profile_version": "v1",
                "statblock_family": "dnd_2024",
                "layout_type": "two_column_card",
                "expected_single_page": True,
                "column_count": 2,
                "section_order": ["header", "traits", "actions", "legendary_actions"],
                "heading_patterns": ["uppercase_red_heading"],
                "known_variations": ["option_table_action"],
                "notes": "Synthetic source shaped like a complex single-page stat block.",
                "metadata": {
                    "source_specific": True
                },
            },
            "lineage": {
                "extracted_page_text_ids": ["synthetic-page-text-v1"],
                "extraction_methods": ["manual_transcription"],
                "segmentation_run_id": "segment-run-test",
                "segmentation_method": "fixture_sections",
                "segmenter_version": "segmenter-v0.1.0",
                "parent_candidate_id": None,
                "repair_source_quarantine_record_id": None,
            },
            "candidate": {
                "name_hint": "Reloader",
                "creature_type_hint": "aberration",
                "structured_fields": {
                    "name": "Reloader",
                    "creature_type": "aberration",
                },
                "page_span_text": "synthetic candidate text",
                "page_span_text_ref": None,
                "sections": [
                    {
                        "label": "header",
                        "text": "synthetic header text",
                    },
                    {
                        "label": "actions",
                        "text": "synthetic action text",
                    },
                ],
                "start_marker": "RELOADER",
                "end_marker": "LEGENDARY ACTIONS",
                "raw_text_hash": "sha256:example",
            },
            "location": {
                "page_start": 1,
                "page_end": 1,
                "text_start_offset": 0,
                "text_end_offset": 2000,
                "bounding_boxes": [
                    {
                        "page": 1,
                        "x0": 0.05,
                        "y0": 0.04,
                        "x1": 0.95,
                        "y1": 0.96,
                        "unit": "page_ratio",
                    }
                ],
            },
            "quality": {
                "confidence": 0.88,
                "text_quality": "good",
                "segmentation_quality": "complete",
                "warnings": [
                    {
                        "code": "possible_wrapped_action",
                        "message": "One action may continue across a column break.",
                    }
                ],
            },
            "normalization": {
                "recommended_method": "deterministic_rules",
                "attempt_count": 0,
                "last_attempt_at": None,
            },
            "audit": {
                "created_at": "2026-06-11T05:10:00Z",
                "created_by": "candidate_segmentation",
                "private_content": False,
                "updated_at": None,
            },
        }
    )

    assert candidate.candidate_id == "synthetic-p0001-reloader-candidate-v1"
    assert candidate.status == "pending"
    assert candidate.source_format.profile_id == "synthetic-2024-style"
    assert candidate.source_format.known_variations == ["option_table_action"]
    assert candidate.lineage.extraction_methods == ["manual_transcription"]
    assert candidate.candidate.name_hint == "Reloader"
    assert candidate.candidate.structured_fields["creature_type"] == "aberration"
    assert candidate.candidate.sections[1].label == "actions"
    assert candidate.location.bounding_boxes[0].unit == "page_ratio"
    assert candidate.quality.warnings[0].code == "possible_wrapped_action"
    assert candidate.normalization.attempt_count == 0
