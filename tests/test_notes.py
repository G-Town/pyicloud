import unittest
from unittest.mock import MagicMock, patch, Mock
from pyicloud.services.notes import NotesService

class NotesServiceTest(unittest.TestCase):
    """Notes service tests."""

    def setUp(self):
        """Set up tests."""
        self.mock_session = Mock()
        self.mock_session.service = Mock()
        self.mock_session.service.data = {
            "dsInfo": {
                "dsid": "mock_dsid",
            }
        }
        self.mock_params = {
            "dsid": "mock_dsid",
        }
        self.notes_service = NotesService("mock_service_root", self.mock_session, self.mock_params)

    @patch("pyicloud.services.notes.base64.b64decode")
    @patch("pyicloud.services.notes.gzip.decompress")
    @patch("pyicloud.services.notes.zlib.decompress")
    @patch("pyicloud.services.notes.Document.ParseFromString")
    @patch("pyicloud.services.notes.String.ParseFromString")
    @patch("pyicloud.services.notes.MessageToDict")
    def test_refresh(self, mock_MessageToDict, mock_String_ParseFromString, mock_Document_ParseFromString, mock_zlib_decompress, mock_gzip_decompress, mock_base64_b64decode):
        """Test the refresh method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "zones": [
                {
                    "records": [
                        {
                            "recordType": "Note",
                            "recordName": "note1",
                            "fields": {
                                "TitleEncrypted": {"value": "mock_title_encoded"},
                                "SnippetEncrypted": {"value": "mock_snippet_encoded"},
                                "TextDataEncrypted": {"value": "mock_text_data_encoded"}
                            }
                        }
                    ],
                    "moreComing": False
                }
            ]
        }
        self.mock_session.post.return_value = mock_response

        mock_base64_b64decode.side_effect = lambda x: x.encode()
        mock_zlib_decompress.side_effect = lambda x: x
        mock_gzip_decompress.side_effect = lambda x: x
        mock_Document_ParseFromString.return_value = None
        mock_String_ParseFromString.return_value = None
        mock_MessageToDict.side_effect = [
            {"version": "mock_version"},
            {"data": "mock_data"}
        ]

        # Adding debug print statements
        print("Before refresh")
        self.notes_service.refresh()
        print("After refresh")
        print(self.notes_service.records)

        self.assertEqual(len(self.notes_service.records), 1)
        note = self.notes_service.records[0]
        self.assertEqual(note["recordName"], "note1")
        self.assertEqual(note["fields"]["title"], "mock_title_encoded")
        self.assertEqual(note["fields"]["snippet"], "mock_snippet_encoded")
        self.assertEqual(note["fields"]["TextData"], {"version": "mock_version"})
        self.assertEqual(note["fields"]["Text"], {"data": "mock_data"})

if __name__ == "__main__":
    unittest.main()
