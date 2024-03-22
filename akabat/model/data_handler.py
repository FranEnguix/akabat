import json

import pandas as pd
import re
import os
import unicodedata

from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering


class UserPreferences:
    def __init__(self, preferences_file_path: str = "preferences.json"):
        """
        Initialize the UserPreferences.

        Args:
            preferences_file_path (str): Path to the preferences JSON file.
        """
        self.preferences_file_path = preferences_file_path
        self.preferences: dict = None
        self.root_folder: str = None
        self.csv_folder: str = None
        self.output_files_folder: str = None
        self.plot_folder: str = None
        self.excluded_starting_by_keywords_at_csv_import: list[str] = []
        self.excluded_keywords_at_csv_import: list[str] = []
        self.excluded_keywords_in_plot: list[str] = []
        self.csv_import_column_names: dict[str, str] = {}
        self.csv_column_names: dict[str, str] = {}
        self.load_preferences(preferences_file_path)

    def save_preferences(self, alternative_preferences_file_path: str = None) -> None:
        preferences_file_path = self.preferences_file_path
        if alternative_preferences_file_path:
            preferences_file_path = alternative_preferences_file_path
        CheckpointHandler.write_to_json_file(self.preferences, preferences_file_path)

    def load_preferences(self, preferences_file_path: str = "preferences.json"):
        """
        Load preferences from the specified JSON file.

        Args:
            preferences_file_path (str): Path to the preferences JSON file.
        """
        if preferences_file_path:
            self.preferences_file_path = preferences_file_path

        self.preferences = CheckpointHandler.load_from_json_file(
            self.preferences_file_path
        )

        if self.preferences:
            paths: dict = self.preferences.get("paths", None)
            if paths:
                self.root_folder: str = paths.get("root_folder", None)
                self.csv_folder: str = paths.get("csv_folder", None)
                self.output_files_folder: str = paths.get("output_files_folder", None)
                self.plot_folder: str = paths.get("plot_folder", None)

            self.csv_import_column_names: dict[str, str] = self.preferences.get(
                "csv_import_column_names", {}
            )

            excluded_keywords: dict = self.preferences.get("excluded_keywords", None)
            if excluded_keywords:
                self.excluded_starting_by_keywords_at_csv_import: list[str] = (
                    excluded_keywords.get(
                        "excluded_starting_by_keywords_at_csv_import", []
                    )
                )
                self.excluded_keywords_at_csv_import: list[str] = excluded_keywords.get(
                    "excluded_keywords_at_csv_import", []
                )
                self.excluded_keywords_in_plot: list[str] = excluded_keywords.get(
                    "excluded_keywords_in_plot", []
                )


class CheckpointHandler:

    def write_to_json_file(obj, file_path: str, human_readable: bool = True) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            if human_readable:
                json.dump(obj, f, indent=4)
            else:
                json.dump(obj, f)

    def load_from_json_file(file_path: str):
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return False


