import requests

class APIHandlers:
    @staticmethod
    def get_chapter(volume: str, book: str, chapter_number: int) -> list[str]:
        api_url: str = f'https://openscriptureapi.org/api/scriptures/v1/lds/en/volume/{volume}/{book}/{chapter_number}'
        response = requests.get(api_url)

        if (response.status_code == 200):
            return [verse_info["text"] for verse_info in response.json()['chapter']["verses"]]
        else:
            raise ConnectionRefusedError