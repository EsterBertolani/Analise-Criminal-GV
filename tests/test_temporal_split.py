import pandas as pd

from src.config import get_settings
from src.models.regression import temporal_cutoff_months


def test_temporal_cutoff_keeps_future_as_test():
    settings = get_settings()
    data = pd.DataFrame(
        {
            "data_mes": pd.date_range("2021-01-01", periods=36, freq="MS"),
            "ocorrencias": range(36),
        }
    )
    cutoff = temporal_cutoff_months(data, settings)
    train = data[data["data_mes"] < cutoff]
    test = data[data["data_mes"] >= cutoff]
    assert train["data_mes"].max() < test["data_mes"].min()
