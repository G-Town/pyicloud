"""Notes service."""
import base64
import gzip
import json
import zlib
from urllib.parse import urlencode
from functools import reduce

from google.protobuf.json_format import MessageToDict

from pyicloud.protobuf.versioned_document_pb2 import Document
from pyicloud.protobuf.topotext_pb2 import String


class NotesService(object):
    """The 'Notes' iCloud service."""

    def __init__(self, service_root, session, params):
        self.session = session
        self._params = params
        self._service_root = service_root
        self.service_endpoint = (
                "%s/database/1/com.apple.notes/production/private"
                % self._service_root
        )

        self.records = []

        self.refresh()

    def refresh(self):
        def fetch_zone_data(sync_token=None):
            params = {
                "dsid": self.session.service.data["dsInfo"]["dsid"],
            }
            url = "%s/changes/zone?%s" % (self.service_endpoint, urlencode(params))
            body = json.dumps({
                "zones": [
                    {
                        "zoneID": {
                            "zoneName": "Notes",
                            "zoneType": "REGULAR_CUSTOM_ZONE",
                        },
                        "desiredKeys": [
                            "TitleEncrypted",
                            "SnippetEncrypted",
                            "FirstAttachmentUTIEncrypted",
                            "FirstAttachmentThumbnail",
                            "FirstAttachmentThumbnailOrientation",
                            "ModificationDate",
                            "Deleted",
                            "Folders",
                            "Folder",
                            "Attachments",
                            "ParentFolder",
                            "Folder",
                            "Note",
                            "LastViewedModificationDate",
                            "MinimumSupportedNotesVersion",
                        ],
                        "desiredRecordTypes": [
                            "Note",
                            "SearchIndexes",
                            "Folder",
                            "PasswordProtectedNote",
                            "User",
                            "Users",
                            "Note_UserSpecific",
                            "cloudkit.share",
                        ],
                        "syncToken": sync_token,
                        "reverse": True,
                    },
                ]
            })

            request = self.session.post(
                url, data=body, headers={"Content-type": "text/plain"}
            )

            # print(request.json())
            zone = request.json()["zones"][0]

            records = []

            if len(zone["records"]) > 0:
                records = [*records, *zone["records"]]

            if zone["moreComing"]:
                records = [*records, *fetch_zone_data(zone.syncToken)]

            return records

        records = fetch_zone_data()

        params = {
            "remapEnums": True,
            "dsid": self.session.service.data["dsInfo"]["dsid"],
        }
        url = "%s/records/lookup?%s" % (self.service_endpoint, urlencode(params))

        resolved_records = []

        for i in range(0, len(records), 50):
            '''Get Notes' Detail.'''

            body = json.dumps({
                "records": list(
                    map(
                        lambda record: {"recordName": record["recordName"] if type(record) is dict else record},
                        records[i:i + 50]
                    )
                ),
                "zoneID": {
                    "zoneName": "Notes",
                }
            })

            request = self.session.post(
                url, data=body, headers={"Content-type": "text/plain"}
            )

            '''Resolve Notes' Detail.'''

            def resolver(last, current):
                print("resolver...")
                if current["recordType"] == "Note" or current["recordType"] == "Note_UserSpecific":
                    print("record type:")
                    print(current["recordType"])
                    current["fields"]["title"] = base64.b64decode(current["fields"]["TitleEncrypted"]["value"]).decode(
                        'utf-8')
                    current["fields"]["snippet"] = base64.b64decode(current["fields"]["SnippetEncrypted"]["value"]).decode(
                        'utf-8')

                    text_data = base64.b64decode(current["fields"]["TextDataEncrypted"]["value"])
                    text_data = gzip.decompress(text_data) if text_data[0] == 0x1f and text_data[
                        1] == 0x8b else zlib.decompress(text_data)

                    proto_document = Document()
                    proto_document.ParseFromString(text_data)
                    current["fields"]["TextData"] = MessageToDict(proto_document)

                    version = proto_document.version

                    proto_string = String()
                    proto_string.ParseFromString(version[len(version) - 1].data)
                    current["fields"]["Text"] = MessageToDict(proto_string)

                    last = [*last, current]

                return last

            resolved_records = [*resolved_records, *reduce(resolver, request.json()["records"], [])]

        self.records = resolved_records
