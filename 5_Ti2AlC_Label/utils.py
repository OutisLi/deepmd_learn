import os
import math
import csv
import torch
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.ticker as mtick

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from typing import Tuple


class PlotUtils:
    @staticmethod
    def set_ytick(ax: Axes, width, data=None, log=False, sci=False) -> None:
        def custom_formatter(x, pos):
            return f"{x:.{width}f}" if x != 0 else "0"

        if data is not None:
            y_min, y_max = np.percentile(data, [25, 75])  # find the IQR
        else:
            y_min, y_max = ax.get_ylim()
        if log:
            log_y_min = np.floor(np.log10(y_min))
            log_y_max = np.ceil(np.log10(y_max))
            yticks = np.logspace(log_y_min, log_y_max, int(abs(log_y_max - log_y_min)) + 1)
            ax.set_yticks(yticks)
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%g"))
        else:
            default_yticks = ax.get_yticks()
            # 判断是否应该使用科学计数法
            use_sci = any([abs(ytick) < 10**-(width) for ytick in default_yticks if abs(ytick) > 0])
            use_sci = use_sci or sci
            if use_sci:
                fmt = mtick.ScalarFormatter(useMathText=True)
                fmt.set_powerlimits((-1, 1))
                ax.yaxis.set_major_formatter(fmt)
                ax.yaxis.get_offset_text().set_fontsize(12)
            else:
                valid_yticks = [ytick for ytick in default_yticks if abs(ytick - round(ytick, width)) < 1e-5]
                if valid_yticks:
                    ax.set_yticks(valid_yticks)
                    # ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(f"%.{width}f"))
                    ax.yaxis.set_major_formatter(ticker.FuncFormatter(custom_formatter))
                else:
                    yticks = np.arange(
                        np.floor(y_min * pow(10, width)) / pow(10, width),
                        np.ceil(y_max * pow(10, width)) / pow(10, width) + 1 / float(pow(10, width)),
                        1 / float(pow(10, width)),
                    )
                    ax.set_yticks(yticks)
                    ax.yaxis.set_major_formatter(ticker.FuncFormatter(custom_formatter))

    @staticmethod
    def set_grid(ax: Axes, xnum=10, ynum=10, xlog=False, ylog=False) -> None:
        if ylog:
            major_ticks_base = 10.0
            ax.yaxis.set_major_locator(ticker.LogLocator(base=major_ticks_base))
            ax.yaxis.set_minor_locator(ticker.LogLocator(base=major_ticks_base, subs=np.arange(2, 10)))
        else:
            yticks = ax.get_yticks()
            # 计算主刻度间隔
            if len(yticks) > 1:
                y_main_interval = yticks[1] - yticks[0]
            else:
                y_main_interval = 1  # fallback value
            # 设置次刻度间隔
            ax.yaxis.set_minor_locator(ticker.MultipleLocator(y_main_interval / ynum))

        if xlog:
            major_ticks_base = 10.0
            ax.xaxis.set_major_locator(ticker.LogLocator(base=major_ticks_base))
            ax.xaxis.set_minor_locator(ticker.LogLocator(base=major_ticks_base, subs=np.arange(2, 10)))
        else:
            xticks = ax.get_xticks()
            # 计算主刻度间隔
            if len(xticks) > 1:
                x_main_interval = xticks[1] - xticks[0]
            else:
                x_main_interval = 1  # fallback value
            # 设置次刻度间隔
            ax.xaxis.set_minor_locator(ticker.MultipleLocator(x_main_interval / xnum))

        # 画主刻度网格线
        yticks = ax.get_yticks()
        xticks = ax.get_xticks()
        for y in yticks:
            ax.axhline(y, color="darkgray", linewidth=1)
        for x in xticks:
            ax.axvline(x, color="darkgray", linewidth=1)

        # 显示网格
        ax.grid(color="lightgray", linestyle="-", linewidth=0.5, which="both")

    @staticmethod
    def graph_standard(xlabel=None, ylabel=None, label=None, title=None, w=10, h=6, fnt_size=18) -> Tuple[plt.Figure | plt.Axes]:
        fig, ax = plt.subplots(figsize=(w, h))
        fnt_family = "Times New Roman"

        if title:
            ax.set_title(title, fontsize=fnt_size, y=1.016, fontfamily=fnt_family)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=fnt_size - 1, y=1.02, fontfamily=fnt_family)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=fnt_size - 1, x=1.2, fontfamily=fnt_family)

        ax.tick_params(axis="both", which="major", labelsize=fnt_size, fontfamily=fnt_family)

        ax.locator_params(axis="x", nbins=6)
        ax.locator_params(axis="y", nbins=6)

        # ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

        for axis in ["top", "bottom", "left", "right"]:
            ax.spines[axis].set_linewidth(1)

        if label:
            ax.legend(prop={"family": fnt_family}, fontsize=fnt_size - 3, frameon=False)

        plt.tight_layout()

        return fig, ax
