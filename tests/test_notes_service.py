import base64
import json
import zlib
import logging
from unittest.mock import Mock
from pyicloud.services.notes import NotesService
from pyicloud.protobuf.versioned_document_pb2 import Document
from pyicloud.protobuf.topotext_pb2 import String
from google.protobuf.json_format import MessageToDict

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
encoded_text_data = base64.b64encode(compressed_text_data).decode('utf-8')


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
                                    "value": base64.b64encode(b"Test Note").decode(
                                        "utf-8"
                                    )
                                },
                                "SnippetEncrypted": {
                                    "value": base64.b64encode(
                                        b"This is a test note"
                                    ).decode("utf-8")
                                },
                                "TextDataEncrypted": {"value": encoded_text_data},
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
notes_service = NotesService(service_root, mock_session, mock_params)

# Print the fetched notes
print(json.dumps(notes_service.records, indent=2))
