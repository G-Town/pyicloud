import os
from dotenv import load_dotenv
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException
import logging

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

    print("testing notes service")

    # Test fetching folders
    # print("fetching folders")
    # folders = icloud_service.fetch_folders()
    # assert folders is not None, "Failed to fetch folders"
    # assert isinstance(folders, list), "Folders should be a list"
    # if folders:
    #     assert "recordName" in folders[0], "Each folder should have a recordName"
    #     for folder in folders:
    #         # print(folder)
    #         if "notes" in folder:
    #             for note in folder["notes"]:
    #                 # print(note["fields"])
    #                 assert "fields" in note, "Each note should have fields"
    #                 assert (
    #                     "title" in note["fields"]
    #                 ), "Each note should have a title field"

    # Test fetching notes
    print("fetching notes")
    notes = icloud_service.fetch_notes()
    assert notes is not None, "Failed to fetch notes"
    assert isinstance(notes, list), "Notes should be a list"
    if notes:
        assert "fields" in notes[0], "Each note should have fields"
        assert "title" in notes[0]["fields"], "Each note should have a title field"
        print("\nfetched notes:")
        for note in notes:
            # items = []
            # for item in note:
            #     items.append(item)
            # print(items)
            # fields = list(note["fields"].keys())
            # print(fields)
            if "Deleted" in note["fields"]:
                deleted = note["fields"]["Deleted"]["value"]
                # print("deleted: ", deleted)
                if deleted:
                    continue
            print("title: " + note["fields"]["title"])
            print("snippet: " + note["fields"]["snippet"])
            print("Text:")
            for item in note["fields"]["Text"]:
                print(item)
            print(note["fields"]["Text"]["string"])
            print()


if __name__ == "__main__":
    test_icloud_sync()
