import string

STR_CHARS = "!@#$%^&*" + string.ascii_lowercase + string.digits + string.ascii_uppercase
STR_CHARS_NO_SPECIAL = string.ascii_lowercase + string.digits + string.ascii_uppercase
STR_CHARS_NO_UPPER = string.ascii_lowercase + string.digits + "!@#$%^&*"
STR_CHARS_NO_LOWER = string.ascii_uppercase + string.digits + "!@#$%^&*"
STR_CHARS_NO_DIGITS = string.ascii_lowercase + string.ascii_uppercase + "!@#$%^&*"
STR_CHARS_NO_SPECIAL_NO_UPPER = string.ascii_lowercase + string.digits
STR_CHARS_NO_SPECIAL_NO_LOWER = string.ascii_uppercase + string.digits
STR_CHARS_NO_SPECIAL_NO_DIGITS = string.ascii_lowercase + string.ascii_uppercase
INT_CHARS = string.digits
BOOL_CHARS = ["true", "false"]