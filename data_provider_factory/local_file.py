# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""

import pandas as pd

from IBridgePy.constants import DataProviderName
from .data_provider_nonRandom import NonRandom


class LocalFile(NonRandom):
    @property
    def name(self):
        return DataProviderName.LOCAL_FILE

    def ingest_hists(self, histIngestionPlan):
        """
        csv file must have 1st column integer as epoch, then open high low close volume
        hist index must be integer representing epoch time in seconds
        because it will be easier to server data when searching a spot time
        :param histIngestionPlan: histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        :return:
        """
        self._ingest_hists(histIngestionPlan, self._get_hist_from_csv)

    @staticmethod
    def _get_hist_from_csv(plan):
        # print(__name__ + '::_get_hist_from_csv: plan=%s' % (plan,))
        return pd.read_csv(plan.fullFileName,
                           index_col=0,  # first column is index column
                           # parse_dates=[0],  # first column should be parse to date
                           # date_parser=utc_in_seconds_to_dt,  # this is the parse function
                           header=0)  # first row is header row
