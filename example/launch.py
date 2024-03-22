import sys
import os

sys.path.insert(0, os.path.abspath("../"))

from akabat.controller import Controller

if __name__ == "__main__":
    force_build_files = False
    controller = Controller("preferences.json")
    removed_papers = controller.import_all_csvs("SLR")
    print("duplicated papers removed: ", removed_papers)
    print("number of papers imported: ", len(controller._raw_papers))

    if force_build_files or not controller.load_unique_keywords():
        controller.generate_unique_keywords()
        controller.save_unique_keywords()
    print("number of unique keywords: ", len(controller._data.unique_keywords))

    if force_build_files or not controller.load_keywords_by_semantic_similarity():
        controller.group_keywords_by_semantic_similarity()
        controller.save_keywords_by_semantic_similarity()
    print("number of semantic groups: ", len(controller._data.unique_keywords_groups))

    if force_build_files or not controller.is_database_created():
        controller.create_and_populate_database()
        print("created database")
    print("database loaded")

    controller.generate_plots()
