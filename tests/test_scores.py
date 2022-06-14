from dctag import scores

import pytest


def test_get_dctag_label_dict():
    blood = scores.get_dctag_label_dict(name="ml_scores_blood")
    assert blood["ml_score_r1f"]["label"] == "RBC singlet focused"


def test_get_dctag_label_dict_error_wrong_name():
    with pytest.raises(FileNotFoundError):
        scores.get_dctag_label_dict(name="peter")


@pytest.mark.parametrize("feat,label", [
    ["ml_score_r1f", "RBC singlet focused"],
    ["ml_score_66a", "ML score 66A"],  # from dclab
])
def test_get_feature_label(feat, label):
    assert scores.get_feature_label(feat) == label


@pytest.mark.parametrize("feat,shortcut", [
    ["ml_score_r1f", "R"],
    ["ml_score_r1u", "Ctrl+R"],
    ["ml_score_66a", "A"],  # default
])
def test_get_feature_shortcut(feat, shortcut):
    assert scores.get_feature_shortcut(feat) == shortcut


def test_unique_score_labels():
    blood = scores.get_dctag_label_dict(name="ml_scores_blood")
    labels = [blood[ft]["label"] for ft in blood]
    assert len(labels) == len(set(labels))


def test_unique_score_shortcuts():
    blood = scores.get_dctag_label_dict(name="ml_scores_blood")
    shortcuts = [blood[ft]["shortcut"] for ft in blood]
    assert len(shortcuts) == len(set(shortcuts))
