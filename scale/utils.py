from math import isnan, isinf


def isNumber(num):
    """Check if `num` is a number.

    """
    try:
        float(num)
        return True
    except Exception:
        return False


def isNan(num):
    """Check to see if `num` is `nan`.

    """
    return isnan(num)


def isInf(num):
    """Check to see if `num` is infinite

    """
    return isinf(num)