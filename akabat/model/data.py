import pandas as pd


class Data:

    def __init__(self) -> None:
        self._keywords: pd.Series = None
        self._unique_keywords: list[str] = None
        self._unique_keywords_groups: dict[str, list[str]] = None

    def all_keys_exist(self, keyword_groups_names: list[str]) -> bool:
        for key in keyword_groups_names:
            if key not in self._unique_keywords_groups.keys():
                return False
        return True

    def merge_keyword_groups(
        self, keyword_groups_names: list[str], new_group_name: str
    ) -> None:
        merged_keywords = []
        for key in keyword_groups_names:
            merged_keywords.extend(self._unique_keywords_groups[key])
            del self._unique_keywords_groups[key]
        self._unique_keywords_groups[new_group_name] = list(set(merged_keywords))

    @property
    def keywords(self) -> list[str]:
        return self._keywords

    @keywords.setter
    def keywords(self, keywords: list[str]):
        self._keywords = keywords

    @property
    def unique_keywords(self) -> list[str]:
        return self._unique_keywords

    @unique_keywords.setter
    def unique_keywords(self, unique_keywords: list[str]):
        self._unique_keywords = unique_keywords

    @property
    def unique_keywords_groups(self) -> dict[str, list[str]]:
        return self._unique_keywords_groups

    @unique_keywords_groups.setter
    def unique_keywords_groups(self, unique_keywords_groups: dict[str, list[str]]):
        self._unique_keywords_groups = unique_keywords_groups
