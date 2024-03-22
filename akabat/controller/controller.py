import pandas as pd

from akabat.view import ConsoleViewer

from akabat.model import (
    Data,
    UserPreferences,
    PaperLoader,
    CheckpointHandler,
    DBHandler,
    PlotGenerator,
)


class Controller:

    def __init__(self, preferences_file_path: str = "preferences.json") -> None:
        # menu keys are the internal IDs, values are the shown names
        self._menu: dict[str, str] = {
            "exit": "Exit menu",
            # IMPORTS
            # "import csv": "Import one CSV",
            "import all csvs": "Import all CSVs",
            "import unique keywords": "Import unique keywords",
            "import keyword group": "Import keywords groups",
            # "import database": "Import database",
            # GENERATORS
            # "generate keywords": "Generate keywords",
            "generate unique keywords": "Generate unique keywords",
            "generate keyword groups": "Generate keywords groups",
            "generate database": "Generate database",
            "generate plots": "Generate plots",
            # MERGERS
            # "merge keyword groups": "Merge keyword groups",
            # EXCLUSION
            "exclude keyword": "Ban keyword",
            # "exclude keywords": "Exclude list of keywords",
            "remove excluded keyword": "Unban keyword",
            # DELETERS
            "delete database": "Delete database",
            # SAVE FILES
            "save preferences": "Save preferences (such as: banned keywords)",
            "save unique keywords": "Save unique keywords",
            "save keyword groups": "Save keywords groups",
        }
        self._raw_papers: pd.DataFrame = None
        self._data: Data = Data()
        if preferences_file_path:
            self._preferences: UserPreferences = UserPreferences(preferences_file_path)
        else:
            self._preferences: UserPreferences = UserPreferences()

        self._viewer: ConsoleViewer = ConsoleViewer()
        self._paper_loader: PaperLoader = PaperLoader()
        self._db_handler: DBHandler = DBHandler()
        self._plot_generator: PlotGenerator = PlotGenerator()
        self._kill_akabat: bool = False

    def start(self) -> None:
        self._kill_akabat = False
        while not self._kill_akabat:
            option_id = self._viewer.ask_menu_option(self._menu)
            self.run_menu_option(option_id)

    def import_all_csvs(self, folder_path: str = None) -> int:
        """
        Imports all CSV files in the folder and stores the result in the
        self._raw_paper variable. If self._raw_paper exists, then merges
        the imported CSVs with the self._raw_paper pandas.DataFrame. The
        result does not contain duplicated papers, because the merging process.

        Args:
            folder_path (str, optional): The relative or absolute path to
            the folder that contains the CSV files to import. Defaults to None.

        Returns:
            int: Number of duplicated papers removed during the merge process.
        """
        if not folder_path:
            folder_path: str = self._viewer.ask_folder_path()
        csvs: list[pd.DataFrame] = self._paper_loader.import_csvs(
            folder_path=folder_path,
            excluded_keywords_at_csv_import=self._preferences.excluded_keywords_at_csv_import,
            excluded_starting_by_keywords_at_csv_import=self._preferences.excluded_starting_by_keywords_at_csv_import,
            import_columns_names=self._preferences.csv_import_column_names,
        )
        if self._raw_papers is not None and not self._raw_papers.empty:
            csvs.append(self._raw_papers)
        self._raw_papers, duplicated_number = self._paper_loader.merge_csvs(csvs)
        return duplicated_number

    def generate_unique_keywords(self) -> None:
        self._data.unique_keywords = self._paper_loader.get_unique_keywords(
            self._raw_papers,
        )

    def save_unique_keywords(self) -> None:
        CheckpointHandler.write_to_json_file(
            self._data.unique_keywords,
            f"{self._preferences.output_files_folder}/unique_keywords.json",
            human_readable=True,
        )

    def load_unique_keywords(self) -> bool:
        loaded_data = CheckpointHandler.load_from_json_file(
            f"{self._preferences.output_files_folder}/unique_keywords.json",
        )
        if loaded_data:
            self._data.unique_keywords = loaded_data
            return True
        return False

    def group_keywords_by_semantic_similarity(self) -> None:
        number_clusters = self._viewer.ask_number_clusters()
        if number_clusters == 0:
            distance_threshold = self._viewer.ask_distance_threshold()
            if distance_threshold:
                self._data.unique_keywords_groups = (
                    self._paper_loader.group_keywords_by_semantic_similarity(
                        self._data.unique_keywords,
                        distance_threshold=distance_threshold,
                    )
                )
        else:
            self._data.unique_keywords_groups = (
                self._paper_loader.group_keywords_by_semantic_similarity(
                    self._data.unique_keywords,
                    distance_threshold=None,
                    n_clusters=number_clusters,
                )
            )

    def save_keywords_by_semantic_similarity(self) -> None:
        CheckpointHandler.write_to_json_file(
            self._data.unique_keywords_groups,
            f"{self._preferences.output_files_folder}/keyword_groups.json",
            human_readable=True,
        )

    def load_keywords_by_semantic_similarity(self) -> bool:
        loaded_data = CheckpointHandler.load_from_json_file(
            f"{self._preferences.output_files_folder}/keyword_groups.json",
        )
        if loaded_data:
            self._data.unique_keywords_groups = loaded_data
            return True
        return False

    def create_and_populate_database(self) -> None:
        self._db_handler.create_database()
        self._db_handler.populate_paper_table(self._raw_papers)
        self._db_handler.populate_keyword_tables(self._data.unique_keywords_groups)
        self._db_handler.populate_paper_keyword_table(self._raw_papers)

    def merge_keyword_groups(self) -> None:
        if not self._data.unique_keywords_groups:
            print("You have to load or generate keywords first")
        else:
            keyword_groups = self._viewer.ask_keyword_groups()
            if keyword_groups:
                new_group_name = self._viewer.ask_keyword(
                    "Enter the new keyword group name: "
                )
                if new_group_name:
                    if self._data.all_keys_exist(keyword_groups):
                        self._data.merge_keyword_groups(keyword_groups, new_group_name)
                    else:
                        print("ERROR: All keys must exist to merge the groups.")

    def exclude_keyword(self) -> None:
        excluded_keyword = self._viewer.ask_keyword()
        if (
            excluded_keyword
            and excluded_keyword not in self._preferences.excluded_keywords_in_plot
        ):
            self._preferences.excluded_keywords_in_plot.append(excluded_keyword)
            self._preferences.excluded_keywords_in_plot.sort()

    def remove_excluded_keyword(self) -> None:
        excluded_keyword = self._viewer.ask_keyword()
        if excluded_keyword in self._preferences.excluded_keywords_in_plot:
            self._preferences.excluded_keywords_in_plot.remove(excluded_keyword)

    def delete_database(self) -> bool:
        return self._db_handler.delete_database()

    def is_database_created(self) -> bool:
        return self._db_handler.is_database_created()

    def save_preferences(self) -> bool:
        self._preferences.save_preferences("test.json")

    def generate_plots(
        self,
        limit: int = 10,
        year_lower_bound: int = 2023,
        year_upper_bound: int = 2024,
        width: int = 12,
        height: int = 8,
    ) -> None:
        if self.is_database_created():
            self._generate_trends_lineplot(
                limit=limit,
                year_lower_bound=year_lower_bound,
                year_upper_bound=year_upper_bound,
                width=width,
                height=height,
            )
        else:
            print("ERROR: Database is not created.")

    def _generate_trends_lineplot(
        self,
        limit: int = 10,
        year_lower_bound: int = 2023,
        year_upper_bound: int = 2024,
        width: int = 12,
        height: int = 8,
    ) -> None:
        filename = f"n{limit}_trends_in_{year_lower_bound}-{year_upper_bound}.png"
        save_path = f"{self._preferences.output_files_folder}/{self._preferences.plot_folder}/{filename}"

        df_top = self._db_handler.query_top_groups(
            limit=limit,
            year_lower_bound=year_lower_bound,
            year_upper_bound=year_upper_bound,
            excluded_keywords=self._preferences.excluded_keywords_in_plot,
        )
        df_trends = self._db_handler.query_trends_of_groups(df_top)
        year_title = self._get_years_title(year_lower_bound, year_upper_bound)
        self._plot_generator.generate_trends_lineplot(
            df=df_trends,
            title=f"Trends of Top {limit} Groups of Keywords {year_title} Over the Years",
            x_label="Publication Year",
            y_label="Number of Papers",
            excluded_keywords=self._preferences.excluded_keywords_in_plot,
            save_file_path=save_path,
            width=width,
            height=height,
        )

    def _get_years_title(
        self, year_lower_bound: int, year_upper_bound: int = None
    ) -> str:
        if not year_upper_bound:
            return f"in {year_lower_bound}"
        elif year_lower_bound == 0:
            return ""
        else:
            return f"from {year_lower_bound} to {year_upper_bound}"

    def run_menu_option(self, option_id: int = -1) -> None:
        if option_id >= 0 and option_id < len(self._menu):
            option_name = list(self._menu.keys())[option_id]
            if option_name == "exit":
                self._kill_akabat = True
            elif option_name == "import all csvs":
                duplicated_papers_removed = self.import_all_csvs()
                print(
                    f"Removed {duplicated_papers_removed} and loaded {len(self._raw_papers)} papers."
                )
            elif option_name == "import unique keywords":
                loaded = self.load_unique_keywords()
                if loaded:
                    print("Loaded.")
                else:
                    print("Error loading.")
            elif option_name == "import keyword group":
                loaded = self.load_keywords_by_semantic_similarity()
                if loaded:
                    print("Loaded.")
                else:
                    print("Error loading.")
            elif option_name == "generate unique keywords":
                self.generate_unique_keywords()
            elif option_name == "generate keyword groups":
                self.group_keywords_by_semantic_similarity()
            elif option_name == "generate database":
                if not self.is_database_created():
                    self.create_and_populate_database()
            elif option_name == "generate plots":
                self.generate_plots()
            elif option_name == "merge keyword groups":
                self.merge_keyword_groups()
            elif option_name == "exclude keyword":
                self.exclude_keyword()
            elif option_name == "remove excluded keyword":
                self.remove_excluded_keyword()
            elif option_name == "delete database":
                self.delete_database()
            elif option_name == "save preferences":
                self.save_preferences()
            elif option_name == "save unique keywords":
                self.save_unique_keywords()
            elif option_name == "save keyword groups":
                self.save_keywords_by_semantic_similarity()
            else:
                self._viewer.display_non_valid_option(self._menu)
