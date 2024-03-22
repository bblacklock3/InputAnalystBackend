def click_match(start, end):
    return {
        "$match": {
            "timestamp": {
                "$gt": start,
                "$lt": end
            },
            "$or": [
                {
                    "left_click": True
                },
                {
                    "right_click": True
                },
                {
                    "middle_click": True
                },
            ]
        }
    }


def click_match_timestamp(start, end):
    return [{
        "$match": {
            "timestamp": {
                "$gt": start,
                "$lt": end
            },
            "$or": [
                {
                    "left_click": True
                },
                {
                    "right_click": True
                },
                {
                    "middle_click": True
                },
            ]
        }
    }, {
        "$project": {
            "_id": 0,
            "timestamp": 1
        }
    }]


total_click_count = {
    "$group": {
        "_id": "null",
        "total": {
            "$sum": {
                "$cond": [{
                    "$or": [{
                        "left_click": True
                    }, {
                        "right_click": True
                    }, {
                        "middle_click": True
                    }]
                }, 1, 0]
            }
        },
    }
}

individual_click_count = {
    "$group": {
        "_id": "null",
        "total": {
            "$sum": {
                "$cond": [{
                    "$or": [{
                        "left_click": True
                    }, {
                        "right_click": True
                    }, {
                        "middle_click": True
                    }]
                }, 1, 0]
            }
        },
        "right": {
            "$sum": {
                "$cond": [{
                    "$eq": ["$right_click", True]
                }, 1, 0]
            }
        },
        "middle": {
            "$sum": {
                "$cond": [{
                    "$eq": ["$middle_click", True]
                }, 1, 0]
            }
        },
        "left": {
            "$sum": {
                "$cond": [{
                    "$eq": ["$left_click", True]
                }, 1, 0]
            }
        }
    }
}