class PaperLoader:

    def __init__(self) -> None:
        self._transformer_model: SentenceTransformer = None
        self._column_names: dict[str, str] = {
            "title": "title",
            "publication_year": "publication_year",
            "keywords": "keywords",
        }

        self._column_data_types: dict = {
            "title": str,
            "publication_year": int,
            # "keywords": list[str],
        }

    def get_keyword_counts(
        self, df: pd.DataFrame, excluded_keywords: list[str] = []
    ) -> pd.Series:
        all_keywords = [
            keyword
            for keywords in df[self._column_names["keywords"]]
            for keyword in keywords
        ]

        keyword_counts = pd.Series(all_keywords).value_counts()

        keyword_counts_filtered = keyword_counts
        if excluded_keywords:
            keyword_counts_filtered = keyword_counts[
                ~keyword_counts.index.isin(excluded_keywords)
            ]

        return keyword_counts_filtered

    def get_unique_keywords(
        self, df: pd.DataFrame, excluded_keywords: list[str] = []
    ) -> list[str]:
        all_keywords = self.get_keyword_counts(
            df=df, excluded_keywords=excluded_keywords
        )
        return [
            keyword
            for keyword in all_keywords.keys()
            if keyword not in excluded_keywords
        ]

    def group_keywords_by_semantic_similarity(
        self,
        unique_keywords: list[str],
        distance_threshold: float = 1.9,
        n_clusters: int = None,
    ):
        model_name = "all-mpnet-base-v2"
        if not self._transformer_model:
            self._transformer_model = SentenceTransformer(model_name)

        embeddings = self._transformer_model.encode(unique_keywords)
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            distance_threshold=distance_threshold,
            compute_full_tree=True,
            metric="euclidean",
            linkage="ward",
        )
        clustering.fit(embeddings)
        cluster_labels = clustering.labels_

        groups_key_embeddings = {}
        for i, keyword in enumerate(unique_keywords):
            cluster = cluster_labels[i]
            if cluster not in groups_key_embeddings:
                groups_key_embeddings[cluster] = []
            groups_key_embeddings[cluster].append(keyword)

        groups = {}
        for key, value in groups_key_embeddings.items():
            groups[value[0]] = value

        return groups

    def merge_csvs(self, csvs: list[pd.DataFrame]) -> tuple[pd.DataFrame, int]:
        concatenated_df = pd.concat(csvs)
        return self.remove_duplicates(df=concatenated_df)

    def import_csvs(
        self,
        folder_path: str,
        excluded_keywords_at_csv_import: list[str],
        excluded_starting_by_keywords_at_csv_import: list[str],
        import_columns_names: dict[str, str],
        keyword_separator: str = ";",
        separator: str = ",",
        header: int = 0,
    ) -> list[pd.DataFrame]:
        csvs = []
        for file_path in os.listdir(folder_path):
            if file_path.endswith(".csv"):
                csvs.append(
                    self.import_csv(
                        file_path=f"{folder_path}/{file_path}",
                        excluded_keywords_at_csv_import=excluded_keywords_at_csv_import,
                        excluded_starting_by_keywords_at_csv_import=excluded_starting_by_keywords_at_csv_import,
                        import_columns_names=import_columns_names,
                        keyword_separator=keyword_separator,
                        separator=separator,
                        header=header,
                    )
                )
        return csvs

    def import_csv(
        self,
        file_path: str,
        excluded_keywords_at_csv_import: list[str],
        excluded_starting_by_keywords_at_csv_import: list[str],
        import_columns_names: dict[str, str],
        keyword_separator: str = ";",
        separator: str = ",",
        header: int = 0,
    ) -> pd.DataFrame:
        csv: pd.DataFrame = pd.read_csv(
            file_path,
            sep=separator,
            header=header,
            usecols=list(import_columns_names.values()),
        )

        csv[self._column_names["keywords"]] = csv.apply(
            lambda row: self.create_keywords(
                keyword_list=str(row[import_columns_names["keywords"]]),
                keyword_separator=keyword_separator,
                excluded_keywords_at_csv_import=excluded_keywords_at_csv_import,
                excluded_starting_by_keywords_at_csv_import=excluded_starting_by_keywords_at_csv_import,
            ),
            axis=1,
        )
        csv = csv.drop(columns=[import_columns_names["keywords"]])

        inverted_import_columns_names = dict(
            map(reversed, import_columns_names.items())
        )
        csv.rename(columns=inverted_import_columns_names, inplace=True)

        csv = csv.astype(self._column_data_types)
        return csv

    def create_keywords(
        self,
        keyword_list: str,
        keyword_separator: str,
        excluded_keywords_at_csv_import: list[str],
        excluded_starting_by_keywords_at_csv_import: list[str],
    ) -> list[str]:
        """
        Creates a list of unique keywords after normalizing the keywords.

        Args:
            keyword_list (str): List of keywords in a string format with a separator.
            keyword_separator (str): The character that separates keywords.

        Returns:
            list[str]: The list of processed unique keyword.
        """
        keywords = [
            term
            for term in map(self.parse_keyword, keyword_list.split(keyword_separator))
            if term not in excluded_keywords_at_csv_import
            and not any(
                term == "" or term.startswith(excluded_word)
                for excluded_word in excluded_starting_by_keywords_at_csv_import
            )
        ]
        return list(set(keywords))

    def _strip_accents(self, word: str) -> str:
        return "".join(
            c
            for c in unicodedata.normalize("NFD", word)
            if unicodedata.category(c) != "Mn"  # Mn = Nonspacing_Mark
        )

    def parse_keyword(self, keyword: str) -> str:
        """
        Parses the keyword to remove characters such as "-" and "'" and also
        removes extra spaces and spaces to the beggining and end of keywords.

        Args:
            keyword (str): The keyword that will be processed.

        Returns:
            str: The processed keyword.
        """
        parsed_word = keyword.replace("-", " ").replace("&", " and ").replace("[", " ")
        parsed_word = parsed_word.replace("]", " ").replace("+", " ").replace("%", " ")
        parsed_word = parsed_word.replace("$", " ").replace(">", " ").replace("<", " ")
        parsed_word = parsed_word.replace("/", " ").replace(".", " ").replace(",", " ")
        parsed_word = parsed_word.replace("–", " ").replace("'", " ").replace("-", " ")
        parsed_word = parsed_word.replace("‐", " ").replace("λ", " ").replace("—", "e")
        parsed_word = parsed_word.replace("—", " ")
        return re.sub(r"\s+", " ", self._strip_accents(parsed_word.lower())).strip()

    def remove_duplicates(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        total_num_records = len(df)
        title_counts = df[self._column_names["title"]].value_counts()
        duplicated_num_records = len(title_counts[title_counts > 1])
        df_unique = df.drop_duplicates(subset=self._column_names["title"])
        total_num_records_after_drop = len(df_unique)
        expected_unique_papers = total_num_records - duplicated_num_records

        # Check if the unique df is consistent
        # if total_num_records_after_drop != expected_unique_papers:
        #     raise ValueError(
        #         f"The number of unique papers ({total_num_records_after_drop}) does not match the expected value ({expected_unique_papers})."
        #     )

        # if debug:
        #     print(f"The initial record count is {total_num_papers}, with {duplicated_num_papers} duplicate entries identified and removed. The new DataFrame record count is {total_num_papers_after_drop}.")

        return df_unique, duplicated_num_records
