"""Notes service tests."""

from unittest import TestCase
from unittest.mock import Mock
import base64
import zlib
import json

from pyicloud.services.notes import NotesService
from pyicloud.protobuf.versioned_document_pb2 import Document
from pyicloud.protobuf.topotext_pb2 import String


class NotesServiceTest(TestCase):
    """Notes service tests."""

    service = None

    def setUp(self):
        """Set up tests."""
        # Mock session and parameters
        mock_session = Mock()
        mock_session.service = Mock()
        mock_session.service.data = {
            "dsInfo": {
                "dsid": "mock_dsid",
            }
        }
        mock_params = {
            "dsid": "mock_dsid",
        }

        # Create a valid protobuf Document message
        document = Document()
        proto_string = String()
        proto_string.string = "Test Note Content"
        document.version.add().data = proto_string.SerializeToString()
        text_data = document.SerializeToString()
        compressed_text_data = zlib.compress(text_data)
        encoded_text_data = base64.b64encode(compressed_text_data).decode("utf-8")

        # Create a mock response for the post request
        def mock_post(url, data, headers):
            if "changes/zone" in url:
                return Mock(
                    json=Mock(
                        return_value={
                            "zones": [
                                {
                                    "records": [
                                        {
                                            "recordName": "note1",
                                            "recordType": "Note",
                                            "fields": {
                                                "TitleEncrypted": {
                                                    "value": base64.b64encode(
                                                        b"Test Note"
                                                    ).decode("utf-8")
                                                },
                                                "SnippetEncrypted": {
                                                    "value": base64.b64encode(
                                                        b"This is a test note"
                                                    ).decode("utf-8")
                                                },
                                                "TextDataEncrypted": {
                                                    "value": encoded_text_data
                                                },
                                            },
                                        },
                                    ],
                                    "moreComing": False,
                                }
                            ]
                        }
                    )
                )
            elif "records/lookup" in url:
                return Mock(
                    json=Mock(
                        return_value={
                            "records": [
                                {
                                    "recordName": "note1",
                                    "recordType": "Note",
                                    "fields": {
                                        "TitleEncrypted": {
                                            "value": base64.b64encode(
                                                b"Test Note"
                                            ).decode("utf-8")
                                        },
                                        "SnippetEncrypted": {
                                            "value": base64.b64encode(
                                                b"This is a test note"
                                            ).decode("utf-8")
                                        },
                                        "TextDataEncrypted": {
                                            "value": encoded_text_data
                                        },
                                    },
                                },
                            ]
                        }
                    )
                )
            return Mock()

        mock_session.post.side_effect = mock_post

        # Initialize NotesService
        service_root = "mock_service_root"
        self.service = NotesService(service_root, mock_session, mock_params)

    def test_notes(self):
        """Test fetching notes."""
        notes = self.service.notes
        assert notes
        assert len(notes) == 1
        note = notes[0]

        assert note["fields"]["title"] == "Test Note"
        assert note["fields"]["snippet"] == "This is a test note"
        assert note["fields"]["Text"]["string"] == "Test Note Content"
        # fmt: off
        expected_note_repr = {
            'recordName': 'note1',
            'recordType': 'Note',
            'fields': {
                'TitleEncrypted': {'value': 'VGVzdCBOb3Rl'},
                'SnippetEncrypted': {'value': 'VGhpcyBpcyBhIHRlc3Qgbm90ZQ=='},
                'TextDataEncrypted': {'value': 'eJwTEpUSFhIMSS0uUfDLL0lVcM7PK0nNKwEAQKgGyQ=='},
                'title': 'Test Note',
                'snippet': 'This is a test note',
                'TextData': {'version': [{'data': 'EhFUZXN0IE5vdGUgQ29udGVudA=='}]},
                'Text': {'string': 'Test Note Content'}
            }
        }
        assert note == expected_note_repr
        # fmt: on

    def test_folders(self):
        """Test fetching folders."""
        # As no folders are defined in the mock data, we should get an empty list
        folders = self.service.folders
        assert folders == []


# Run the tests
if __name__ == "__main__":
    import unittest

    unittest.main()
