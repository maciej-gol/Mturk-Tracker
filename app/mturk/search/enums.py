from utils.enum import EnumMetaclass


class SearchInEnum:
    """Describes fields that can be search in using the search view."""

    __metaclass__ = EnumMetaclass

    TITLE = "title"
    DESCRIPTION = "description"
    REQUESTER_ID = "requester_id"
    REQUESTER_NAME = "requester_name"
    CONTENT = "content"
    KEYWORDS = "keywords"
    QUALIFICATIONS = "qualifications"
