import requests
from shared.request_classes import VerseRequest
from shared.response_classes import VerseResponse

def get_verse(verse_request: VerseRequest) -> VerseResponse:
    volume: str = verse_request.volume
    book: str = verse_request.book
    chapter_number: int = verse_request.chapter
    verse_number: int = verse_request.verse
    
    api_url: str = f'https://openscriptureapi.org/api/scriptures/v1/lds/en/volume/{volume}/{book}/{chapter_number}'
    response = requests.get(api_url)

    if (response.status_code == 200):
        chapter = [verse_info["text"] for verse_info in response.json()['chapter']["verses"]]
        verse = chapter[verse_number-1]
        return VerseResponse(chapter, verse)
    else:
        raise ConnectionRefusedError