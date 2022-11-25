import re

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
    ["userdef1", "User-defined 1"],  # from dclab
])
def test_get_feature_label(feat, label):
    assert scores.get_feature_label(feat) == label


@pytest.mark.parametrize("label,feat,shortcut", [
    ["ml_scores_blood", "ml_score_r1f", "R"],
    ["ml_scores_blood", "ml_score_r1u", "Ctrl+R"],
    ["ml_scores_blood", "ml_score_66a", "A"],  # default
    ["userdef", "userdef1", "1"],  # default
])
def test_get_feature_shortcut(label, feat, shortcut):
    assert scores.get_feature_shortcut(feat, label) == shortcut


def test_correct_ml_score_feat():
    blood = scores.get_dctag_label_dict(name="ml_scores_blood")
    pattern = re.compile("^ml_score_[a-z0-9]{3}$")
    for feat in blood.keys():
        assert pattern.match(feat), (f"Feature name '{feat}' does not match "
                                     "'ml_score_???'-pattern. Only lower case "
                                     "alphanumeric values allowed!")


def test_correct_ml_scores_format():
    blood = scores.get_dctag_label_dict(name="ml_scores_blood")
    for feat, feat_dict in blood.items():
        assert "label" in feat_dict, (f"Label entry missing for feature "
                                      f"'{feat}'!")
        assert "shortcut" in feat_dict, (f"Shortcut entry missing for feature "
                                         f"'{feat}'!")


def test_unique_score_labels():
    groups = scores.get_available_label_groups()
    for group in groups:
        blood = scores.get_dctag_label_dict(name=group)
        labels = [blood[ft]["label"] for ft in blood]
        assert len(labels) == len(set(labels))


def test_unique_score_shortcuts():
    blood = scores.get_dctag_label_dict(name="ml_scores_blood")
    shortcuts = [blood[ft]["shortcut"] for ft in blood]
    assert len(shortcuts) == len(set(shortcuts))
