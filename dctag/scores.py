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


def get_feature_label(feature, label_group=None):
    default_label = dclab.dfn.get_feature_label(feature)
    if label_group is None:
        # go through all label groups
        for group in get_available_label_groups():
            label = get_feature_label(feature, group)
            if label != default_label:
                break
        else:
            label = default_label
    else:
        # use this specific label group
        score_dict = get_dctag_label_dict(name=label_group)
        if feature in score_dict:
            label = score_dict[feature]["label"]
        else:
            label = default_label
    return label


def get_feature_shortcut(feature, label_group="ml_scores_blood"):
    score_dict = get_dctag_label_dict(name=label_group)
    if feature in score_dict:
        return score_dict[feature]["shortcut"]
    else:
        return "A"
