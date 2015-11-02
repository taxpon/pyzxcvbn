[![Build Status](https://travis-ci.org/taxpon/pyzxcvbn.svg?branch=master)](https://travis-ci.org/taxpon/pyzxcvbn)

# pyzxcvb
Python version [zxcvbn](https://github.com/dropbox/zxcvbn). There are the same test scripts (but written in not coffee script but python) as the original repository in order to ensure this library will move in the same way.

# Install
```
pip install pyzxcvbn
```

# Usage
```
from pyzxcvbn import zxcvbn
result = zxcvbn('foobar')
```

Return value of zxcvbn is a dictionary which has keys and values as follows. For more details, please see [original zxcvbn douments](https://github.com/dropbox/zxcvbn).
  
|Key name| Description|
---------|------------|
|guesses|Estimated guesses needed to crack password|
|guesses_log10|Order of magnitude of result.guesses|
|crack_time_display|Same keys as result.crack_time_seconds, with friendlier display string values: "less than a second", "3 hours", "centuries", etc.|
|score|Integer from 0-4|
|feedback|Verbal feedback to help choose better passwords. set when score <= 2.|
|sequence|The list of patterns that zxcvbn based the guess calculation on.|
|calc_time|How long it took zxcvbn to calculate an answer, in milliseconds.|
