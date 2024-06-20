# from __future__ import absolute_import
# from datetime import datetime, timedelta
# import time
# import uuid
# import json
from tzlocal import get_localzone
import re
import logging


class NotesService(object):

    def __init__(self, service_root, session, params):
        self.session = session
        self.params = params
        self._service_root = service_root
        self.collections = {}

        self.refresh()

    def parseHTML(self, s):
        s = s.replace("&lt;", "<")
        s = s.replace("&gt;", ">")
        s = s.replace("&amp;", "&")
        s = re.sub("<br>", "\n", s)
        s = re.sub("<[A-Za-z\/][^>]*>", "", s)

        return s

    def refresh(self):
        params_notes = dict(self.params)
        params_notes.update(
            {
                "clientVersion": "4.0",
                "lang": "en-us",
                "usertz": get_localzone().key
            }
        )

        # Open notes
        #req = self.session.get(self._service_root + "/no/startup", params=params_notes)
        logging.debug(f"Requesting notes with parameters: {params_notes}")
        try:
            # req = self.session.get(self._service_root + "/no/startup", params=params_notes)
            req = self.session.get(self._service_root + "/startup", params=params_notes)
            req.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except Exception as e:
            logging.error(f"Error fetching notes: {e}")
            return

        try:
            startup = req.json()
        except ValueError as e:
            logging.error(f"Error parsing notes response: {e}")
            return

        self.collections = {}

        for note in startup["notes"]:
            if not note["folderName"] in self.collections:
                self.collections[note["folderName"]] = {}
            if "content" in note["detail"]:
                content = self.parseHTML(note["detail"]["content"])
                self.collections[note["folderName"]].update(
                    {
                        note["noteId"]: {
                            "dateModified": note["dateModified"],
                            "subject": note["subject"],
                            "size": note["size"],
                            "content": content,
                        }
                    }
                )
