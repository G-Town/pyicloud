import os
from dotenv import load_dotenv
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException
import logging

import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)


class ICloudSyncService:
    def __init__(self, apple_id, password):
        try:
            self.api = PyiCloudService(apple_id, password)
            if self.api.requires_2fa:
                print("Two-factor authentication required.")
                code = input("Enter the code you received on your devices: ")
                result = self.api.validate_2fa_code(code)
                if not result:
                    print("Failed to verify security code")
                    return
                if not self.api.is_trusted_session:
                    print("Session is not trusted. Requesting trust...")
                    self.api.trust_session()
                    print("Session trusted")
        except PyiCloudFailedLoginException as e:
            print(f"Failed to log in to iCloud: {str(e)}")

    def fetch_notes(self):
        try:
            notes = self.api.notes.notes
            return notes
        except Exception as e:
            print(f"Error fetching notes: {str(e)}")
            return []

    def fetch_folders(self):
        try:
            folders = self.api.notes.folders
            return folders
        except Exception as e:
            print(f"Error fetching folders: {str(e)}")
            return []


# Load environment variables
load_dotenv()


def test_icloud_sync():
    apple_id = os.getenv("IC_APPLEID")
    password = os.getenv("IC_PWD")
    icloud_service = ICloudSyncService(apple_id, password)

    # Test fetching folders
    # print("fetching folders")
    folders = icloud_service.fetch_folders()
    assert folders is not None, "Failed to fetch folders"
    assert isinstance(folders, list), "Folders should be a list"
    if folders:
        print("\nfetched folders:\n")
        for folder in folders:
            print(folder["fields"].keys())
            print(folder["fields"]["title"]+" -- record name: "+folder["recordName"])
            # if "parent" in folder:
            #     print("parent folder: "+folder["parent"]["recordName"])
            if "notes" not in folder:
                continue
            for note in folder["notes"]:
                assert "fields" in note, "Each note should have fields"
                assert (
                    "title" in note["fields"]
                ), "Each note should have a title field"
            #     print(" - " + note["fields"]["title"])
                print(note["fields"].keys())
                # print(note["fields"]["Text"].keys())
                # print(note["fields"].get("snippet"))
                # timestamp = note["fields"]["ModificationDate"]["value"]
                # timestamp_to_unix = round(timestamp / 1000)
                # date_time = datetime.datetime.fromtimestamp(timestamp_to_unix)
                # print(date_time)
            print()

    # Test fetching notes
    # notes = icloud_service.fetch_notes()
    # assert notes is not None, "Failed to fetch notes"
    # assert isinstance(notes, list), "Notes should be a list"
    # if notes:
    #     assert "fields" in notes[0], "Each note should have fields"
    #     assert "title" in notes[0]["fields"], "Each note should have a title field"
    #     print("\nfetched notes:")
    #     for note in notes:
    #         items = []
    #         for item in note:
    #             items.append(item)
    #         # print(items)
    #         fields = list(note["fields"].keys())
    #         if "Deleted" in note["fields"]:
    #             deleted = note["fields"]["Deleted"]["value"]
    #             # print("deleted: ", deleted)
    #             if deleted:
    #                 continue
    #         # print(fields)
    #         print("title: " + note["fields"]["title"])
    #         # print("Folders:")
    #         # print(note["fields"]["Folders"])
    #         # print(note["fields"]["Folder"])
    #         # print("snippet: " + note["fields"]["snippet"])
    #         # print("Text:")
    #         # for item in note["fields"]["Text"]:
    #         #     print(item)
    #         print(note["fields"]["Text"].keys())
    #         # timestamp = note["fields"]["ModificationDate"]["value"]
    #         # timestamp_to_unix = round(timestamp / 1000)
    #         # print(timestamp)
    #         # date_time = datetime.datetime.fromtimestamp(timestamp_to_unix)
    #         # print(date_time)
    #         # print(note["fields"]["LastViewedModificationDate"])
    #         print()

    # TODO: test fetching search indexes


if __name__ == "__main__":
    test_icloud_sync()
