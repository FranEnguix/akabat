import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from akabat.model import DBHandler


class PlotGenerator:

    def generate_trends_lineplot(
        self,
        df: pd.DataFrame,
        title: str,
        x_label: str,
        y_label: str,
        excluded_keywords: list[str] = [],
        save_file_path: str = None,
        width: int = 12,
        height: int = 8,
    ):
        """
        Given a pandas.DataFrame with "name", "publication_year" and "unique_paper_count"
        this function plots a figure with the trends over all years in "publication_year"
        column per group of keywords in "name" column.

        Args:
            df (pd.DataFrame): The pandas.DataFrame with columns "name",
            "publication_year" and "unique_paper_count"
            title (str): Title of the resulting plot.
            x_label (str): Displayed label of the X axis of the plot.
            y_label (str): Displayed label of the Y axis of the plot.
            excluded_keywords (list[str], optional): List of keyword groups that will not appear in the plot. Defaults to [].
            save_file_path (str, optional): Path of the resulting plot file. Defaults to None.
            width (int, optional): Width size of the resulting figure. Defaults to 12.
            height (int, optional): Height size of the resulting figure. Defaults to 8.
        """
        df_filtered = df[~df["name"].isin(excluded_keywords)]

        fig: Figure = plt.figure(figsize=(width, height))
        ax: Axes = sns.lineplot(
            data=df_filtered, x="publication_year", y="unique_paper_count", hue="name"
        )

        ax.set_title(title)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        plt.xticks(rotation=45)

        # Set x-axis ticks to integers
        ax.set_xticks(df["publication_year"].unique())
        # plt.xticks(df["publication_year"].unique())

        ax.legend(title="Areas of research", bbox_to_anchor=(1.02, 1), loc="upper left")

        plt.tight_layout()  # it is important to run when figure and legend are created

        if save_file_path:
            plt.savefig(save_file_path, bbox_inches="tight")

        plt.show()
