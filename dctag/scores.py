from collections import OrderedDict
import functools
import json
import pathlib
import pkg_resources

import dclab


def get_available_label_groups():
    path = pkg_resources.resource_filename("dctag", "resources")
    files = list(pathlib.Path(path).glob("tag_*.json"))
    names = [pp.stem[4:] for pp in files]
    return sorted(names)


@functools.lru_cache(maxsize=100)
def get_dctag_label_dict(name="ml_scores_blood"):
    fname = f"tag_{name}.json"
    path = pkg_resources.resource_filename("dctag.resources", fname)
    score_dict = json.loads(pathlib.Path(path).read_text(),
                            # load as ordered dictionary
                            object_pairs_hook=OrderedDict)
    return score_dict


def get_feature_label(feature):
    score_dict = get_dctag_label_dict(name="ml_scores_blood")
    if feature in score_dict:
        return score_dict[feature]["label"]
    else:
        return dclab.dfn.get_feature_label(feature)


def get_feature_shortcut(feature):
    score_dict = get_dctag_label_dict(name="ml_scores_blood")
    if feature in score_dict:
        return score_dict[feature]["shortcut"]
    else:
        return "A"
