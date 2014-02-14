import sys

# Check for Python 2
if sys.version_info[0] < 3:

    # Python 2
    class Object(object):
        """
        A default "base" object simplifying Python 2 and Python 3
        compatibility. Ensures a 'new-style' class on Python 2.
        """
        pass
else:

    # Python 3
    class Object():
        """
        A default "base" object simplifying Python 2 and Python 3
        compatibility. Ensures a 'new-style' class on Python 2.
        """
        pass