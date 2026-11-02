"""Regenerate hand-specified shared fixtures; no solver is used for expectations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cases = []

def valid(name, numbers, target, selected):
    cases.append({'name': name, 'args': ['--numbers', numbers, '--target', target],
                  'numbers': [str(int(x)) for x in numbers.split(',')], 'target': str(int(target)),
                  'selected': [str(x) for x in selected]})


def invalid(name, args, error, code=2):
    cases.append({'name': name, 'args': args, 'code': code, 'error': error})


valid('original', '3,5,7,9', '18', [3,5,9])
valid('exact', '3,5,7', '10', [3,7])
valid('count_before_sum', '2,3,9', '9', [2,3])
valid('index_tie', '4,1,3,2', '5', [4,1])
valid('single_fits', '42', '42', [42])
valid('single_exceeds', '42', '41', [])
valid('zero_target', '3,5,7', '0', [])
valid('all_exceed', '8,9,10', '7', [])
valid('all_fit', '9,3,5', '99', [9,3,5])
valid('unsorted', '9,7,3,5', '18', [9,3,5])
valid('whitespace', ' \t03 , 5\r\n,7 ', ' 0010\t', [3,7])
valid('uint64', '18446744073709551615', '18446744073709551615', [18446744073709551615])
valid('wide_input_sum', '18446744073709551615,18446744073709551614', '18446744073709551615', [18446744073709551615])
valid('wide_search', '18446744073709551615,1,2', '18446744073709551615', [1,2])
for name, numbers, error in [
 ('negative','-3,5','numbers[0]: expected decimal digits'),
 ('zero','0,3','numbers[0]: must be positive'),
 ('duplicate','3,5,3','numbers[2]: duplicate value'),
 ('numeric_duplicate','3,03','numbers[1]: duplicate value'),
 ('colon','3:5','numbers[0]: expected decimal digits'),
 ('semicolon','3;5','numbers[0]: expected decimal digits'),
 ('mixed','3,5;7','numbers[1]: expected decimal digits'),
 ('fraction','3,5.5','numbers[1]: expected decimal digits'),
 ('empty','','numbers[0]: expected decimal digits'),
 ('consecutive','3,,7','numbers[1]: expected decimal digits'),
 ('trailing','3,5,','numbers[2]: expected decimal digits'),
 ('alpha','abc','numbers[0]: expected decimal digits'),
 ('plus','+3','numbers[0]: expected decimal digits'),
 ('unicode_digit','٣','numbers[0]: expected decimal digits'),
 ('unicode_space','\u00a03','numbers[0]: expected decimal digits'),
 ('internal_space','3 5','numbers[0]: expected decimal digits'),
 ('number_overflow','18446744073709551616','numbers[0]: exceeds uint64 range')]:
    invalid(name, ['--numbers',numbers,'--target','18'], error)
for target in ['-1','1.5','','+1','1e3','abc','١']:
    invalid('target_'+repr(target), ['--numbers','3','--target',target], 'target: expected decimal digits')
invalid('target_overflow',['--numbers','3','--target','18446744073709551616'],'target: exceeds uint64 range')
invalid('missing_both', [], 'missing required argument: --numbers')
invalid('missing_target', ['--numbers','3'], 'missing required argument: --target')
invalid('missing_numbers', ['--target','3'], 'missing required argument: --numbers')
invalid('missing_value', ['--numbers'], 'missing value for --numbers')
invalid('flag_as_value', ['--numbers','--target','3'], 'missing value for --numbers')
invalid('repeated', ['--numbers','3','--numbers','4','--target','5'], 'repeated argument: --numbers')
invalid('equals_form', ['--numbers=3','--target','5'], 'unknown argument: --numbers=3')
invalid('positional', ['3','5'], 'unknown argument: 3')
invalid('help_extra', ['--help','extra'], 'unknown argument: --help')
invalid('search_limit', ['--numbers',','.join(map(str,range(1,38))),'--target','38'], 'exact search requires at most 36 eligible items',3)
cases.append({'name':'help','args':['--help'],'stdout':'Usage: solver --numbers "3,5,7,9" --target 18\n       solver --help\n'})
(ROOT/'testdata/cases.json').write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n')
print(f'Wrote {len(cases)} shared fixtures')
