import unittest
from unittest.mock import MagicMock, patch
from pyicloud.services.notes import NotesService

class NotesServiceTest(unittest.TestCase):
    """Notes service tests."""

    def setUp(self):
        """Set up tests."""
        self.mock_session = MagicMock()
        self.mock_params = {
            "dsid": "mock_dsid",
            "clientBuildNumber": "mock_build_number",
            "clientId": "mock_client_id",
        }
        self.notes_service = NotesService("mock_service_root", self.mock_session, self.mock_params)

    @patch("pyicloud.services.notes.get_localzone")
    def test_refresh(self, mock_get_localzone):
        """Test the refresh method."""
        mock_get_localzone.return_value.key = "mock_timezone"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "notes": [
                {
                    "folderName": "Test Folder",
                    "noteId": "note1",
                    "dateModified": "2024-06-17T12:00:00Z",
                    "subject": "Test Note",
                    "size": 123,
                    "detail": {
                        "content": "This is a <b>test</b> note with <br>HTML<br> content."
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        self.mock_session.get.return_value = mock_response

        self.notes_service.refresh()

        self.assertIn("Test Folder", self.notes_service.collections)
        self.assertIn("note1", self.notes_service.collections["Test Folder"])
        note = self.notes_service.collections["Test Folder"]["note1"]
        self.assertEqual(note["dateModified"], "2024-06-17T12:00:00Z")
        self.assertEqual(note["subject"], "Test Note")
        self.assertEqual(note["size"], 123)
        self.assertEqual(note["content"], "This is a test note with \nHTML\n content.")

    def test_parseHTML(self):
        """Test the parseHTML method."""
        html_content = "This is a <b>test</b> note with <br>HTML<br> content."
        expected_content = "This is a test note with \nHTML\n content."
        parsed_content = self.notes_service.parseHTML(html_content)
        self.assertEqual(parsed_content, expected_content)

if __name__ == "__main__":
    unittest.main()
