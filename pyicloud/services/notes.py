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


class NotesService:
    """The 'Notes' iCloud service."""

    def __init__(self, service_root, session, params):
        self.session = session
        self._params = params
        self._service_root = service_root
        self.service_endpoint = (
            f"{self._service_root}/database/1/com.apple.notes/production/private"
        )

        self.records = []

        self.refresh()

    def refresh(self):
        def fetch_zone_data(sync_token=None):
            params = {
                "dsid": self.session.service.data["dsInfo"]["dsid"],
            }
            url = f"{self.service_endpoint}/changes/zone?{urlencode(params)}"
            body = json.dumps(
                {
                    "zones": [
                        {
                            "zoneID": {
                                "zoneName": "Notes",
                                "zoneType": "REGULAR_CUSTOM_ZONE",
                            },
                            "desiredKeys": [
                                "TitleEncrypted",
                                "SnippetEncrypted",
                                # "FirstAttachmentUTIEncrypted",
                                # "FirstAttachmentThumbnail",
                                # "FirstAttachmentThumbnailOrientation",
                                "ModificationDate",
                                "Deleted",
                                "Folders",
                                "Folder",
                                # "Attachments",
                                "ParentFolder",
                                "Note",
                                "LastViewedModificationDate",
                                # "MinimumSupportedNotesVersion",
                            ],
                            "desiredRecordTypes": [
                                "Note",
                                "SearchIndexes",
                                "Folder",
                                # "PasswordProtectedNote",
                                "User",
                                "Users",
                                # "Note_UserSpecific",
                                # "cloudkit.share",
                            ],
                            "syncToken": sync_token,
                            "reverse": True,
                        },
                    ]
                }
            )

            request = self.session.post(
                url, data=body, headers={"Content-type": "text/plain"}
            )

            zone = request.json()["zones"][0]

            records = zone.get("records", [])

            if zone.get("moreComing"):
                records += fetch_zone_data(zone.get("syncToken"))

            return records

        records = fetch_zone_data()

        params = {
            "remapEnums": True,
            "dsid": self.session.service.data["dsInfo"]["dsid"],
        }
        url = f"{self.service_endpoint}/records/lookup?{urlencode(params)}"

        resolved_records = []

        for i in range(0, len(records), 50):
            body = json.dumps(
                {
                    "records": [
                        {"recordName": record["recordName"]}
                        for record in records[i : i + 50]
                    ],
                    "zoneID": {
                        "zoneName": "Notes",
                    },
                }
            )

            request = self.session.post(
                url, data=body, headers={"Content-type": "text/plain"}
            )

            def resolver(last, current):

                # TODO: resolve folders
                # if current["recordType"] in ["Folder"]:
                #     print("resolve folder")

                # moved handling of user specific notes, only resolve "Notes" here
                if current["recordType"] in ["Note"]:
                    # print("resolve note")
                    current["fields"]["title"] = base64.b64decode(
                        current["fields"]["TitleEncrypted"]["value"]
                    ).decode("utf-8")
                    current["fields"]["snippet"] = base64.b64decode(
                        current["fields"]["SnippetEncrypted"]["value"]
                    ).decode("utf-8")

                    text_data = base64.b64decode(
                        current["fields"]["TextDataEncrypted"]["value"]
                    )
                    text_data = (
                        gzip.decompress(text_data)
                        if text_data[0] == 0x1F and text_data[1] == 0x8B
                        else zlib.decompress(text_data)
                    )

                    proto_document = Document()
                    proto_document.ParseFromString(text_data)
                    current["fields"]["TextData"] = MessageToDict(proto_document)

                    version = proto_document.version

                    proto_string = String()
                    proto_string.ParseFromString(version[-1].data)
                    current["fields"]["Text"] = MessageToDict(proto_string)

                    last.append(current)

                # TODO: resolve search indexes

                # TODO: handle records of recordType Note_UserSpecific
                # if current["recordType"] in ["Note_UserSpecific"]:
                    # print("handle user specific note")
                    # userSpecific_fields = current["fields"]
                    # fields_list = []
                    # for field in userSpecific_fields:
                    #     fields_list.append(field)
                    # print(fields_list)
                    # for item in current:
                    #     print(item)
                    # print(current["fields"]["Note"])
                    # print()



                return last

            resolved_records.extend(reduce(resolver, request.json()["records"], []))

        self.records = resolved_records

    @property
    def notes(self):
        return [
            record
            for record in self.records
            if record["recordType"] in ["Note", "Note_UserSpecific"]
        ]

    @property
    def folders(self):
        folder_records = [
            record for record in self.records if record["recordType"] == "Folder"
        ]
        for folder in folder_records:
            folder["notes"] = [
                note for note in self.notes if self._is_note_in_folder(note, folder)
            ]
        return folder_records

    def _is_note_in_folder(self, note, folder):
        note_parent = note.get("parent")
        if note_parent:
            return note_parent["recordName"] == folder["recordName"]
        folder_field = note["fields"].get("Folder")
        if folder_field:
            return folder_field["value"] == folder["recordName"]
        return False
