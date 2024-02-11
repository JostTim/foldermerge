import pandas as pd
from typing import List


@pd.api.extensions.register_dataframe_accessor("cmp")
class ComparatorDataframeAccessor:

    def __init__(self, pandas_obj):
        self._obj = pandas_obj


@pd.api.extensions.register_series_accessor("cmp")
class ComparatorSeriesAccessor:

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def name_match(self) -> pd.Series:
        if not len(self._obj.name_matches):
            return pd.Series()
        return self._obj.reference.loc[self._obj.name_matches[0]]

    def content_matches(self) -> List[pd.Series]:
        if not len(self._obj.content_matches):
            return []
        return [self._obj.reference.loc[item] for item in self._obj.content_matches]

    def has_name_match(self) -> bool:
        return not self.name_match().empty

    def has_content_match(self) -> bool:
        return bool(len(self.content_matches()))
