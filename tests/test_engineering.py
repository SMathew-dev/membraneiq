import pandas as pd

from membraneiq.engineering import calculate_flux, calculate_pressure_drop, calculate_rejection, calculate_tmp


def test_tmp():
    feed = pd.Series([4.0])
    ret = pd.Series([3.0])
    perm = pd.Series([0.5])
    assert calculate_tmp(feed, ret, perm).iloc[0] == 3.0


def test_flux():
    flow = pd.Series([2400.0])
    area = pd.Series([120.0])
    assert calculate_flux(flow, area).iloc[0] == 20.0


def test_pressure_drop():
    feed = pd.Series([4.0])
    ret = pd.Series([3.2])
    assert abs(calculate_pressure_drop(feed, ret).iloc[0] - 0.8) < 1e-12


def test_rejection():
    feed = pd.Series([10.0])
    perm = pd.Series([0.5])
    assert abs(calculate_rejection(feed, perm).iloc[0] - 0.95) < 1e-12
