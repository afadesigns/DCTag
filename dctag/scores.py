from collections import OrderedDict
import functools
import json
import pathlib
import pkg_resources

import dclab


@functools.lru_cache(maxsize=100)
def get_dctag_score_dict(name="blood"):
    path = pkg_resources.resource_filename("dctag.resources",
                                           f"ml_scores_{name}.json")
    score_dict = json.loads(pathlib.Path(path).read_text(),
                            # load as ordered dictionary
                            object_pairs_hook=OrderedDict)
    return score_dict


def get_feature_label(feature):
    score_dict = get_dctag_score_dict(name="blood")
    if feature in score_dict:
        return score_dict[feature]["label"]
    else:
        return dclab.dfn.get_feature_label(feature)


def get_feature_shortcut(feature):
    score_dict = get_dctag_score_dict(name="blood")
    if feature in score_dict:
        return score_dict[feature]["shortcut"]
    else:
        return "A"
