import difflib
import re

def diff(actual,expected,is_text_exp,visible_diff):
    '''Compares actual and expected and returns differences.
        When expected parameter is text (is_text_exp==True) then
        runs two comparisons and returns a pair: 
        In the soft-test, whitespace differences are completely
        ignored (whitespaces are stripped before the comparison is made), while
        in the hard-test whitespace differences are taken into account.
        The 1st component of the returned pair is the outcome of the soft-test,
        while the 2nd component is the outcome of the hard-test.
        When visible_diff==True, whitespaces are replaced by '#'
        when computing the soft-test diff.
        When the expected parameter is binary, byte-by-byte comparison
        is used and the pair (actual,None) is returned if differences
        are detected.        
    '''
    softtest_diffs = None
    hardtest_diffs = None
    if is_text_exp:
        softtest_diffs = get_softtest_diff(expected, actual)
        if not softtest_diffs: # if diff detected
            if visible_diff:  # show a visible diff
                expected = clean_data(expected, r'[\s]', '#')
                actual = clean_data(actual, r'[\s]', '#')
            hardtest_diffs = get_hardtest_diff(expected,actual)
    elif actual!=expected: # binary diff is byte by byte comparison
            softtest_diffs = actual
    return (softtest_diffs,hardtest_diffs)

def clean_data(data, patt, repl):
    '''Replace the given pattern throughout the data
       and returns the result.
       Data is a list of strings.
    '''
    cleaned = []
    for line in data:
        end = '\n'
        stripped_line = re.sub(patt, repl, line) + end
        if len(stripped_line) > 0:
            cleaned.append(stripped_line)
    return cleaned


def get_hardtest_diff(expected, actual, fuzz_level=0):
    '''Line by line comparison of two lists of strings.
    Returns a list of the lines where differences were found.
    Prefix of differences:
    '- ': lines missing from actual
    '+ ': extra lines in actual
    '  ': lines common to both actual and expected
    '''    
    diff_engine = difflib.Differ()
    diff_result = list(diff_engine.compare(expected, actual))

    count = 0
    found_diff = False
    for line in diff_result:
        if line[0] == '+' or line[0] == '-':
            count += 1
            if count >= fuzz_level:
                found_diff = True
                break
    if found_diff:
        return diff_result
    return []



def get_softtest_diff(data_one, data_two, fuzz_level=0):
    '''Same as get_hardtest_diff, but first stripping white space.'''
    stripped_one = clean_data(data_one, r'\s+', '')
    stripped_two = clean_data(data_two, r'\s+', '')
    return get_hardtest_diff(stripped_one, stripped_two, fuzz_level)
#    if df:
#        stripped_one = clean_data(data_one, r'\s+', ' ')
#        stripped_two = clean_data(data_two, r'\s+', ' ')
#        return get_hardtest_diff(stripped_one, stripped_two, fuzz_level)
#    return df
        
