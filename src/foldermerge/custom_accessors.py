import pandas as pd


@pd.api.extensions.register_dataframe_accessor("cmp")
class ComparatorAccessor:

    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        pass
